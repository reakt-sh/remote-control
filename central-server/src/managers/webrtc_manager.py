import asyncio
from typing import Dict, Optional
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCDataChannel
from aiortc.contrib.media import MediaRelay
from utils.app_logger import logger

class WebRTCManager:
    """
    Manages WebRTC peer connections for remote control clients.
    Server acts as a WebRTC peer for each remote control connection.
    """
    def __init__(self):
        self.peer_connections: Dict[str, RTCPeerConnection] = {}
        self.data_channels: Dict[str, RTCDataChannel] = {}
        self.pending_ice_candidates: Dict[str, list] = {}
        self.media_relay = MediaRelay()

    async def create_peer_connection(self, remote_control_id: str) -> RTCPeerConnection:
        """
        Create a new RTCPeerConnection for a remote control client.
        """
        if remote_control_id in self.peer_connections:
            logger.warning(f"WebRTC: Peer connection already exists for {remote_control_id}")
            return self.peer_connections[remote_control_id]

        pc = RTCPeerConnection()
        self.peer_connections[remote_control_id] = pc
        self.pending_ice_candidates[remote_control_id] = []

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"WebRTC: Connection state for {remote_control_id}: {pc.connectionState}")
            if pc.connectionState == "failed" or pc.connectionState == "closed":
                await self.close_peer_connection(remote_control_id)

        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            logger.info(f"WebRTC: ICE connection state for {remote_control_id}: {pc.iceConnectionState}")

        @pc.on("datachannel")
        def on_datachannel(channel: RTCDataChannel):
            logger.info(f"WebRTC: Data channel '{channel.label}' created by remote peer {remote_control_id}")
            self.data_channels[f"{remote_control_id}_{channel.label}"] = channel

            @channel.on("message")
            def on_message(message):
                # Handle incoming messages from web client (commands, etc.)
                logger.debug(f"WebRTC: Received message on channel '{channel.label}' from {remote_control_id}: {message[:50] if isinstance(message, (bytes, str)) else message}")

        logger.info(f"WebRTC: Created peer connection for {remote_control_id}")
        return pc

    async def create_data_channel(self, remote_control_id: str, channel_name: str = "video") -> Optional[RTCDataChannel]:
        """
        Create a data channel for sending video data to remote control.
        """
        pc = self.peer_connections.get(remote_control_id)
        if not pc:
            logger.error(f"WebRTC: No peer connection found for {remote_control_id}")
            return None

        channel = pc.createDataChannel(channel_name, ordered=False, maxRetransmits=0)
        self.data_channels[f"{remote_control_id}_{channel_name}"] = channel

        @channel.on("open")
        def on_open():
            logger.info(f"WebRTC: Data channel '{channel_name}' opened for {remote_control_id}")

        @channel.on("close")
        def on_close():
            logger.info(f"WebRTC: Data channel '{channel_name}' closed for {remote_control_id}")
            if f"{remote_control_id}_{channel_name}" in self.data_channels:
                del self.data_channels[f"{remote_control_id}_{channel_name}"]

        logger.info(f"WebRTC: Created data channel '{channel_name}' for {remote_control_id}")
        return channel

    async def create_offer(self, remote_control_id: str) -> dict:
        """
        Create and set local offer for the peer connection.
        """
        pc = self.peer_connections.get(remote_control_id)
        if not pc:
            logger.error(f"WebRTC: No peer connection found for {remote_control_id}")
            return {"error": "No peer connection found"}

        # Create data channel before creating offer
        await self.create_data_channel(remote_control_id, "video")
        await self.create_data_channel(remote_control_id, "commands")

        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        logger.info(f"WebRTC: Created offer for {remote_control_id}")
        return {
            "type": pc.localDescription.type,
            "sdp": pc.localDescription.sdp
        }

    async def set_remote_description(self, remote_control_id: str, sdp: dict):
        """
        Set the remote description (answer) from the web client.
        """
        pc = self.peer_connections.get(remote_control_id)
        if not pc:
            logger.error(f"WebRTC: No peer connection found for {remote_control_id}")
            return

        answer = RTCSessionDescription(sdp=sdp["sdp"], type=sdp["type"])
        await pc.setRemoteDescription(answer)
        logger.info(f"WebRTC: Set remote description for {remote_control_id}")

        # Process any pending ICE candidates
        if remote_control_id in self.pending_ice_candidates:
            for candidate in self.pending_ice_candidates[remote_control_id]:
                try:
                    await pc.addIceCandidate(candidate)
                except Exception as e:
                    logger.error(f"WebRTC: Error adding pending ICE candidate: {e}")
            self.pending_ice_candidates[remote_control_id].clear()

    async def add_ice_candidate(self, remote_control_id: str, candidate: dict):
        """
        Add an ICE candidate from the web client.
        """
        pc = self.peer_connections.get(remote_control_id)
        if not pc:
            logger.error(f"WebRTC: No peer connection found for {remote_control_id}")
            return

        try:
            from aiortc import RTCIceCandidate
            ice_candidate = RTCIceCandidate(
                component=candidate.get("component", 1),
                foundation=candidate.get("foundation", ""),
                ip=candidate.get("ip", ""),
                port=candidate.get("port", 0),
                priority=candidate.get("priority", 0),
                protocol=candidate.get("protocol", "udp"),
                type=candidate.get("type", "host"),
                sdpMid=candidate.get("sdpMid"),
                sdpMLineIndex=candidate.get("sdpMLineIndex")
            )

            if pc.remoteDescription:
                await pc.addIceCandidate(ice_candidate)
                logger.debug(f"WebRTC: Added ICE candidate for {remote_control_id}")
            else:
                # Store candidate if remote description not set yet
                self.pending_ice_candidates[remote_control_id].append(ice_candidate)
                logger.debug(f"WebRTC: Stored pending ICE candidate for {remote_control_id}")
        except Exception as e:
            logger.error(f"WebRTC: Error adding ICE candidate: {e}")

    async def send_video_data(self, remote_control_id: str, data: bytes):
        """
        Send video data to the remote control via WebRTC data channel.
        """
        channel_key = f"{remote_control_id}_video"
        channel = self.data_channels.get(channel_key)

        if not channel:
            logger.debug(f"WebRTC: No video channel found for {remote_control_id}")
            return

        if channel.readyState != "open":
            logger.debug(f"WebRTC: Video channel not open for {remote_control_id}, state: {channel.readyState}")
            return

        try:
            channel.send(data)
        except Exception as e:
            logger.error(f"WebRTC: Error sending video data to {remote_control_id}: {e}")

    async def send_command_data(self, remote_control_id: str, data: bytes):
        """
        Send command data to the remote control via WebRTC data channel.
        """
        channel_key = f"{remote_control_id}_commands"
        channel = self.data_channels.get(channel_key)

        if not channel:
            logger.debug(f"WebRTC: No commands channel found for {remote_control_id}")
            return

        if channel.readyState != "open":
            logger.debug(f"WebRTC: Commands channel not open for {remote_control_id}, state: {channel.readyState}")
            return

        try:
            channel.send(data)
        except Exception as e:
            logger.error(f"WebRTC: Error sending command data to {remote_control_id}: {e}")

    async def close_peer_connection(self, remote_control_id: str):
        """
        Close and cleanup peer connection for a remote control.
        """
        # Close data channels
        channels_to_remove = [key for key in self.data_channels.keys() if key.startswith(f"{remote_control_id}_")]
        for channel_key in channels_to_remove:
            try:
                channel = self.data_channels[channel_key]
                if channel.readyState == "open":
                    channel.close()
                del self.data_channels[channel_key]
            except Exception as e:
                logger.error(f"WebRTC: Error closing data channel {channel_key}: {e}")

        # Close peer connection
        if remote_control_id in self.peer_connections:
            pc = self.peer_connections[remote_control_id]
            try:
                await pc.close()
            except Exception as e:
                logger.error(f"WebRTC: Error closing peer connection for {remote_control_id}: {e}")
            del self.peer_connections[remote_control_id]

        # Clean up pending ICE candidates
        if remote_control_id in self.pending_ice_candidates:
            del self.pending_ice_candidates[remote_control_id]

        logger.info(f"WebRTC: Closed peer connection for {remote_control_id}")

    async def close_all(self):
        """
        Close all peer connections.
        """
        remote_control_ids = list(self.peer_connections.keys())
        for remote_control_id in remote_control_ids:
            await self.close_peer_connection(remote_control_id)
        logger.info("WebRTC: Closed all peer connections")
