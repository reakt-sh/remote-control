import asyncio
import queue
from PyQt5.QtCore import QThread
from aioquic.asyncio import connect

class NetworkWorkerQuic(QThread):
    def __init__(self, server_host, server_port, parent=None):
        super().__init__(parent)
        self.server_host = server_host
        self.server_port = server_port
        self.packet_queue = queue.Queue()
        self.running = False
        self.loop = None

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
        async with connect(self.server_host, self.server_port, configuration=None) as client:
            stream_id = client._quic.get_next_available_stream_id()
            while self.running:
                try:
                    packet = self.packet_queue.get_nowait()
                    if packet:
                        client._quic.send_stream_data(stream_id, packet)
                        await client.transmit()
                except queue.Empty:
                    await asyncio.sleep(0.01)
                except Exception as e:
                    print(f"QUIC sender error: {e}")
                    break

    def stop(self):
        self.running = False

    def enqueue_packet(self, packet):
        self.packet_queue.put(packet)