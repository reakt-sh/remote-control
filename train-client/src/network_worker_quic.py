import asyncio
import queue
import ssl
import json
import struct
import datetime
import threading
from typing import Optional


from app_logger import logger
from aioquic.asyncio import connect
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.connection import QuicConnection
from aioquic.quic.events import QuicEvent, StreamDataReceived, DatagramFrameReceived, ConnectionTerminated, StreamReset
from aioquic.asyncio.protocol import QuicStreamAdapter
from aioquic.asyncio.protocol import QuicConnectionProtocol

from globals import *

original_stream_close = QuicStreamAdapter.close

def patched_stream_close(self):
    try:
        original_stream_close(self)
    except ValueError as e:
        if "Cannot send data on peer-initiated unidirectional stream" in str(e):
            pass  # Ignore harmless cleanup errors
        else:
            raise

QuicStreamAdapter.close = patched_stream_close


class _Signal:
    """Lightweight callback signal, drop-in for pyqtSignal in non-Qt threads."""

    def __init__(self):
        self._callbacks = []

    def connect(self, callback):
        self._callbacks.append(callback)

    def emit(self, *args):
        for cb in self._callbacks:
            cb(*args)


class NetworkWorkerQUIC:
    def __init__(self, train_client_id: str, parent=None):
        self.connection_established = _Signal()
        self.connection_failed = _Signal()
        self.connection_closed = _Signal()
        self.stream_data = _Signal()

        self._thread: Optional[threading.Thread] = None
        self.train_client_id = train_client_id
        self.train_client_id_bytes = train_client_id.encode('utf-8').ljust(36)[:36]  # Ensure 36 bytes

        # QUIC Configuration
        self.configuration = QuicConfiguration(
            is_client=True,
            alpn_protocols=["quic"],
            max_datagram_frame_size=65536,
            idle_timeout=30.0,
        )
        self.configuration.verify_mode = ssl.CERT_NONE  # For testing only

        self.server_host = SERVER
        self.server_port = QUIC_PORT
        self.frame_queue = queue.Queue(maxsize=30)  # Use asyncio.Queue
        self.stream_packet_queue = queue.Queue()  # Use asyncio.Queue
        self._running = False
        self._client: Optional[QuicConnection] = None
        self._stream_id: Optional[int] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        logger.info(f"QUIC client initialized for train {train_client_id}")
        logger.info(f"QUIC server URL: {self.server_host}:{self.server_port}")

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True, name='NetworkWorkerQUIC')
        self._thread.start()

    def _run(self):
        self._running = True
        try:
            # Create a new event loop for this thread
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self.run_client())
        except Exception as e:
            logger.error(f"QUIC client error: {e}")
            self.connection_failed.emit(str(e))
        finally:
            if self._loop and self._loop.is_running():
                self._loop.stop()
            if self._loop:
                self._loop.close()
            self._running = False
            self.connection_closed.emit()

    async def run_client(self):
        try:
            async with connect(
                self.server_host,
                self.server_port,
                configuration=self.configuration,
                create_protocol=lambda *args, **kwargs: QuicClientProtocol(
                *args, network_worker=self, **kwargs
            )
            ) as client:
                self._client = client
                self.connection_established.emit()

                # Get a new stream ID for communication
                self._stream_id = client._quic.get_next_available_stream_id(is_unidirectional=False)

                logger.debug(f"Sending QUIC handshake on stream {self._stream_id}")
                # Send train identification
                client._quic.send_stream_data(self._stream_id, self.prepareConnectMessage(), end_stream=False)
                result = client.transmit()
                if result is not None:
                    await result
                logger.info(f"QUIC handshake sent on stream {self._stream_id}")

                asyncio.create_task(self.send_stream_reliable())  # Start sending stream packets

                # Main sending loop
                await self.send_datagram_unreliable()

        except Exception as e:
            logger.error(f"QUIC connection error: {e}")
            self.connection_failed.emit(str(e))

    def prepareConnectMessage(self):
        connect_packet = {
            "type": "connect",
            "train_id": self.train_client_id,
        }
        packet_data = json.dumps(connect_packet).encode('utf-8')

        # Create packet with type byte + data
        packet = struct.pack("B", PACKET_TYPE["connect"]) + packet_data

        # Add 2-byte length prefix (big-endian)
        data_size = len(packet)
        length_prefixed_packet = bytearray(2 + len(packet))
        length_prefixed_packet[0] = (data_size >> 8) & 0xFF  # High byte
        length_prefixed_packet[1] = data_size & 0xFF         # Low byte
        length_prefixed_packet[2:] = packet

        return bytes(length_prefixed_packet)

    async def send_stream_reliable(self):
        while self._running:
            try:
                packet = self.stream_packet_queue.get_nowait()
                self._client._quic.send_stream_data(self._stream_id, packet, end_stream=False)
                result = self._client.transmit()
                if result is not None:
                    await result
                await asyncio.sleep(0.1)  # 100ms delay
            except queue.Empty:
                await asyncio.sleep(0.1)
                continue


    async def send_datagram_unreliable(self):
        while self._running:
            try:
                # Get frame from queue with timeout
                try:
                    frame_id, timestamp, frame, camera_type = self.frame_queue.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.01)
                    continue

                # Split frame into packets and send
                packet_list = self.create_packets(frame_id, timestamp, frame, camera_type)
                for packet in packet_list:
                    if not self._running:
                        break
                    if self._client is None:
                        raise ConnectionError("Client not connected")

                    self._client._quic.send_datagram_frame(packet)
                    result = self._client.transmit()
                    if result is not None:
                        await result

            except ConnectionError as e:
                logger.error(f"Connection lost: {e}")
                break
            except Exception as e:
                logger.error(f"Error in send loop: {e}")
                continue

    def create_packets(self, frame_id: int, timestamp: int, frame: bytes, camera_type: str) -> list[bytes]:
        packet_list = []
        frame_size = len(frame)
        number_of_packets = (frame_size // MAX_PACKET_SIZE) + 1
        remaining_data = frame

        for packet_id in range(1, number_of_packets + 1):
            header = bytearray()
            if camera_type == CAMERA_TYPE["FRONT"]:
                header.append(PACKET_TYPE["video_front"])
            elif camera_type == CAMERA_TYPE["REAR"]:
                header.append(PACKET_TYPE["video_rear"])
            else:
                pass
            header.extend(frame_id.to_bytes(4, byteorder='big'))
            header.extend(number_of_packets.to_bytes(2, byteorder='big'))
            header.extend(packet_id.to_bytes(2, byteorder='big'))
            header.extend(self.train_client_id_bytes)
            header.extend(timestamp.to_bytes(8, byteorder='big'))

            chunk = remaining_data[:MAX_PACKET_SIZE]
            remaining_data = remaining_data[MAX_PACKET_SIZE:]
            packet_list.append(bytes(header + chunk))

        return packet_list

    def enqueue_frame(self, frame_id: int, timestamp: int, frame: bytes, camera_type: str):
        if not self._running or not self._loop:
            logger.warning("Cannot enqueue frame - client not running")
            return
        try:
            self.frame_queue.put((frame_id, timestamp, frame, camera_type))
        except Exception as e:
            logger.error(f"Error enqueuing frame: {e}")

    def enqueue_stream_packet(self, data: bytes):
        if not self._running or not self._loop:
            logger.warning("Cannot enqueue stream packet - client not running")
            return
        self.stream_packet_queue.put(data)

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=4.0)

class QuicClientProtocol(QuicConnectionProtocol):  # <-- inherit from QuicConnectionProtocol
    def __init__(self, *args, network_worker: NetworkWorkerQUIC, **kwargs):
        super().__init__(*args, **kwargs)
        self.network_worker = network_worker

    def quic_event_received(self, event: QuicEvent):
        if isinstance(event, ConnectionTerminated):
            logger.error(f"QUIC connection terminated! Error code: {event.error_code}, "
                        f"Reason: {event.reason_phrase}")
            self.network_worker._running = False
            self.network_worker.connection_closed.emit()
            return

        if isinstance(event, StreamReset):
            logger.warning(f"Stream {event.stream_id} reset! Error code: {event.error_code}")
            # Potentially reconnect or handle gracefully
            return

        if isinstance(event, StreamDataReceived):
            self.network_worker.stream_data.emit(event.data)  # Emit raw stream data for processing

