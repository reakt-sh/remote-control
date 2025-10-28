import asyncio
import time
from typing import Dict, Optional
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCDataChannel, RTCCertificate
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
        self.keepalive_tasks: Dict[str, asyncio.Task] = {}
        self.last_activity: Dict[str, float] = {}
        # Generate a persistent DTLS certificate for all connections
        # This prevents OpenSSL issues and improves connection stability
        self.dtls_certificate = RTCCertificate.generateCertificate()
        logger.info(f"WebRTC: Generated DTLS certificate with fingerprint: {self.dtls_certificate.getFingerprints()[0]}")

    async def create_peer_connection(self, remote_control_id: str) -> RTCPeerConnection:
        """
        Create a new RTCPeerConnection for a remote control client.
        """
        if remote_control_id in self.peer_connections:
            logger.warning(f"WebRTC: Peer connection already exists for {remote_control_id}")
            return self.peer_connections[remote_control_id]

        # Create peer connection with configuration for stability
        from aiortc import RTCConfiguration, RTCIceServer
        
        config = RTCConfiguration(
            iceServers=[
                RTCIceServer(urls=["stun:stun.l.google.com:19302"]),
                RTCIceServer(urls=["stun:stun1.l.google.com:19302"])
            ]
        )
        
        # Create peer connection with persistent DTLS certificate
        # This ensures stable DTLS negotiation and prevents OpenSSL errors
        pc = RTCPeerConnection(configuration=config)
        pc.configuration.certificates = [self.dtls_certificate]
        
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

        @pc.on("icegatheringstatechange")
        async def on_icegatheringstatechange():
            logger.info(f"WebRTC: ICE gathering state for {remote_control_id}: {pc.iceGatheringState}")

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

    def get_certificate_info(self) -> dict:
        """
        Get information about the current DTLS certificate.
        Useful for debugging and monitoring.
        """
        try:
            fingerprints = self.dtls_certificate.getFingerprints()
            return {
                "fingerprint": fingerprints[0] if fingerprints else "N/A",
                "active_connections": len(self.peer_connections),
                "certificate_expires": "Check certificate validity manually"
            }
        except Exception as e:
            logger.error(f"WebRTC: Error getting certificate info: {e}")
            return {"error": str(e)}

    async def create_data_channel(self, remote_control_id: str, channel_name: str = "video") -> Optional[RTCDataChannel]:
        """
        Create a data channel for sending video data to remote control.
        """
        pc = self.peer_connections.get(remote_control_id)
        if not pc:
            logger.error(f"WebRTC: No peer connection found for {remote_control_id}")
            return None
        
        channel_key = f"{remote_control_id}_{channel_name}"
        
        # Check if channel already exists and is still valid
        if channel_key in self.data_channels:
            existing_channel = self.data_channels[channel_key]
            if existing_channel.readyState in ['connecting', 'open']:
                logger.debug(f"WebRTC: Data channel '{channel_name}' already exists for {remote_control_id} (state: {existing_channel.readyState})")
                return existing_channel
            else:
                logger.debug(f"WebRTC: Removing stale data channel '{channel_name}' for {remote_control_id} (state: {existing_channel.readyState})")
                del self.data_channels[channel_key]

        # Create data channel with proper configuration
        # ordered=False and maxRetransmits=0 for low latency
        # Set bufferedAmountLowThreshold to prevent buffer overflow
        channel = pc.createDataChannel(
            channel_name, 
            ordered=False, 
            maxRetransmits=0
        )
        
        self.data_channels[channel_key] = channel

        @channel.on("open")
        def on_open():
            logger.info(f"WebRTC: Data channel '{channel_name}' opened for {remote_control_id}")
            # Start keepalive for this connection
            if channel_name == "video":
                self._start_keepalive(remote_control_id)

        @channel.on("close")
        def on_close():
            logger.info(f"WebRTC: Data channel '{channel_name}' closed for {remote_control_id}")
            if channel_key in self.data_channels:
                del self.data_channels[channel_key]

        @channel.on("error")
        def on_error(error):
            logger.error(f"WebRTC: Data channel '{channel_name}' error for {remote_control_id}: {error}")

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
        
        # Check if peer connection is in a valid state
        if pc.connectionState in ['closed', 'failed']:
            logger.error(f"WebRTC: Peer connection for {remote_control_id} is in state: {pc.connectionState}")
            return {"error": f"Peer connection is {pc.connectionState}"}

        try:
            # Create data channels before creating offer
            # This ensures the m= sections are properly created in the SDP
            video_channel = await self.create_data_channel(remote_control_id, "video")
            commands_channel = await self.create_data_channel(remote_control_id, "commands")

            if not video_channel or not commands_channel:
                logger.error(f"WebRTC: Failed to create data channels for {remote_control_id}")
                return {"error": "Failed to create data channels"}

            # Wait a brief moment to ensure channels are initialized
            await asyncio.sleep(0.1)

            # Create the offer after data channels are set up
            offer = await pc.createOffer()
            await pc.setLocalDescription(offer)

            # Verify the SDP has proper m= sections
            sdp_lines = pc.localDescription.sdp.split('\n')
            m_sections = [line for line in sdp_lines if line.startswith('m=')]
            mid_lines = [line for line in sdp_lines if line.startswith('a=mid:')]
            
            logger.info(f"WebRTC: Created offer for {remote_control_id}")
            logger.debug(f"WebRTC: Offer has {len(m_sections)} m= sections and {len(mid_lines)} MID attributes")
            logger.debug(f"WebRTC: Offer SDP:\n{pc.localDescription.sdp}")
            
            # Validate the offer before returning
            if not pc.localDescription or not pc.localDescription.sdp or not pc.localDescription.type:
                logger.error(f"WebRTC: Generated invalid offer for {remote_control_id}")
                return {"error": "Generated offer is invalid"}
            
            if len(m_sections) == 0:
                logger.error(f"WebRTC: Offer has no media sections for {remote_control_id}")
                return {"error": "Offer has no media sections"}
            
            return {
                "type": pc.localDescription.type,
                "sdp": pc.localDescription.sdp
            }
        except Exception as e:
            logger.error(f"WebRTC: Exception creating offer for {remote_control_id}: {e}")
            import traceback
            logger.error(f"WebRTC: Traceback: {traceback.format_exc()}")
            
            # Check if it's a DTLS-related error
            if "ssl" in str(e).lower() or "dtls" in str(e).lower() or "certificate" in str(e).lower():
                logger.error(f"WebRTC: DTLS/SSL error detected. Certificate fingerprint: {self.dtls_certificate.getFingerprints()[0]}")
            
            return {"error": f"Exception: {str(e)}"}

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
        Implements backpressure handling to prevent buffer overflow.
        """
        channel_key = f"{remote_control_id}_video"
        channel = self.data_channels.get(channel_key)

        if not channel:
            # logger.debug(f"WebRTC: No video channel found for {remote_control_id}")
            return

        if channel.readyState != "open":
            logger.debug(f"WebRTC: Video channel not open for {remote_control_id}, state: {channel.readyState}")
            return

        try:
            # Check buffered amount to prevent overflow (16MB default buffer)
            # Drop frames if buffer is too full to maintain low latency
            max_buffer_size = 4 * 1024 * 1024  # 4MB threshold

            if hasattr(channel, 'bufferedAmount') and channel.bufferedAmount > max_buffer_size:
                logger.warning(f"WebRTC: Buffer full ({channel.bufferedAmount} bytes) for {remote_control_id}, dropping frame")
                return

            channel.send(data)
            self.last_activity[remote_control_id] = time.time()

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

    def _start_keepalive(self, remote_control_id: str):
        """
        Start keepalive task for a peer connection.
        Sends periodic ping messages to keep the connection alive.
        """
        if remote_control_id in self.keepalive_tasks:
            logger.debug(f"WebRTC: Keepalive already running for {remote_control_id}")
            return

        async def keepalive_loop():
            logger.info(f"WebRTC: Starting keepalive for {remote_control_id}")
            while remote_control_id in self.peer_connections:
                try:
                    await asyncio.sleep(5)  # Send keepalive every 5 seconds

                    channel_key = f"{remote_control_id}_commands"
                    channel = self.data_channels.get(channel_key)

                    if channel and channel.readyState == "open":
                        # Send a small keepalive ping
                        keepalive_msg = b'\x00PING'
                        channel.send(keepalive_msg)
                        logger.debug(f"WebRTC: Sent keepalive to {remote_control_id}")
                    else:
                        logger.warning(f"WebRTC: Commands channel not available for keepalive {remote_control_id}")

                except asyncio.CancelledError:
                    logger.info(f"WebRTC: Keepalive cancelled for {remote_control_id}")
                    break
                except Exception as e:
                    logger.error(f"WebRTC: Keepalive error for {remote_control_id}: {e}")
                    await asyncio.sleep(5)  # Continue even if there's an error

        task = asyncio.create_task(keepalive_loop())
        self.keepalive_tasks[remote_control_id] = task
        self.last_activity[remote_control_id] = time.time()

    def _stop_keepalive(self, remote_control_id: str):
        """
        Stop keepalive task for a peer connection.
        """
        if remote_control_id in self.keepalive_tasks:
            task = self.keepalive_tasks[remote_control_id]
            task.cancel()
            del self.keepalive_tasks[remote_control_id]
            logger.info(f"WebRTC: Stopped keepalive for {remote_control_id}")
        
        if remote_control_id in self.last_activity:
            del self.last_activity[remote_control_id]

    async def close_peer_connection(self, remote_control_id: str):
        """
        Close and cleanup peer connection for a remote control.
        """
        # Stop keepalive
        self._stop_keepalive(remote_control_id)
        
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
