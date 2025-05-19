import asyncio
import queue
from PyQt5.QtCore import QThread
from aioquic.asyncio import connect
from globals import *


class NetworkWorkerQuic(QThread):
    def __init__(self, train_client_id, parent=None):
        super().__init__(parent)
        self.train_client_id = train_client_id

        self.server_host = SERVER_HOST
        self.server_port = QUIC_PORT
        self.packet_queue = queue.Queue()
        self.running = False
        self.loop = None
        print(f"QUIC server URL: {self.server_host}:{self.server_port}")


    def run(self):
        self.running = True
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.quic_sender())
        finally:
            self.loop.close()

    async def quic_sender(self):
        # NOTE: For production, use a real TLS configuration!
        print("### QUIC Sender task started ###")
        async with connect(self.server_host, self.server_port, configuration=None) as client:
            stream_id = client._quic.get_next_available_stream_id()
            while self.running:
                try:
                    print("Here in quic_sender")
                    packet = self.packet_queue.get_nowait()
                    if packet:
                        client._quic.send_stream_data(stream_id, packet)
                        print(f"trying to send packet: {packet}")
                        await client.transmit()
                        print(f"client.transmit() done")
                except queue.Empty:
                    await asyncio.sleep(0.01)
                except Exception as e:
                    print(f"QUIC sender error: {e}")
                    break

    def stop(self):
        self.running = False

    def enqueue_packet(self, packet):
        self.packet_queue.put(packet)