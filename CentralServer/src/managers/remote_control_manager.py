import asyncio
from typing import Set
from fastapi import WebSocket

class RemoteControlManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    async def disconnect(self, websocket: WebSocket):
        await websocket.close()
        self.active_connections.remove(websocket)

    async def broadcast_video(self, data: bytes):
        """Send video to all control clients"""
        for connection in self.active_connections:
            await connection.send_bytes(data)

    async def send_command(self, train_id: str, command: dict):
        """Forward command to specific train"""
        pass

    async def disconnect_all(self):
        for connection in list(self.active_connections):
            await connection.close()
        self.active_connections.clear()