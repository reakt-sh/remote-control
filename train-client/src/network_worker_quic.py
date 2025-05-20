import asyncio
import queue
import ssl
import threading

from PyQt5.QtCore import QThread
from aioquic.asyncio import connect
from aioquic.quic.configuration import QuicConfiguration

from globals import *


class NetworkWorkerQUIC(threading.Thread):
    def __init__(self, train_client_id, parent=None):
        super().__init__(parent)
        self.train_client_id = train_client_id

        self.configuration = QuicConfiguration(is_client=True)
        self.configuration.verify_mode = ssl.CERT_NONE  # For testing, disable verification mode

        self.server_host = QUIC_HOST
        self.server_port = QUIC_PORT
        self.packet_queue = queue.Queue()
        self.running = False
        self.loop = None
        print(f"QUIC: server URL: {self.server_host}:{self.server_port}")


    def run(self):
        self.running = True
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.quic_sender())
        finally:
            self.loop.close()

    async def quic_sender(self):
        print("QUIC: Sender task started")
        try:
            async with connect(
                self.server_host,
                self.server_port,
                configuration=self.configuration,
            ) as client:
                # Send train identification first
                stream_id = client._quic.get_next_available_stream_id()
                handshake = f"TRAIN:{self.train_client_id}".encode()
                client._quic.send_stream_data(stream_id, handshake)
                await client.transmit()
                print(f"QUIC: handshake sent, stream ID: {stream_id}")

                while self.running:
                    try:
                        packet = self.packet_queue.get_nowait()
                        if packet:
                            client._quic.send_stream_data(stream_id, packet)
                            await client.transmit()
                    except queue.Empty:
                        await asyncio.sleep(0.01)
                    except Exception as e:
                        print(f"QUIC: sender error: {e}")
                        break
        except Exception as e:
            print(f"QUIC: connection failed: {type(e).__name__}: {e}")

    def stop(self):
        self.running = False

    def enqueue_packet(self, packet):
        self.packet_queue.put(packet)