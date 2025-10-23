import asyncio
from typing import Dict, Optional
from fastapi import WebSocket

from utils.app_logger import logger
from managers.webrtc_manager import WebRTCManager

class RemoteControlManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.webrtc_manager = WebRTCManager()

    async def add(self, websocket: WebSocket, remote_control_id: str):
        self.active_connections[remote_control_id] = websocket
        # Create WebRTC peer connection for this remote control
        await self.webrtc_manager.create_peer_connection(remote_control_id)
        logger.info(f"RemoteControl: Added {remote_control_id} with WebRTC support")

    async def remove(self, remote_control_id: str):
        if remote_control_id in self.active_connections:
            self.active_connections.pop(remote_control_id, None)
        # Close WebRTC peer connection
        await self.webrtc_manager.close_peer_connection(remote_control_id)
        logger.info(f"RemoteControl: Removed {remote_control_id}")

    async def disconnect_all(self):
        for connection in list(self.active_connections.values()):
            await connection.close()
        self.active_connections.clear()
        # Close all WebRTC connections
        await self.webrtc_manager.close_all()
        logger.info("RemoteControl: Disconnected all connections")

    async def send_video_via_webrtc(self, remote_control_id: str, data: bytes):
        """Send video data to remote control via WebRTC data channel"""
        await self.webrtc_manager.send_video_data(remote_control_id, data)

    async def get_webrtc_offer(self, remote_control_id: str) -> dict:
        """Get WebRTC offer for remote control"""
        return await self.webrtc_manager.create_offer(remote_control_id)

    async def set_webrtc_answer(self, remote_control_id: str, answer: dict):
        """Set WebRTC answer from remote control"""
        await self.webrtc_manager.set_remote_description(remote_control_id, answer)

    async def add_webrtc_ice_candidate(self, remote_control_id: str, candidate: dict):
        """Add ICE candidate from remote control"""
        await self.webrtc_manager.add_ice_candidate(remote_control_id, candidate)