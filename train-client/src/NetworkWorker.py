import asyncio
import queue
from PyQt5.QtCore import QThread, pyqtSignal
import websockets


class NetworkWorker(QThread):
    packet_sent = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.packet_queue = queue.Queue()
        self.running = True
        self.loop = None
        self.server_url = "ws://127.0.0.1:8000/ws/train/123"

    def run(self):
        # This is the QThread run method, runs in its own thread
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.websocket_sender())
        finally:
            self.loop.close()

    async def websocket_sender(self):
        try:
            async with websockets.connect(self.server_url) as websocket:
                while self.running:
                    try:
                        packet = self.packet_queue.get(timeout=0.1)
                        if packet:
                            await websocket.send(packet)
                            self.packet_sent.emit(len(packet))
                    except queue.Empty:
                        await asyncio.sleep(0.01)
        except Exception as e:
            print(f"WebSocket error: {e}")

    def stop(self):
        self.running = False
        if self.loop:
            # Wait for loop to finish cleanly
            self.quit()
            self.wait()

    def enqueue_packet(self, packet):
        self.packet_queue.put(packet)
