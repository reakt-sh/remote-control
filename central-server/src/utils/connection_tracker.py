import asyncio
from enum import Enum
from typing import Dict, Set, Optional
from dataclasses import dataclass
from utils.app_logger import logger


class ConnectionProtocol(Enum):
    """Available transport protocols for video streaming"""
    WEBTRANSPORT = "webtransport"  # QUIC-based, preferred for low latency
    WEBRTC = "webrtc"              # UDP-based, widely supported
    WEBSOCKET = "websocket"        # TCP-based, fallback for legacy


@dataclass
class ConnectionCapability:
    remote_control_id: str
    webtransport_available: bool = False
    webrtc_available: bool = False
    websocket_available: bool = False
    preferred_protocol: Optional[ConnectionProtocol] = None
    active_protocol: Optional[ConnectionProtocol] = None


class ConnectionTracker:
    def __init__(self):
        # Track transport capabilities per remote control
        self.capabilities: Dict[str, ConnectionCapability] = {}
        # Default protocol priority (can be configured)
        self.protocol_priority = [
            ConnectionProtocol.WEBTRANSPORT,
            ConnectionProtocol.WEBRTC,
            ConnectionProtocol.WEBSOCKET
        ]

        logger.info("Connection Tracker initialized")

    def create_if_not_exists(self, remote_control_id: str) -> ConnectionCapability:
        if remote_control_id not in self.capabilities:
            self.capabilities[remote_control_id] = ConnectionCapability(
                remote_control_id=remote_control_id
            )
        return self.capabilities[remote_control_id]

    def delete_if_exists(self, remote_control_id: str):
        if remote_control_id in self.capabilities:
            del self.capabilities[remote_control_id]

    def update_webtransport_status(self, remote_control_id: str, available: bool):
        capability = self.create_if_not_exists(remote_control_id)
        capability.webtransport_available = available

    def update_webrtc_status(self, remote_control_id: str, available: bool):
        capability = self.create_if_not_exists(remote_control_id)
        capability.webrtc_available = available

    def update_websocket_status(self, remote_control_id: str, available: bool):
        capability = self.create_if_not_exists(remote_control_id)
        capability.websocket_available = available

    def is_webtransport_available(self, remote_control_id: str) -> bool:
        capability = self.capabilities.get(remote_control_id)
        return capability.webtransport_available if capability else False

    def is_webrtc_available(self, remote_control_id: str) -> bool:
        capability = self.capabilities.get(remote_control_id)
        return capability.webrtc_available if capability else False

    def is_websocket_available(self, remote_control_id: str) -> bool:
        capability = self.capabilities.get(remote_control_id)
        return capability.websocket_available if capability else False

    def get_capabilities(self, remote_control_id: str) -> Optional[ConnectionCapability]:
        return self.capabilities.get(remote_control_id)

