import asyncio
from random import randint
from typing import Dict
from fastapi import WebSocket

from src.utils.app_logger import logger
class TrainManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.telemetry_data: Dict[str, dict] = {}

    async def add(self, train_id: str, websocket: WebSocket):
        self.active_connections[train_id] = websocket

    async def remove(self, train_id: str):
        if train_id in self.active_connections:
            self.active_connections.pop(train_id, None)

    async def disconnect_all(self):
        for connection in self.active_connections.values():
            await connection.close()
        self.active_connections.clear()


    async def update_telemetry(self, train_id: str, data: dict):
        self.telemetry_data[train_id] = data

    def get_trains(self):
        train_client_ids = list(self.active_connections.keys())
        return train_client_ids