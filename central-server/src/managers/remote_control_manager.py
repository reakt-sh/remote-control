import asyncio
from typing import Dict, Optional, TYPE_CHECKING
from fastapi import WebSocket

from utils.app_logger import logger
from managers.webrtc_manager import WebRTCManager

if TYPE_CHECKING:
    from server_controller import ServerController

class RemoteControlManager:
    def __init__(self, server_controller: Optional['ServerController'] = None):
        self.active_connections: Dict[str, WebSocket] = {}
        self.webrtc_manager = WebRTCManager(server_controller)

    def set_server_controller(self, server_controller: 'ServerController'):
        """Set the server controller after initialization to avoid circular import"""
        self.webrtc_manager.set_server_controller(server_controller)

    def start_webrtc_relay(self):
        """Start the WebRTC relay background task. Must be called after event loop is running."""
        self.webrtc_manager.start_relay_task()

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
        # Ensure peer connection exists before creating offer
        if remote_control_id not in self.webrtc_manager.peer_connections:
            logger.info(f"RemoteControl: Creating new peer connection for {remote_control_id}")
            await self.webrtc_manager.create_peer_connection(remote_control_id)
        else:
            # Check if existing connection is closed/failed
            pc = self.webrtc_manager.peer_connections[remote_control_id]
            if pc.connectionState in ['closed', 'failed']:
                logger.info(f"RemoteControl: Recreating peer connection for {remote_control_id} (state: {pc.connectionState})")
                await self.webrtc_manager.close_peer_connection(remote_control_id)
                await self.webrtc_manager.create_peer_connection(remote_control_id)

        return await self.webrtc_manager.create_offer(remote_control_id)

    async def set_webrtc_answer(self, remote_control_id: str, answer: dict):
        """Set WebRTC answer from remote control"""
        await self.webrtc_manager.set_remote_description(remote_control_id, answer)

    async def add_webrtc_ice_candidate(self, remote_control_id: str, candidate: dict):
        """Add ICE candidate from remote control"""
        await self.webrtc_manager.add_ice_candidate(remote_control_id, candidate)