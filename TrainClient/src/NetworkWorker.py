import queue
import asyncio
from time import sleep
from PyQt5.QtCore import QThread, pyqtSignal
from aioquic.asyncio import connect
from aioquic.quic.configuration import QuicConfiguration

class NetworkWorker(QThread):
    packet_sent = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.packet_queue = queue.Queue()
        self.running = True
        self.loop = None

        # QUIC configuration
        self.server_addr = "127.0.0.1"
        self.server_port = 4433
        self.quic_config = QuicConfiguration(is_client=True, alpn_protocols=["hq-29"])

    def run(self):
        # Start asyncio event loop in this thread
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.quic_sender())

    async def quic_sender(self):
        async with connect(
            self.server_addr, self.server_port, configuration=self.quic_config
        ) as client:
            stream_id = client._quic.get_next_available_stream_id()
            while self.running:
                try:
                    packet = self.packet_queue.get(timeout=0.1)
                    if packet:
                        await client.send_stream_data(stream_id, packet, end_stream=False)
                        self.packet_sent.emit(len(packet))
                except queue.Empty:
                    await asyncio.sleep(0.01)
            await client.send_stream_data(stream_id, b"", end_stream=True)

    def stop(self):
        self.running = False
        sleep(1)  # Give some time for the loop to finish

    def enqueue_packet(self, packet):
        self.packet_queue.put(packet)