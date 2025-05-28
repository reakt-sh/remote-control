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

class ClientManager:
    def __init__(self):
        self.train_clients: Dict[str, QuicConnectionProtocol] = {}
        self.remote_control_clients: Dict[str, QuicConnectionProtocol] = {}

        self.train_to_remote_controls_map: Dict[str, Set[str]] = {}
        self.remote_control_to_train_map: Dict[str, str] = {}

        self.lock = asyncio.Lock()

    async def add_train_client(self, train_id: str, protocol: QuicConnectionProtocol):
        async with self.lock:
            self.train_clients[train_id] = protocol
            logger.info(f"QUIC: Train client connected: {train_id}")

    async def remove_train_client(self, train_id: str):
        async with self.lock:
            # first remove mapping from remote controls connected to this train
            if train_id in self.train_to_remote_controls_map:
                remote_control_ids = self.train_to_remote_controls_map[train_id]
                for remote_control_id in remote_control_ids:
                    self.remote_control_to_train_map.pop(remote_control_id, None)
                del self.train_to_remote_controls_map[train_id]

            # then remove the train client
            if train_id in self.train_clients:
                del self.train_clients[train_id]
                logger.info(f"QUIC: Train client disconnected: {train_id}")

    async def add_remote_control_client(self, remote_control_id: str, protocol: QuicConnectionProtocol):
        async with self.lock:
            self.remote_control_clients[remote_control_id] = protocol
            logger.info(f"QUIC: Remote Control client connected {remote_control_id}")

    async def remove_remote_control_client(self, remote_control_id: str, protocol: QuicConnectionProtocol):
        async with self.lock:
            # Remove mapping if it exists
            if remote_control_id in self.remote_control_to_train_map:
                train_id = self.remote_control_to_train_map.pop(remote_control_id)
                if train_id in self.train_to_remote_controls_map:
                    self.train_to_remote_controls_map[train_id].discard(remote_control_id)
                    if not self.train_to_remote_controls_map[train_id]:
                        del self.train_to_remote_controls_map[train_id]
                        logger.debug(f"Removed empty entry for train {train_id} from train_to_remote_controls_map")

            if remote_control_id in self.remote_control_clients:
                del self.remote_control_clients[remote_control_id]
                logger.info(f"QUIC: Remote Control client disconnected: {remote_control_id}")

    async def connect_remote_control_to_train(self, remote_control_id: str, train_id: str):
        async with self.lock:
            # Check if the remote control is already mapped to a train
            if remote_control_id in self.remote_control_to_train_map:
                existing_train_id = self.remote_control_to_train_map[remote_control_id]
                if existing_train_id != train_id:
                    # Unmap from the existing train
                    if existing_train_id in self.train_to_remote_controls_map:
                        self.train_to_remote_controls_map[existing_train_id].discard(remote_control_id)
                        if not self.train_to_remote_controls_map[existing_train_id]:
                            del self.train_to_remote_controls_map[existing_train_id]
                            logger.debug(f"QUIC: Removed empty entry for train {existing_train_id} from train_to_remote_controls_map")
            else:
                logger.debug(f"QUIC: Mapping remote control {remote_control_id} to train {train_id}")

            # Map the remote control to the new train
            self.remote_control_to_train_map[remote_control_id] = train_id
            if train_id not in self.train_to_remote_controls_map:
                self.train_to_remote_controls_map[train_id] = set()
            self.train_to_remote_controls_map[train_id].add(remote_control_id)
            logger.info(f"QUIC: Updated train_to_remote_controls_map: {self.train_to_remote_controls_map}")

    async def relay_video_to_remote_controls(self, train_id: str, data: bytes):
        remote_controls = self.train_to_remote_controls_map.get(train_id, set())
        for remote_control_id in remote_controls:
            protocol = self.remote_control_clients.get(remote_control_id)
            if protocol:
                try:
                    logger.debug(f"Relaying video data to remote_control {remote_control_id} for train {train_id}")
                    protocol._quic.send_datagram_frame(data)
                    transmit_coro = protocol.transmit()
                    if transmit_coro is not None:
                        await transmit_coro
                    logger.debug(f"Video data relayed to remote_control {remote_control_id} for train {train_id}")
                except Exception as e:
                    logger.error(f"Failed to relay video to remote_control {remote_control_id}: {e}")

class VideoStreamHandler:
    def __init__(self, train_id: str):
        self.train_id = train_id
        self.current_frame = bytearray()
        self.current_frame_id = -1
        self.expected_packets = 0
        self.received_packets = 0

    def process_packet(self, data: bytes) -> Optional[bytes]:
        try:
            # Ignoring first byte as packet_type = data[0]
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
        self.client_type: Optional[str] = None
        self.train_id: Optional[str] = None
        self.remote_control_id: Optional[str] = None
        self.h3_connection: Optional[H3Connection] = None
        self.video_stream_handler: Optional[VideoStreamHandler] = None
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
                self.client_manager.relay_video_to_remote_controls(self.train_id, event.data)
            )
            frame = self.video_stream_handler.process_packet(event.data)
            # If a complete frame is received, write it to the file temporarily
            if frame:
                logger.debug(f"QUIC: Received video frame for train {self.train_id}, size: {len(frame)} bytes")
                self.file.write(frame)
                self.file.flush()
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
                    self.video_stream_handler = VideoStreamHandler(self.train_id)
                    asyncio.create_task(self.client_manager.add_train_client(self.train_id, self))
                    return
                elif message.startswith("REMOTE_CONTROL:"):
                    self.client_type = "REMOTE_CONTROL"
                    self.remote_control_id = message[15:]  # Extract train ID
                    asyncio.create_task(self.client_manager.add_remote_control_client(self.remote_control_id, self))

                    # try send Stream hello world message to the remote control
                    hello_message = f"HELLO: {self.remote_control_id}".encode()
                    self._quic.send_stream_data(self._quic.get_next_available_stream_id(), hello_message, end_stream=False)
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
        authority = request_headers.get(b":authority")
        path = request_headers.get(b":path")
        logger.debug(f"QUIC: Handshake webtransport: {authority}, {path}")
        self._send_response(stream_id, 200, end_stream=False)

        # TEST: Send a datagram to the browser right after handshake
        try:
            self._quic.send_datagram_frame(b"hello from server after handshake")
            transmit_coro = self.transmit()
            if transmit_coro is not None:
                asyncio.create_task(transmit_coro)
            logger.debug("Sent test datagram after handshake")
        except Exception as e:
            logger.error(f"Failed to send test datagram: {e}")

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

        logger.info(f"QUIC: server running on {HOST}:{QUIC_PORT}")
        await asyncio.Future()  # Run forever

    except Exception as e:
        logger.critical(f"QUIC: server failed to start: {e}", exc_info=True)
        raise