import asyncio
from typing import Dict
from fastapi import WebSocket
from utils.app_logger import logger

# Mock database of trains
trains_db_mock = {
    "123": {
        "name": "Linux Dell-Latitude-5440 ",
        "status": "running",
        "speed": 0,
        "max_speed": 120,
        "brake_status": "released",
        "location": "Station A",
        "next_station": "Station B",
        "passenger_count": 156,
        "temperature": 22,
        "battery_level": 87,
        "video_stream_url": "/stream/train_1"
    },
    "526": {
        "name": "Windows Lenovo 8897",
        "status": "stopped",
        "speed": 0,
        "max_speed": 80,
        "brake_status": "applied",
        "location": "Depot 3",
        "next_station": "Loading Zone",
        "passenger_count": 2,
        "temperature": 18,
        "battery_level": 45,
        "video_stream_url": "/stream/train_2"
    }
}

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
        logger.debug("All train connections closed.")

    async def receive_video(self, train_id: str, data: bytes):
        """Forward video to all control clients"""
        pass

    async def update_telemetry(self, train_id: str, data: dict):
        self.telemetry_data[train_id] = data

    def get_trains(self):
        return trains_db_mock