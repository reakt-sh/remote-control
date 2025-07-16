import asyncio
from typing import Dict, Optional
import json, os

from aioquic.asyncio import serve
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.quic.events import (
    QuicEvent,
    DatagramFrameReceived,
    StreamDataReceived,
    ConnectionIdIssued,
    ProtocolNegotiated,
    StreamReset,
    ConnectionTerminated,
)
from aioquic.quic.configuration import QuicConfiguration
from aioquic.h3.connection import H3Connection
from aioquic.h3.events import H3Event, HeadersReceived, DataReceived

from utils.app_logger import logger
from utils.video_datagram_assembler import VideoDatagramAssembler
from utils.calculator import Calculator
from managers.client_manager import ClientManager
from utils.simulation_process import SimulationProcess
from globals import *

class QUICRelayProtocol(QuicConnectionProtocol):
    def __init__(self, *args, client_manager: ClientManager, calculator: Calculator, sim_process: SimulationProcess, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_manager = client_manager
        self.sim_process = sim_process
        self.calculator = calculator
        self.client_type: Optional[str] = None
        self.train_id: Optional[str] = None
        self.remote_control_id: Optional[str] = None
        self.h3_connection: Optional[H3Connection] = None
        self.session_id: int = -1  # Default session ID
        self.stream_id: Optional[int] = None
        self.video_datagram_assembler: Optional[VideoDatagramAssembler] = None
        self.is_closed = False
        self.file = open("video_dump.h264", "wb")

    def connection_idle_timeout(self) -> None:
        logger.warning(f"QUIC: Connection idle timeout for train_id: {self.train_id}, remote_control_id: {self.remote_control_id}")
        self._close_connection()

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
            elif isinstance(event, ConnectionTerminated):
                self._close_connection()
            else:
                logger.warning(f"QUIC: Received unhandled event: {event}")

            if self.h3_connection is not None:
                for h3_event in self.h3_connection.handle_event(event):
                    self._h3_event_received(h3_event)

        except Exception as e:
            logger.error(f"QUIC: Error processing event: {e}, {event.data}", exc_info=True)
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
            self.calculator.calculate_bandwidth(len(event.data))

            # if a complete video frame is received, then write to a file to check
            # frame = self.video_datagram_assembler.process_packet(event.data)
            # if frame:
            #     logger.debug(f"QUIC: Received video frame for train {self.train_id}, size: {len(frame)} bytes")
            #     self.file.write(frame)
            #     self.file.flush()
        else:
            logger.warning(f"QUIC: Received unhandled data : {event.data}")

    def _handle_stream_data(self, event: StreamDataReceived) -> None:
        if self.client_type is None:
            try:
                message = event.data.decode()
                if message.startswith("TRAIN:"):
                    self.client_type = "TRAIN"
                    self.stream_id = event.stream_id
                    self.train_id = message[6:]  # Extract train ID
                    self.video_datagram_assembler = VideoDatagramAssembler(self.train_id)
                    asyncio.create_task(self.client_manager.add_train_client(self.train_id, self))

                    # try send Stream hello world message to the remote control
                    logger.debug(f"QUIC: stream received from stream_id: {event.stream_id}, train-id: {self.train_id}")
                    hello_message = f"HELLO: {self.train_id}".encode()
                    self._quic.send_stream_data(event.stream_id, hello_message, end_stream=False)
                    transmit_coro = self.transmit()
                    logger.debug(f"QUIC: hello_message sent to train {self.train_id}")
                    return
                elif message.startswith("REMOTE_CONTROL:"):
                    self.client_type = "REMOTE_CONTROL"
                    self.stream_id = event.stream_id
                    self.remote_control_id = message[15:]  # Extract train ID
                    asyncio.create_task(self.client_manager.add_remote_control_client(self.remote_control_id, self))

                    # If no train clients are connected, spawn a subprocess to run a simulated train client
                    if not self.client_manager.train_clients:
                        logger.info("No train clients connected. Spawning a simulated train client subprocess.")
                        self.sim_process.create_simulation_process()

                    # try send Stream hello world message to the remote control
                    hello_message = f"HELLO: {self.remote_control_id}".encode()
                    self._quic.send_stream_data(event.stream_id, hello_message, end_stream=False)
                    self.transmit()
                    logger.debug(f"QUIC: hello_message sent to Remote control {self.remote_control_id}")

                    # initiate download/upload speed test with the remote control
                    # asyncio.create_task(self.measure_download_speed())
                    return
                else:
                    logger.warning(f"Unknown client identification message: {message}")
                    return
            except UnicodeDecodeError:
                logger.warning("Could not decode client identification message")
                return

        elif self.client_type == "TRAIN" and event.data and event.data[0] == PACKET_TYPE["telemetry"]:
            asyncio.create_task(
                self.client_manager.relay_stream_to_remote_controls(self.train_id, event.data)
            )
        elif self.client_type == "TRAIN" and event.data and event.data[0] == PACKET_TYPE["keepalive"]:
            self.decode_keepalive_packet(event.data)
        elif self.client_type == "REMOTE_CONTROL":
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
            elif event.data[0] == PACKET_TYPE["command"]:
                asyncio.create_task(
                    self.client_manager.relay_stream_to_train(self.remote_control_id, event.data)
                )
            elif event.data[0] == PACKET_TYPE["keepalive"]:
                self.decode_keepalive_packet(event.data)
            else:
                logger.warning(f"QUIC: Received unhandled data from remote control {self.remote_control_id}: {message}")
        else:
            logger.debug(f"QUIC: Unhandled stream data on stream_id {event.stream_id}, data length: {len(event.data)}, data: {event.data[:50]}...")
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
        self.session_id = stream_id
        self._send_response(stream_id, 200, end_stream=False)

    def _send_response(self, stream_id: int, status_code: int, end_stream=False) -> None:
        headers = [(b":status", str(status_code).encode())]
        if status_code == 200:
            headers.append((b"sec-webtransport-http3-draft", b"02"))
        self.h3_connection.send_headers(stream_id=stream_id, headers=headers, end_stream=end_stream)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        if self.client_type == "TRAIN":
            logger.info(f"QUIC: Connection lost for train_id: {self.train_id}")
        elif self.client_type == "REMOTE_CONTROL":
            logger.info(f"QUIC: Connection lost for remote_control_id: {self.remote_control_id}")
        else:
            logger.warning("QUIC: Connection lost for unknown client type")

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
                await self.client_manager.remove_remote_control_client(self.remote_control_id)
                if not self.client_manager.remote_control_clients:
                    self.sim_process.destroy_simulation_process()
        except Exception as e:
            logger.error(f"Error cleaning up client: {e}")

    def decode_keepalive_packet(self, data) -> None:

        json_bytes = data[1:]
        try:
            json_str = json_bytes.decode('utf-8')
            payload = json.loads(json_str)
            logger.debug(f"Decoded keepalive packet: {payload}")

        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"Error decoding packet: {e}")
            print(f"Raw JSON bytes: {json_bytes}")

    async def measure_download_speed(self):
        logger.info(f"QUIC: Starting download speed test for remote control {self.remote_control_id}")
        # send 10MB of random bytes to the remote control
        totalBytes = 0

        data = bytearray(os.urandom(10 * 1024 * 1024))  # 10 MB of random data

        packet = data[:1024]  # 1 KB of random data
        packet[0] = PACKET_TYPE["download_start"]
        self.h3_connection.send_datagram(self.session_id, packet)
        totalBytes += len(packet)

        while totalBytes < 10 * 1024 * 1024:
            packet = data[totalBytes:totalBytes + 1024]  # 1 KB of random data
            packet[0] = PACKET_TYPE["downloading"]
            self.h3_connection.send_datagram(self.session_id, packet)
            totalBytes += len(packet)

        packet = bytearray(10)
        packet[0] = PACKET_TYPE["download_end"]
        self.h3_connection.send_datagram(self.session_id, packet)
        self.transmit()

    async def measure_upload_speed(self, data):
        packet_type = data[0]
        if packet_type == PACKET_TYPE["upload_start"]:
            totalBytes = len(data)
            self.upload_start_time = asyncio.get_event_loop().time()
        elif packet_type == PACKET_TYPE["uploading"]:
            totalBytes += len(data)
        elif packet_type == PACKET_TYPE["upload_end"]:
            self.upload_end_time = asyncio.get_event_loop().time()
            elapsed_time = self.upload_end_time - self.upload_start_time
            self.upload_speed = totalBytes / elapsed_time / 1024 / 1024
            logger.info(f"QUIC: Upload speed: {self.upload_speed:.2f} MB/s")
        else:
            logger.warning(f"QUIC: Received unhandled upload packet type: {packet_type}")


async def run_quic_server():
    try:
        config = get_client_config()

        quic_config = QuicConfiguration(
            is_client=False,
            alpn_protocols=["quic", "h3", "webtransport"],
            max_datagram_frame_size=2000,
            idle_timeout=30.0,  # 30 seconds idle timeout
        )
        quic_config.load_cert_chain(certfile=config.cert_file, keyfile=config.key_file)

        # Create a shared client manager
        client_manager = ClientManager()

        # Create a shared train simulation process
        sim_process = SimulationProcess()

        # create a shared Calculator instance
        calculator = Calculator()

        server = await serve(
            HOST,
            QUIC_PORT,
            configuration=quic_config,
            create_protocol=lambda *args, **kwargs: QUICRelayProtocol(
                *args, client_manager=client_manager, calculator=calculator, sim_process=sim_process, **kwargs
            )
        )

        logger.info(f"QUIC: server running on {HOST}:{QUIC_PORT}")
        await asyncio.Future()  # Run forever

    except Exception as e:
        logger.critical(f"QUIC: server failed to start: {e}", exc_info=True)
        raise