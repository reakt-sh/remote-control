import asyncio
import queue
import json
import struct
from PyQt5.QtCore import QThread, pyqtSignal
import websockets

from globals import *

class NetworkWorker(QThread):
    packet_sent = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.packet_queue = queue.Queue()
        self.running = False
        self.loop = None
        self.server_url = f"{SERVER_URL}/train/{TRAIN_ID}"

    def run(self):
        self.running = True
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.websocket_handler())
        finally:
            self.loop.close()

    async def websocket_handler(self):
        try:
            async with websockets.connect(self.server_url) as websocket:
                print(f"Connected to server at {self.server_url}")
                # Create tasks
                tasks = [
                    asyncio.create_task(self.websocket_sender(websocket)),
                    asyncio.create_task(self.websocket_receiver(websocket)),
                    asyncio.create_task(self.keepalive(websocket))
                ]
                # Wait for the first task to complete (which will happen if any fails)
                done, pending = await asyncio.wait(
                    tasks,
                    return_when=asyncio.FIRST_COMPLETED
                )
                # Cancel remaining tasks
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
        except Exception as e:
            print(f"WebSocket connection error: {e}")

    async def websocket_sender(self, websocket):
        print("### Sender task started ###")
        while self.running:
            try:
                packet = self.packet_queue.get_nowait()
                if packet:
                    await websocket.send(packet)
                    self.packet_sent.emit(len(packet))
            except queue.Empty:
                await asyncio.sleep(0.1)  # Increased sleep to yield to other tasks
            except Exception as e:
                print(f"Sender error: {e}")
                break

    async def websocket_receiver(self, websocket):
        print("### Receiver task started ###")
        while self.running:
            try:
                packet = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                if packet:
                    print(f"Received packet: {packet}")
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Receiver error: {e}")
                break

    async def keepalive(self, websocket):
        print("### Keepalive task started ###")
        while self.running:
            try:
                keepalive_packet = {
                    "timestamp": asyncio.get_event_loop().time()
                }
                packet_data = json.dumps(keepalive_packet).encode('utf-8')
                packet = struct.pack("B", PACKET_TYPE["keepalive"]) + packet_data
                await websocket.send(packet)
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Keepalive error: {e}")
                break

    def stop(self):
        self.running = False

    def enqueue_packet(self, packet):
        self.packet_queue.put(packet)