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
from aioquic.h3.events import H3Event, HeadersReceived

from utils.app_logger import logger
from globals import HOST, QUIC_PORT, PACKET_TYPE


@dataclass
class ClientConfig:
    cert_file: str
    key_file: str


class ClientManager:
    def __init__(self):
        self.train_clients: Dict[str, QuicConnectionProtocol] = {}
        self.web_clients: Dict[str, Set[QuicConnectionProtocol]] = defaultdict(set)
        self.lock = asyncio.Lock()

    async def add_train_client(self, train_id: str, protocol: QuicConnectionProtocol):
        async with self.lock:
            self.train_clients[train_id] = protocol
            logger.info(f"Train client connected: {train_id}")

    async def remove_train_client(self, train_id: str):
        async with self.lock:
            if train_id in self.train_clients:
                del self.train_clients[train_id]
                logger.info(f"Train client disconnected: {train_id}")

    async def add_web_client(self, train_id: str, protocol: QuicConnectionProtocol):
        async with self.lock:
            self.web_clients[train_id].add(protocol)
            logger.info(f"Web client connected for train {train_id}")

    async def remove_web_client(self, train_id: str, protocol: QuicConnectionProtocol):
        async with self.lock:
            if train_id in self.web_clients and protocol in self.web_clients[train_id]:
                self.web_clients[train_id].remove(protocol)
                logger.info(f"Web client disconnected for train {train_id}")

    async def get_web_clients(self, train_id: str) -> List[QuicConnectionProtocol]:
        async with self.lock:
            return list(self.web_clients.get(train_id, []))

    async def get_train_client(self, train_id: str) -> Optional[QuicConnectionProtocol]:
        async with self.lock:
            return self.train_clients.get(train_id)


def get_client_config() -> ClientConfig:
    """Get platform-specific client configuration"""
    if sys.platform.startswith("win"):
        return ClientConfig(
            cert_file="C:\\quic_conf\\certificate.pem",
            key_file="C:\\quic_conf\\certificate.key"
        )
    elif sys.platform.startswith("linux"):
        return ClientConfig(
            cert_file="/etc/ssl/quic_conf/certificate.pem",
            key_file="/etc/ssl/quic_conf/certificate.key"
        )
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")


class VideoStreamHandler:
    def __init__(self, train_id: str):
        self.train_id = train_id
        self.current_frame = bytearray()
        self.current_frame_id = -1
        self.expected_packets = 0
        self.received_packets = 0

    def process_packet(self, data: bytes) -> Optional[bytes]:
        """Process a video packet and return complete frame if available"""
        try:
            packet_type = data[0]
            frame_id = int.from_bytes(data[1:5], byteorder='big')
            number_of_packets = int.from_bytes(data[5:7], byteorder='big')
            packet_id = int.from_bytes(data[7:9], byteorder='big')
            train_id = data[9:45].decode('utf-8').strip()
            payload = data[45:]

            if train_id != self.train_id:
                logger.warning(f"Packet train ID mismatch: expected {self.train_id}, got {train_id}")
                return None

            if frame_id != self.current_frame_id:
                # New frame
                self.current_frame = bytearray()
                self.current_frame_id = frame_id
                self.expected_packets = number_of_packets
                self.received_packets = 0

            self.current_frame.extend(payload)
            self.received_packets += 1

            if packet_id == number_of_packets and self.received_packets == self.expected_packets:
                # Complete frame received
                complete_frame = bytes(self.current_frame)
                self.current_frame = bytearray()
                return complete_frame

            return None

        except Exception as e:
            logger.error(f"Error processing video packet: {e}")
            return None


class QUICRelayProtocol(QuicConnectionProtocol):
    def __init__(self, *args, client_manager: ClientManager, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_manager = client_manager
        self.train_id: Optional[str] = None
        self.client_type: Optional[str] = None  # 'train' or 'web'
        self.h3_connection: Optional[H3Connection] = None
        self.video_stream_handler: Optional[VideoStreamHandler] = None
        self._closed = False

    def quic_event_received(self, event: QuicEvent) -> None:
        try:
            if self._closed:
                return

            if isinstance(event, ProtocolNegotiated):
                self._handle_protocol_negotiated(event)
            elif isinstance(event, StreamReset) and self._handler is not None:
                self._handle_stream_reset(event)
            elif isinstance(event, StreamDataReceived):
                self._handle_stream_data(event)
            elif isinstance(event, DatagramFrameReceived):
                logger.debug(f"Datagram frame received: {event.data}")
            elif isinstance(event, ConnectionIdIssued):
                logger.debug(f"New connection ID issued: {event.connection_id}")

            if self.h3_connection is not None:
                for h3_event in self.h3_connection.handle_event(event):
                    self._h3_event_received(h3_event)

        except Exception as e:
            logger.error(f"Error processing QUIC event: {e}", exc_info=True)
            self._close_connection()

    def _handle_protocol_negotiated(self, event: ProtocolNegotiated) -> None:
        logger.debug(f"Protocol negotiated: {event.alpn_protocol}")
        if event.alpn_protocol == 'h3':
            self.h3_connection = H3Connection(self._quic, enable_webtransport=True)
            logger.debug("H3 connection established")

    def _handle_stream_reset(self, event: StreamReset) -> None:
        logger.debug(f"Stream reset: {event.stream_id}")

    def _handle_stream_data(self, event: StreamDataReceived) -> None:
        if not self.client_type:
            self._identify_client(event.data)
            return

        if self.client_type == 'train' and event.data[0] == PACKET_TYPE["video"]:
            self._process_video_data(event)
        else:
            logger.debug(f"Unhandled data received from {self.client_type} client")

    def _identify_client(self, data: bytes) -> None:
        try:
            message = data.decode().strip()
            if message.startswith("TRAIN:"):
                self.client_type = 'train'
                self.train_id = message[6:]
                self.video_stream_handler = VideoStreamHandler(self.train_id)
                asyncio.create_task(self.client_manager.add_train_client(self.train_id, self))
                logger.info(f"Train client identified: {self.train_id}")
            elif message.startswith("CLIENT:"):
                self.client_type = 'web'
                self.train_id = message[7:]
                asyncio.create_task(self.client_manager.add_web_client(self.train_id, self))
                logger.info(f"Web client identified for train: {self.train_id}")
            else:
                logger.warning(f"Unknown client identification message: {message}")
                self._close_connection()
        except UnicodeDecodeError:
            logger.warning("Could not decode client identification message")
            self._close_connection()

    def _process_video_data(self, event: StreamDataReceived) -> None:
        if not self.video_stream_handler:
            logger.error("Video stream handler not initialized")
            return

        complete_frame = self.video_stream_handler.process_packet(event.data)
        if complete_frame:
            asyncio.create_task(self._relay_video_frame(complete_frame, event.stream_id))

    async def _relay_video_frame(self, frame: bytes, stream_id: int) -> None:
        try:
            web_clients = await self.client_manager.get_web_clients(self.train_id)
            if not web_clients:
                logger.debug(f"No web clients connected for train {self.train_id}")
                return

            tasks = []
            for client in web_clients:
                if client != self:  # Don't send back to sender
                    try:
                        client._quic.send_stream_data(stream_id, frame)
                        tasks.append(asyncio.create_task(client.transmit()))
                    except Exception as e:
                        logger.error(f"Error relaying to web client: {e}")
                        await self.client_manager.remove_web_client(self.train_id, client)

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Error relaying video frame: {e}")

    def _h3_event_received(self, event: H3Event) -> None:
        try:
            logger.debug(f"H3 event received: {event}")
            if isinstance(event, HeadersReceived):
                self._handle_headers_received(event)
        except Exception as e:
            logger.error(f"Error processing H3 event: {e}", exc_info=True)
            self._close_connection()

    def _handle_headers_received(self, event: HeadersReceived) -> None:
        headers = {header: value for header, value in event.headers}
        if (headers.get(b":method") == b"CONNECT" and
                headers.get(b":protocol") == b"webtransport"):
            self._handshake_webtransport(event.stream_id, headers)
        else:
            self._send_response(event.stream_id, 400, end_stream=True)

    def _handshake_webtransport(self, stream_id: int, request_headers: Dict[bytes, bytes]) -> None:
        authority = request_headers.get(b":authority")
        path = request_headers.get(b":path")
        logger.info(f"WebTransport handshake: authority={authority}, path={path}")
        self._send_response(stream_id, 200, end_stream=True)

    def _send_response(self, stream_id: int, status_code: int, end_stream=False) -> None:
        headers = [(b":status", str(status_code).encode())]
        if status_code == 200:
            headers.append((b"sec-webtransport-http3-draft", b"draft02"))
        self.h3_connection.send_headers(
            stream_id=stream_id, headers=headers, end_stream=end_stream)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        self._cleanup()
        super().connection_lost(exc)

    def _close_connection(self) -> None:
        if not self._closed:
            self._closed = True
            self._cleanup()
            self._quic.close()

    def _cleanup(self) -> None:
        if self._closed:
            return

        self._closed = True
        if self.train_id and self.client_type:
            asyncio.create_task(self._remove_client_from_manager())

    async def _remove_client_from_manager(self) -> None:
        try:
            if self.client_type == 'train':
                await self.client_manager.remove_train_client(self.train_id)
            elif self.client_type == 'web':
                await self.client_manager.remove_web_client(self.train_id, self)
        except Exception as e:
            logger.error(f"Error cleaning up client: {e}")


async def run_quic_server():
    """Run the QUIC relay server"""
    try:
        config = get_client_config()
        logger.info("Starting QUIC server...")

        quic_config = QuicConfiguration(
            is_client=False,
            alpn_protocols=["h3", "webtransport"],
            max_datagram_frame_size=65536,
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

        logger.info(f"QUIC server running on {HOST}:{QUIC_PORT}")
        await asyncio.Future()  # Run forever

    except Exception as e:
        logger.critical(f"QUIC server failed to start: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(run_quic_server())
    except KeyboardInterrupt:
        logger.info("QUIC server stopped by user")
    except Exception as e:
        logger.critical(f"QUIC server fatal error: {e}", exc_info=True)
        sys.exit(1)