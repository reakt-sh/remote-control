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
        self.web_clients: Dict[str, Set[QuicConnectionProtocol]] = defaultdict(set)
        self.lock = asyncio.Lock()

    async def add_train_client(self, train_id: str, protocol: QuicConnectionProtocol):
        async with self.lock:
            self.train_clients[train_id] = protocol
            logger.info(f"QUIC: Train client connected: {train_id}")

    async def remove_train_client(self, train_id: str):
        async with self.lock:
            if train_id in self.train_clients:
                del self.train_clients[train_id]
                logger.info(f"QUIC: Train client disconnected: {train_id}")

    async def add_web_client(self, train_id: str, protocol: QuicConnectionProtocol):
        async with self.lock:
            self.web_clients[train_id].add(protocol)
            logger.info(f"QUIC: Web client connected for train {train_id}")

    async def remove_web_client(self, train_id: str, protocol: QuicConnectionProtocol):
        async with self.lock:
            if train_id in self.web_clients and protocol in self.web_clients[train_id]:
                self.web_clients[train_id].remove(protocol)
                logger.info(f"QUIC: Web client disconnected for train {train_id}")

    async def get_web_clients(self, train_id: str) -> List[QuicConnectionProtocol]:
        async with self.lock:
            return list(self.web_clients.get(train_id, []))

    async def get_train_client(self, train_id: str) -> Optional[QuicConnectionProtocol]:
        async with self.lock:
            return self.train_clients.get(train_id)

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
        logger.debug(f"QUIC: Received QuicEvent")

        if isinstance(event, ProtocolNegotiated):
            logger.debug(f"QUIC: Protocol negotiated: {event.alpn_protocol}")
            if event.alpn_protocol == 'h3':
                self.h3_connection = H3Connection(self._quic, enable_webtransport=True)
                logger.debug(f"QUIC: setting connection to H3Connection")
        elif isinstance(event, StreamReset) and self._handler is not None:
            # Streams in QUIC can be closed in two ways: normal (FIN) and
            # abnormal (resets).  FIN is handled by the handler; the code
            # below handles the resets.
            logger.debug(f"QUIC: Stream reset event caught: {event.stream_id}")
        else:
            pass

        if self.h3_connection is not None:
            for h3_event in self.h3_connection.handle_event(event):
                self._h3_event_received(h3_event)

        if isinstance(event, StreamDataReceived):
            # Identify client type
            if self.client_type is None:
                try:
                    message = event.data.decode()
                    if message.startswith("TRAIN:"):
                        self.client_type = "TRAIN"
                        self.train_id = message[6:]  # Extract train ID
                        self.video_stream_handler = VideoStreamHandler(self.train_id)
                        logger.info(f"Train {self.train_id} connected via QUIC")
                        return
                    elif message.startswith("REMOTE_CONTROL:"):
                        self.client_type = "REMOTE_CONTROL"
                        self.remote_control_id = message[7:]  # Extract train ID
                        logger.info(f"Remote Control {self.remote_control_id} connected via QUIC")
                        return
                    else:
                        logger.warning(f"Unknown client identification message: {message}")
                        return
                except UnicodeDecodeError:
                    logger.warning("Could not decode client identification message")
                    return

            if self.client_type == "TRAIN" and event.data and event.data[0] == PACKET_TYPE["video"]:
                frame = self.video_stream_handler.process_packet(event.data)
                if frame:
                    self.file.write(frame)
                    self.file.flush()
            else:
                logger.debug(f"QUIC: Received unhandled data : {event.data}")
        if isinstance(event, DatagramFrameReceived):
            logger.debug(f"QUIC: Received datagram frame: {event.data}")
        if isinstance(event, ConnectionIdIssued):
            logger.debug(f"QUIC: Received ConnectionIDIssued: {event.connection_id}")

    def _h3_event_received(self, event: H3Event) -> None:
        logger.debug(f"QUIC: Received H3 event: {event}")
        if isinstance(event, HeadersReceived):
            headers = {}
            for header, value in event.headers:
                headers[header] = value
            if (headers.get(b":method") == b"CONNECT" and
                    headers.get(b":protocol") == b"webtransport"):
                self._handshake_webtransport(event.stream_id, headers)
            else:
                self._send_response(event.stream_id, 400, end_stream=True)

    def _handshake_webtransport(self, stream_id: int, request_headers: Dict[bytes, bytes]) -> None:
        authority = request_headers.get(b":authority")
        path = request_headers.get(b":path")
        logger.debug(f"QUIC: Handshake webtransport: {authority}, {path}")
        self._send_response(stream_id, 200, end_stream=True)

    def _send_response(self, stream_id: int, status_code: int, end_stream=False) -> None:
        headers = [(b":status", str(status_code).encode())]
        if status_code == 200:
            headers.append((b"sec-webtransport-http3-draft", b"draft02"))
        self.h3_connection.send_headers(stream_id=stream_id, headers=headers, end_stream=end_stream)

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