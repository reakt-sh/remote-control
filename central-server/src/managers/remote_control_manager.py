import asyncio
from typing import Set
from fastapi import WebSocket
from utils.app_logger import logger

class RemoteControlManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def add(self, websocket: WebSocket):
        self.active_connections.add(websocket)

    async def remove(self, websocket: WebSocket):
        websocket = self.active_connections.pop(websocket)
        if websocket:
            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"WebSocket for remote control already closed")

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
        logger.debug("All remote control connections closed.")