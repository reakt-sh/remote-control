import asyncio
import queue
import json
import struct
from PyQt5.QtCore import QThread, pyqtSignal
import websockets
from loguru import logger

from globals import *

class NetworkWorkerWS(QThread):
    process_command = pyqtSignal(object)

    def __init__(self, train_client_id, parent=None):
        super().__init__(parent)
        self.packet_queue = queue.Queue()
        self.train_client_id = train_client_id
        self.running = False
        self.loop = None
        self.server_url = f"{WEBSOCKET_URL}/train/{train_client_id}"

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
                print(f"WebSocket: Connected to server at {self.server_url}")
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
            print(f"WebSocket: connection error: {e}")

    async def websocket_sender(self, websocket):
        print("WebSocket: Sender task started")
        while self.running:
            try:
                packet = self.packet_queue.get_nowait()
                if packet:
                    await websocket.send(packet)
            except queue.Empty:
                await asyncio.sleep(0.1)  # Increased sleep to yield to other tasks
            except Exception as e:
                print(f"WebSocket: Sender error: {e}")
                break

    async def websocket_receiver(self, websocket):
        print("WebSocket: Receiver task started")
        while self.running:
            try:
                packet = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                if packet:
                    print(f"WebSocket: Received packet of size {len(packet)}")
                    packet_type = packet[0]
                    payload = packet[1:]
                    if packet_type == PACKET_TYPE["keepalive"]:
                        message = json.loads(payload.decode('utf-8'))
                        print(f"WebSocket: Keepalive message: {message}")
                    elif packet_type == PACKET_TYPE["command"]:
                        self.process_command.emit(payload)
                    else:
                        print(f"WebSocket: Received packet type {packet_type}, not handled")
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"WebSocket: Receiver error: {e}")
                break

    async def keepalive(self, websocket):
        print("WebSocket: Keepalive task started")
        self.keepalive_sequence = 0
        while self.running:
            try:
                self.keepalive_sequence += 1
                keepalive_packet = {
                    "type": "keepalive",
                    "timestamp": asyncio.get_event_loop().time(),
                    "sequence": self.keepalive_sequence
                }
                packet_data = json.dumps(keepalive_packet).encode('utf-8')
                packet = struct.pack("B", PACKET_TYPE["keepalive"]) + packet_data
                await websocket.send(packet)
                await asyncio.sleep(25)
            except Exception as e:
                print(f"WebSocket: Keepalive error: {e}")
                break

    def stop(self):
        self.running = False
        logger.info("WebSocket connection closed")

    def enqueue_packet(self, packet):
        self.packet_queue.put(packet)