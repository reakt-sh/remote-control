import asyncio
from typing import Dict
from fastapi import WebSocket
from utils.app_logger import logger

class RemoteControlManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def add(self, websocket: WebSocket, remote_control_id: str):
        self.active_connections[remote_control_id] = websocket

    async def remove(self, remote_control_id: str):
        if remote_control_id in self.active_connections:
            self.active_connections.pop(remote_control_id, None)

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