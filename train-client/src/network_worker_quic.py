import asyncio
import queue
import ssl
from typing import Optional

from loguru import logger
from PyQt5.QtCore import QThread, pyqtSignal
from aioquic.asyncio import connect
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.connection import QuicConnection
from aioquic.quic.events import QuicEvent, StreamDataReceived, DatagramFrameReceived, ConnectionTerminated, StreamReset

from globals import *

class NetworkWorkerQUIC(QThread):
    # Signals for Qt integration
    connection_established = pyqtSignal()
    connection_failed = pyqtSignal(str)
    connection_closed = pyqtSignal()
    data_received = pyqtSignal(bytes)  # Signal for received data

    def __init__(self, train_client_id: str, parent=None):
        super().__init__(parent)
        self.train_client_id = train_client_id
        self.train_client_id_bytes = train_client_id.encode('utf-8').ljust(36)[:36]  # Ensure 36 bytes

        # QUIC Configuration
        self.configuration = QuicConfiguration(
            is_client=True,
            alpn_protocols=["h3", "webtransport"],
            max_datagram_frame_size=65536,
            idle_timeout=30.0,
        )
        self.configuration.verify_mode = ssl.CERT_NONE  # For testing only

        self.server_host = QUIC_HOST
        self.server_port = QUIC_PORT
        self.frame_queue = queue.Queue()  # Use asyncio.Queue
        self._running = False
        self._client: Optional[QuicConnection] = None
        self._stream_id: Optional[int] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        logger.info(f"QUIC client initialized for train {train_client_id}")
        logger.info(f"QUIC server URL: {self.server_host}:{self.server_port}")

    def run(self):
        self._running = True
        try:
            # Create a new event loop for this thread
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._run_client())
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

    async def _run_client(self):
        try:
            async with connect(
                self.server_host,
                self.server_port,
                configuration=self.configuration,
            ) as client:
                self._client = client
                logger.info("QUIC connection established")
                self.connection_established.emit()

                # Get a new stream ID for communication
                self._stream_id = client._quic.get_next_available_stream_id(is_unidirectional=False)

                # Start receiving events
                asyncio.create_task(self._receive_events(client))

                # Send train identification
                handshake = f"TRAIN:{self.train_client_id}".encode()
                client._quic.send_stream_data(self._stream_id, handshake, end_stream=False)
                result = client.transmit()
                if result is not None:
                    await result
                logger.info(f"QUIC handshake sent on stream {self._stream_id}")

                # Main sending loop
                await self._send_loop()

        except Exception as e:
            logger.error(f"QUIC connection error: {e}")
            self.connection_failed.emit(str(e))
        finally:
            self._client = None
            self._stream_id = None

    async def _send_loop(self):
        while self._running:
            try:
                # Get frame from queue with timeout
                try:
                    frame_id, frame = self.frame_queue.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.01)
                    continue

                # Split frame into packets and send
                packet_list = self._create_packets(frame_id, frame)
                for packet in packet_list:
                    if not self._running:
                        break
                    if self._client is None:
                        raise ConnectionError("Client not connected")

                    logger.debug(f"Sending packet for frame {frame_id}, size: {len(packet)} bytes")
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

    async def _receive_events(self, client: QuicConnection):
        while self._running:
            try:
                event = client._quic.next_event()
                if event is None:
                    await asyncio.sleep(1)
                    continue

                logger.info(f"Processing QUIC event: {event}")

                if isinstance(event, StreamDataReceived):
                    if event.stream_id == self._stream_id:
                        logger.info(f"Received stream data on stream {event.stream_id}: {event.data!r}")
                        self.data_received.emit(event.data)
                        if event.end_stream:
                            logger.info(f"Stream {event.stream_id} closed by server")
                            break
                    else:
                        logger.warning(f"Received data on unexpected stream {event.stream_id}")

                elif isinstance(event, DatagramFrameReceived):
                    logger.info(f"Received datagram: {event.data!r}")
                    self.data_received.emit(event.data)

                elif isinstance(event, StreamReset):
                    logger.error(f"Stream {event.stream_id} reset: error code {event.error_code}")
                    self.connection_failed.emit(f"Stream reset: {event.error_code}")
                    break

                elif isinstance(event, ConnectionTerminated):
                    logger.error(f"Connection terminated: {event.reason_phrase} (error code: {event.error_code})")
                    self.connection_failed.emit("Connection terminated by server")
                    break

            except Exception as e:
                logger.error(f"Error processing QUIC events: {e}")
                self.connection_failed.emit(str(e))
                break

    def _create_packets(self, frame_id: int, frame: bytes) -> list[bytes]:
        packet_list = []
        frame_size = len(frame)
        number_of_packets = (frame_size // MAX_PACKET_SIZE) + 1
        remaining_data = frame

        for packet_id in range(1, number_of_packets + 1):
            header = bytearray()
            header.append(PACKET_TYPE["video"])
            header.extend(frame_id.to_bytes(4, byteorder='big'))
            header.extend(number_of_packets.to_bytes(2, byteorder='big'))
            header.extend(packet_id.to_bytes(2, byteorder='big'))
            header.extend(self.train_client_id_bytes)

            chunk = remaining_data[:MAX_PACKET_SIZE]
            remaining_data = remaining_data[MAX_PACKET_SIZE:]
            packet_list.append(bytes(header + chunk))

        return packet_list

    def enqueue_frame(self, frame_id: int, frame: bytes):
        """Add a frame to the sending queue"""
        if not self._running or not self._loop:
            logger.warning("Cannot enqueue frame - client not running")
            return
        try:
            self.frame_queue.put((frame_id, frame))
        except Exception as e:
            logger.error(f"Error enqueuing frame: {e}")

    def stop(self):
        """Gracefully stop the client"""
        self._running = False
        if self._client and self._loop and self._stream_id is not None:
            try:
                self._client._quic.send_stream_data(self._stream_id, b"", end_stream=True)
                future = asyncio.run_coroutine_threadsafe(self._client.transmit(), self._loop)
                future.result(timeout=1.0)  # Wait briefly for transmit
                self._client.close()
                future = asyncio.run_coroutine_threadsafe(self._client.transmit(), self._loop)
                future.result(timeout=1.0)
            except Exception as e:
                logger.error(f"Error during graceful shutdown: {e}")

        self.quit()
        self.wait(2000)