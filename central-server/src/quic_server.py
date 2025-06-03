import asyncio
import ssl
import sys
from dataclasses import dataclass
from typing import Dict, Optional, Set, Tuple, List
from collections import defaultdict
from contextlib import suppress

from aioquic.asyncio import serve
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.quic.events import (
    QuicEvent,
    DatagramFrameReceived,
    StreamDataReceived,
    ConnectionIdIssued,
    ProtocolNegotiated,
    StreamReset,
)
from aioquic.quic.configuration import QuicConfiguration
from aioquic.h3.connection import H3Connection
from aioquic.h3.events import H3Event, HeadersReceived, DataReceived

from src.utils.app_logger import logger
from src.utils.video_datagram_assembler import VideoDatagramAssembler
from src.managers.client_manager import ClientManager
from src.globals import HOST, QUIC_PORT, PACKET_TYPE


@dataclass
class ServerConfig:
    cert_file: str = ""
    key_file: str = ""


def get_client_config() -> ServerConfig:
    """Get platform-specific client configuration"""
    if sys.platform.startswith("win"):
        return ServerConfig(
            cert_file="C:\\quic_conf\\certificate.pem",
            key_file="C:\\quic_conf\\certificate.key"
        )
    elif sys.platform.startswith("linux"):
        return ServerConfig(
            cert_file="/etc/ssl/quic_conf/certificate.pem",
            key_file="/etc/ssl/quic_conf/certificate.key"
        )
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")



class QUICRelayProtocol(QuicConnectionProtocol):
    def __init__(self, *args, client_manager: ClientManager, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_manager = client_manager
        self.client_type: Optional[str] = None
        self.train_id: Optional[str] = None
        self.remote_control_id: Optional[str] = None
        self.h3_connection: Optional[H3Connection] = None
        self.session_id: int = -1  # Default session ID
        self.video_datagram_assembler: Optional[VideoDatagramAssembler] = None
        self.is_closed = False
        self.file = open("video_dump.h264", "wb")

    def quic_event_received(self, event: QuicEvent) -> None:
        try:
            if self.is_closed:
                logger.debug("QUIC: Connection is closed, ignoring event")
                return
            if isinstance(event, ProtocolNegotiated):
                self._handle_protocol_negotiated(event)
            elif isinstance(event, StreamReset) and self._handler is not None:
                self._handle_stream_reset(event)
            elif isinstance(event, StreamDataReceived):
                self._handle_stream_data(event)
            elif isinstance(event, DatagramFrameReceived):
                self._handle_datagram_frame(event)
            elif isinstance(event, ConnectionIdIssued):
                logger.debug(f"QUIC: Received ConnectionIDIssued: {event.connection_id}")
            else:
                pass  # Handle other QUIC events as needed

            if self.h3_connection is not None:
                for h3_event in self.h3_connection.handle_event(event):
                    self._h3_event_received(h3_event)

        except Exception as e:
            logger.error(f"QUIC: Error processing event: {e}", exc_info=True)
            self._close_connection()

    def _handle_protocol_negotiated(self, event: ProtocolNegotiated) -> None:
        logger.debug(f"QUIC: Protocol negotiated: {event.alpn_protocol}")
        if event.alpn_protocol == 'h3':
            self.h3_connection = H3Connection(self._quic, enable_webtransport=True)
            logger.debug("QUIC: H3 connection established")

    def _handle_stream_reset(self, event: StreamReset) -> None:
        logger.debug(f"Stream reset: {event.stream_id}")

    def _handle_datagram_frame(self, event: DatagramFrameReceived) -> None:
        if self.client_type == "TRAIN" and event.data and event.data[0] == PACKET_TYPE["video"]:
            # Relay the video frame to all mapped remote controls
            asyncio.create_task(
                self.client_manager.enqueue_video_packet(self.train_id, event.data)
            )
            self.video_datagram_assembler.calculate_bandwidth(len(event.data))

            # if a complete video frame is received, then write to a file to check
            # frame = self.video_datagram_assembler.process_packet(event.data)
            # if frame:
            #     logger.debug(f"QUIC: Received video frame for train {self.train_id}, size: {len(frame)} bytes")
            #     self.file.write(frame)
            #     self.file.flush()
        else:
            logger.debug(f"QUIC: Received unhandled data : {event.data}")

    def _handle_stream_data(self, event: StreamDataReceived) -> None:
        # Identify client type
        logger.debug(f"QUIC: Received stream data on stream {event.data}")
        if self.client_type is None:
            try:
                message = event.data.decode()
                if message.startswith("TRAIN:"):
                    self.client_type = "TRAIN"
                    self.train_id = message[6:]  # Extract train ID
                    self.video_datagram_assembler = VideoDatagramAssembler(self.train_id)
                    asyncio.create_task(self.client_manager.add_train_client(self.train_id, self))

                    # try send Stream hello world message to the train
                    hello_message = f"HELLO: {self.train_id}".encode()
                    self._quic.send_stream_data(self._quic.get_next_available_stream_id(), hello_message, end_stream=False)
                    transmit_coro = self.transmit()
                    if transmit_coro is not None:
                        asyncio.create_task(transmit_coro)
                    logger.info(f"QUIC: hello_message sent to Train {self.train_id}")
                    return
                elif message.startswith("REMOTE_CONTROL:"):
                    self.client_type = "REMOTE_CONTROL"
                    self.remote_control_id = message[15:]  # Extract train ID
                    asyncio.create_task(self.client_manager.add_remote_control_client(self.remote_control_id, self))

                    # try send Stream hello world message to the remote control
                    logger.info(f"QUIC: Remote control stream received from stream_id: {event.stream_id}, remote_control_id: {self.remote_control_id}")
                    hello_message = f"HELLO: {self.remote_control_id}".encode()
                    self._quic.send_stream_data(event.stream_id, hello_message, end_stream=False)
                    transmit_coro = self.transmit()
                    if transmit_coro is not None:
                        asyncio.create_task(transmit_coro)
                    logger.info(f"QUIC: hello_message sent to Remote control {self.remote_control_id}")
                    return
                else:
                    logger.warning(f"Unknown client identification message: {message}")
                    return
            except UnicodeDecodeError:
                logger.warning("Could not decode client identification message")
                return

        if self.client_type == "REMOTE_CONTROL":
            message = event.data.decode()
            if message.startswith("MAP_CONNECTION:"):
                parts = message[15:].split(":")
                if len(parts) == 2:
                    remote_control_id, train_id = parts
                    asyncio.create_task(
                        self.client_manager.connect_remote_control_to_train(remote_control_id, train_id)
                    )
                else:
                    logger.warning("Invalid MAP_CONNECTION message format")

    def _h3_event_received(self, event: H3Event) -> None:
        if isinstance(event, HeadersReceived):
            headers = {}
            for header, value in event.headers:
                headers[header] = value
            logger.debug(f"QUIC: Received headers on stream {event.stream_id}: {headers}")
            if (headers.get(b":method") == b"CONNECT" and
                    headers.get(b":protocol") == b"webtransport"):
                self._handshake_webtransport(event.stream_id, headers)
            else:
                self._send_response(event.stream_id, 400, end_stream=True)
        elif isinstance(event, DataReceived):
            message = event.data.decode(errors='ignore')
            logger.debug(f"QUIC: Received data on stream {event.stream_id}: {message}")

    def _handshake_webtransport(self, stream_id: int, request_headers: Dict[bytes, bytes]) -> None:
        logger.info(f"QUIC: Handshake webtransport on stream {stream_id}")
        authority = request_headers.get(b":authority")
        path = request_headers.get(b":path")
        logger.debug(f"QUIC: Handshake webtransport: {authority}, {path}")
        self.session_id = stream_id
        self._send_response(stream_id, 200, end_stream=False)

        # TEST: Send a datagram to the browser right after handshake
        # try:
        #     self.h3_connection.send_datagram(stream_id, b"Datagram from server after handshake")
        #     logger.debug("Sent test datagram after handshake")
        # except Exception as e:
        #     logger.error(f"Failed to send test datagram: {e}")

    def _send_response(self, stream_id: int, status_code: int, end_stream=False) -> None:
        headers = [(b":status", str(status_code).encode())]
        if status_code == 200:
            headers.append((b"sec-webtransport-http3-draft", b"02"))
        self.h3_connection.send_headers(stream_id=stream_id, headers=headers, end_stream=end_stream)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        self._cleanup()
        super().connection_lost(exc)

    def _close_connection(self) -> None:
        if not self.is_closed:
            self._cleanup()
            self._quic.close()
            self.is_closed = True

    def _cleanup(self) -> None:
        asyncio.create_task(self._remove_client_from_manager())

    async def _remove_client_from_manager(self) -> None:
        try:
            if self.client_type == 'TRAIN':
                await self.client_manager.remove_train_client(self.train_id)
            elif self.client_type == 'REMOTE_CONTROL':
                await self.client_manager.remove_web_client(self.train_id, self)
        except Exception as e:
            logger.error(f"Error cleaning up client: {e}")

async def run_quic_server():
    try:
        config = get_client_config()

        quic_config = QuicConfiguration(
            is_client=False,
            alpn_protocols=["h3", "webtransport"],
            max_datagram_frame_size=2000,
            idle_timeout=30.0,  # 30 seconds idle timeout
        )
        quic_config.load_cert_chain(certfile=config.cert_file, keyfile=config.key_file)

        # Create a shared client manager
        client_manager = ClientManager()

        server = await serve(
            HOST,
            QUIC_PORT,
            configuration=quic_config,
            create_protocol=lambda *args, **kwargs: QUICRelayProtocol(
                *args, client_manager=client_manager, **kwargs
            )
        )

        logger.info(f"QUIC: server running on {HOST}:{QUIC_PORT}")
        await asyncio.Future()  # Run forever

    except Exception as e:
        logger.critical(f"QUIC: server failed to start: {e}", exc_info=True)
        raise