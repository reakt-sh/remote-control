import asyncio
import json
import struct
import ssl
from typing import Optional
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate, VideoStreamTrack
from aiortc.contrib.media import MediaBlackhole
from av import VideoFrame
from PyQt5.QtCore import QThread, pyqtSignal
import websockets
from loguru import logger
import numpy as np

from globals import *


class H264VideoStreamTrack(VideoStreamTrack):
    """
    Custom video track that sends H.264 encoded frames via WebRTC.
    """
    def __init__(self):
        super().__init__()
        self.frame_queue = asyncio.Queue(maxsize=30)
        self._timestamp = 0
        self._start = None

    async def recv(self):
        """
        Receive the next video frame.
        Called by WebRTC to get frames for transmission.
        """
        try:
            # Get encoded frame from queue
            frame_data = await asyncio.wait_for(self.frame_queue.get(), timeout=1.0)
            
            if frame_data is None:
                raise StopIteration
            
            frame_id, timestamp, encoded_bytes = frame_data
            
            # Create a video frame from H.264 data
            # Note: aiortc expects decoded frames, so we need to handle this differently
            # For H.264 pass-through, we'll use data channels instead
            
            # For now, create a placeholder frame
            # In production, you'd decode H.264 or use data channels
            pts, time_base = await self.next_timestamp()
            
            frame = VideoFrame(width=1280, height=720, format="yuv420p")
            frame.pts = pts
            frame.time_base = time_base
            
            return frame
            
        except asyncio.TimeoutError:
            # Return a black frame if no data available
            pts, time_base = await self.next_timestamp()
            frame = VideoFrame(width=1280, height=720, format="yuv420p")
            frame.pts = pts
            frame.time_base = time_base
            return frame
        except Exception as e:
            logger.error(f"Error receiving frame: {e}")
            raise

    def enqueue_frame(self, frame_id: int, timestamp: int, encoded_bytes: bytes):
        """
        Enqueue an encoded frame for transmission.
        """
        try:
            self.frame_queue.put_nowait((frame_id, timestamp, encoded_bytes))
        except asyncio.QueueFull:
            logger.warning("Video frame queue full, dropping frame")


class NetworkWorkerWebRTC(QThread):
    """
    WebRTC network worker for video streaming using data channels.
    Uses WebSocket for signaling and WebRTC data channels for video transmission.
    """
    
    # Signals for Qt integration
    connection_established = pyqtSignal()
    connection_failed = pyqtSignal(str)
    connection_closed = pyqtSignal()
    process_command = pyqtSignal(object)
    data_received = pyqtSignal(bytes)

    def __init__(self, train_client_id: str, parent=None):
        super().__init__(parent)
        self.train_client_id = train_client_id
        self.train_client_id_bytes = train_client_id.encode('utf-8').ljust(36)[:36]
        
        # WebRTC components
        self.pc: Optional[RTCPeerConnection] = None
        self.data_channel = None
        self.video_track: Optional[H264VideoStreamTrack] = None
        
        # Signaling WebSocket
        # Remove /ws prefix from WEBSOCKET_URL and use the correct WebRTC endpoint
        base_url = WEBSOCKET_URL.replace("/ws", "")
        self.signaling_url = f"{base_url}/webrtc/train/{train_client_id}"
        self.signaling_ws = None
        
        # State management
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self.frame_queue = asyncio.Queue()
        self.packet_queue = asyncio.Queue()
        
        # Statistics
        self.keepalive_sequence = 0
        
        logger.info(f"WebRTC worker initialized for train {train_client_id}")

    def run(self):
        """Main thread entry point."""
        self._running = True
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self.run_client())
        except Exception as e:
            logger.error(f"WebRTC client error: {e}")
            self.connection_failed.emit(str(e))
        finally:
            if self._loop and self._loop.is_running():
                self._loop.stop()
            if self._loop:
                self._loop.close()
            self._running = False
            self.connection_closed.emit()

    async def run_client(self):
        """Main WebRTC client loop."""
        try:
            # Connect to signaling server
            ssl_context = ssl._create_unverified_context()
            async with websockets.connect(self.signaling_url, ssl=ssl_context) as ws:
                self.signaling_ws = ws
                logger.info(f"Connected to WebRTC signaling server: {self.signaling_url}")
                
                # Create peer connection
                await self.create_peer_connection()
                
                # Create data channel for video packets
                self.data_channel = self.pc.createDataChannel(
                    "video",
                    ordered=False,  # Allow out-of-order delivery for lower latency
                    maxRetransmits=0  # No retransmissions for real-time video
                )
                self.setup_data_channel_handlers()
                
                # Create and send offer
                await self.create_and_send_offer()
                
                self.connection_established.emit()
                
                # Start background tasks
                tasks = [
                    asyncio.create_task(self.signaling_handler()),
                    asyncio.create_task(self.send_video_packets()),
                    asyncio.create_task(self.send_keepalive()),
                ]
                
                # Wait for any task to complete
                done, pending = await asyncio.wait(
                    tasks,
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Cancel remaining tasks
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                        
        except Exception as e:
            logger.error(f"WebRTC connection error: {e}")
            self.connection_failed.emit(str(e))
        finally:
            await self.cleanup()

    async def create_peer_connection(self):
        """Create and configure RTCPeerConnection."""
        # Configure ICE servers (STUN/TURN)
        configuration = {
            "iceServers": [
                {"urls": "stun:stun.l.google.com:19302"},
                {"urls": "stun:stun1.l.google.com:19302"},
            ]
        }
        
        self.pc = RTCPeerConnection(configuration)
        
        # Set up connection state handlers
        @self.pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"WebRTC connection state: {self.pc.connectionState}")
            if self.pc.connectionState == "failed":
                await self.pc.close()
                self.connection_failed.emit("Connection failed")
            elif self.pc.connectionState == "closed":
                self.connection_closed.emit()
        
        @self.pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            logger.info(f"ICE connection state: {self.pc.iceConnectionState}")
        
        @self.pc.on("icegatheringstatechange")
        async def on_icegatheringstatechange():
            logger.info(f"ICE gathering state: {self.pc.iceGatheringState}")
        
        @self.pc.on("datachannel")
        def on_datachannel(channel):
            logger.info(f"Data channel created: {channel.label}")
            self.setup_data_channel_handlers(channel)
        
        logger.info("RTCPeerConnection created")

    def setup_data_channel_handlers(self, channel=None):
        """Set up data channel event handlers."""
        if channel is None:
            channel = self.data_channel
        
        @channel.on("open")
        def on_open():
            logger.info(f"Data channel '{channel.label}' opened")
        
        @channel.on("close")
        def on_close():
            logger.info(f"Data channel '{channel.label}' closed")
        
        @channel.on("message")
        def on_message(message):
            try:
                if isinstance(message, str):
                    data = json.loads(message)
                    logger.debug(f"Received message: {data}")
                elif isinstance(message, bytes):
                    # Handle binary command messages
                    packet_type = message[0]
                    payload = message[1:]
                    if packet_type == PACKET_TYPE["command"]:
                        self.process_command.emit(payload)
                    self.data_received.emit(message)
            except Exception as e:
                logger.error(f"Error processing data channel message: {e}")

    async def create_and_send_offer(self):
        """Create WebRTC offer and send to signaling server."""
        try:
            # Create offer
            offer = await self.pc.createOffer()
            await self.pc.setLocalDescription(offer)
            
            # Send offer via signaling
            offer_message = {
                "type": "offer",
                "trainClientId": self.train_client_id,
                "sdp": self.pc.localDescription.sdp,
            }
            await self.signaling_ws.send(json.dumps(offer_message))
            logger.info("WebRTC offer sent")
            
        except Exception as e:
            logger.error(f"Error creating offer: {e}")
            raise

    async def signaling_handler(self):
        """Handle signaling messages from server."""
        while self._running:
            try:
                message = await asyncio.wait_for(
                    self.signaling_ws.recv(),
                    timeout=1.0
                )
                
                data = json.loads(message)
                msg_type = data.get("type")
                
                if msg_type == "answer":
                    # Received answer from remote peer
                    answer = RTCSessionDescription(
                        sdp=data["sdp"],
                        type="answer"
                    )
                    await self.pc.setRemoteDescription(answer)
                    logger.info("WebRTC answer received and set")
                    
                elif msg_type == "ice":
                    # Received ICE candidate
                    candidate = RTCIceCandidate(
                        candidate=data["candidate"],
                        sdpMid=data.get("sdpMid"),
                        sdpMLineIndex=data.get("sdpMLineIndex")
                    )
                    await self.pc.addIceCandidate(candidate)
                    logger.debug("ICE candidate added")
                    
                elif msg_type == "error":
                    logger.error(f"Signaling error: {data.get('message')}")
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Signaling handler error: {e}")
                break

    async def send_video_packets(self):
        """Send video packets via data channel."""
        while self._running:
            try:
                # Get frame from queue
                frame_id, timestamp, frame_bytes = await asyncio.wait_for(
                    self.frame_queue.get(),
                    timeout=0.1
                )
                
                # Check if data channel is ready
                if self.data_channel and self.data_channel.readyState == "open":
                    # Create packets
                    packets = self.create_packets(frame_id, timestamp, frame_bytes)
                    
                    # Send each packet via data channel
                    for packet in packets:
                        try:
                            self.data_channel.send(packet)
                        except Exception as e:
                            logger.error(f"Error sending packet: {e}")
                            break
                else:
                    logger.warning("Data channel not ready, dropping frame")
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in send loop: {e}")
                await asyncio.sleep(0.1)

    async def send_keepalive(self):
        """Send periodic keepalive messages."""
        while self._running:
            try:
                await asyncio.sleep(10)
                
                if self.data_channel and self.data_channel.readyState == "open":
                    self.keepalive_sequence += 1
                    keepalive_packet = {
                        "type": "keepalive",
                        "protocol": "webrtc",
                        "trainClientId": self.train_client_id,
                        "timestamp": asyncio.get_event_loop().time(),
                        "sequence": self.keepalive_sequence
                    }
                    
                    packet_data = json.dumps(keepalive_packet).encode('utf-8')
                    packet = struct.pack("B", PACKET_TYPE["keepalive"]) + packet_data
                    
                    self.data_channel.send(packet)
                    logger.debug(f"Sent keepalive {self.keepalive_sequence}")
                    
            except Exception as e:
                logger.error(f"Error sending keepalive: {e}")

    def create_packets(self, frame_id: int, timestamp: int, frame: bytes) -> list[bytes]:
        """
        Create video packets with proper header structure.
        Identical to QUIC/WebSocket implementation for compatibility.
        """
        packet_list = []
        frame_size = len(frame)
        
        # Header is 53 bytes: 1 + 4 + 2 + 2 + 36 + 8 = 53
        header_size = 53
        max_payload_size = MAX_PACKET_SIZE - header_size
        
        # Calculate number of packets needed
        number_of_packets = (frame_size + max_payload_size - 1) // max_payload_size
        remaining_data = frame

        logger.debug(f"Creating {number_of_packets} WebRTC packets for frame {frame_id}, "
                    f"frame_size: {frame_size}")

        for packet_id in range(1, number_of_packets + 1):
            header = bytearray()
            header.append(PACKET_TYPE["video"])
            header.extend(frame_id.to_bytes(4, byteorder='big'))
            header.extend(number_of_packets.to_bytes(2, byteorder='big'))
            header.extend(packet_id.to_bytes(2, byteorder='big'))
            header.extend(self.train_client_id_bytes)
            header.extend(timestamp.to_bytes(8, byteorder='big'))

            chunk = remaining_data[:max_payload_size]
            remaining_data = remaining_data[max_payload_size:]
            
            full_packet = bytes(header + chunk)
            packet_list.append(full_packet)
            
            if len(full_packet) > MAX_PACKET_SIZE:
                logger.error(f"WebRTC packet {packet_id} size {len(full_packet)} exceeds MAX_PACKET_SIZE")

        return packet_list

    def enqueue_frame(self, frame_id: int, timestamp: int, frame: bytes):
        """Enqueue a frame for transmission."""
        if not self._running or not self._loop:
            logger.warning("Cannot enqueue frame - WebRTC client not running")
            return
        
        try:
            self._loop.call_soon_threadsafe(
                self.frame_queue.put_nowait,
                (frame_id, timestamp, frame)
            )
        except Exception as e:
            logger.error(f"Error enqueuing frame: {e}")

    def enqueue_packet(self, data: bytes):
        """Enqueue a packet for transmission (e.g., telemetry)."""
        if not self._running or not self._loop:
            logger.warning("Cannot enqueue packet - WebRTC client not running")
            return
        
        try:
            if self.data_channel and self.data_channel.readyState == "open":
                self._loop.call_soon_threadsafe(
                    self.data_channel.send,
                    data
                )
        except Exception as e:
            logger.error(f"Error enqueuing packet: {e}")

    async def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up WebRTC connection")
        
        try:
            if self.data_channel:
                self.data_channel.close()
            
            if self.pc:
                await self.pc.close()
            
            if self.signaling_ws:
                await self.signaling_ws.close()
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def stop(self):
        """Stop the WebRTC worker."""
        self._running = False
        self.quit()
        self.wait(4000)
        logger.info("WebRTC worker stopped")
