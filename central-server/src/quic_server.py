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

initialize_counter: int = 0

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

class QUICRelayProtocol(QuicConnectionProtocol):
    def __init__(self, *args, client_manager: ClientManager, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_manager = client_manager
        self.train_id = None
        self.is_train = False
        self.is_web_client = False

        self.file = open("video_dump.h264", "wb")
        self.current_frame = bytearray()
        self.current_frame_id = -1

        self.h3_connection: Optional[H3Connection] = None

        global initialize_counter
        initialize_counter += 1
        logger.debug(f"QUIC: Relay Protocol initialized, {initialize_counter} instances created")

    def quic_event_received(self, event: QuicEvent) -> None:
        logger.debug(f"QUIC: Received event: {event}")

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
            if not self.is_train and not self.is_web_client:
                try:
                    message = event.data.decode()
                    if message.startswith("TRAIN:"):
                        self.is_train = True
                        self.train_id = message[6:]  # Extract train ID
                        logger.debug(f"Train {self.train_id} connected via QUIC")
                        return
                    elif message.startswith("CLIENT:"):
                        self.is_web_client = True
                        self.train_id = message[7:]  # Extract train ID
                        logger.debug(f"Web client for train {self.train_id} connected via QUIC")
                        return
                    else:
                        logger.warning(f"Unknown client identification message: {message}")
                        return
                except UnicodeDecodeError:
                    logger.warning("Could not decode client identification message")
                    return

            if self.is_train and event.data[0] == PACKET_TYPE["video"]:
                # Header = 1 byte for packet type, 4 byte for frame_id, 2 byte for number of packets, 2 byte for packet_id, 36 byte for train_id
                packet_type = event.data[0]
                frame_id = int.from_bytes(event.data[1:5], byteorder='big')
                number_of_packets = int.from_bytes(event.data[5:7], byteorder='big')
                packet_id = int.from_bytes(event.data[7:9], byteorder='big')
                train_id = event.data[9:45].decode('utf-8')
                payload = event.data[45:]
                logger.debug(f"QUIC: {train_id} - Video Packet ==> frame_id: {frame_id}, number_of_packets: {number_of_packets}, packet_id: {packet_id}, payload size: {len(payload)}")

                if self.current_frame_id != frame_id:
                    self.current_frame = bytearray()
                    self.current_frame_id = frame_id
                    self.current_frame.extend(payload)
                else:
                    self.current_frame.extend(payload)
                    if packet_id == number_of_packets:
                        # now write to a file to test
                        self.file.write(self.current_frame)
                        self.file.flush()
                        logger.debug(f"QUIC: Received complete video frame {frame_id} of size {len(self.current_frame)}")
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