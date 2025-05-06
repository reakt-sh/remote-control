import asyncio
from typing import Dict
from fastapi import WebSocket
from utils.app_logger import logger

class TrainManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.telemetry_data: Dict[str, dict] = {}

    async def connect(self, train_id: str, websocket: WebSocket):
        self.active_connections[train_id] = websocket

    async def disconnect(self, train_id: str):
        if train_id in self.active_connections:
            websocket = self.active_connections.pop(train_id, None)
            if websocket:
                try:
                    await websocket.close()
                except Exception as e:
                    logger.error(f"WebSocket for train already closed {train_id}: {e}")

    async def disconnect_all(self):
        for connection in self.active_connections.values():
            await connection.close()
        self.active_connections.clear()
        logger.debug("All train connections closed.")

    async def receive_video(self, train_id: str, data: bytes):
        """Forward video to all control clients"""
        pass

    async def update_telemetry(self, train_id: str, data: dict):
        self.telemetry_data[train_id] = data