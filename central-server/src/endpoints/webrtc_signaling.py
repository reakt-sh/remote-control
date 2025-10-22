"""
WebRTC Signaling Endpoint for Train Client Connections

This module handles WebRTC signaling for establishing peer connections
between train clients and web clients.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
import json
from typing import Dict, Optional
import asyncio

router = APIRouter()

# Store active WebRTC connections
# Structure: {train_client_id: {"train": WebSocket, "web_clients": [WebSocket, ...]}}
webrtc_connections: Dict[str, Dict] = {}


class WebRTCSignalingManager:
    """Manages WebRTC signaling between train clients and web clients."""
    
    def __init__(self):
        self.connections = webrtc_connections
    
    async def register_train_client(self, train_id: str, websocket: WebSocket):
        """Register a train client for WebRTC signaling."""
        if train_id not in self.connections:
            self.connections[train_id] = {
                "train": websocket,
                "web_clients": []
            }
        else:
            self.connections[train_id]["train"] = websocket
        
        logger.info(f"Train client {train_id} registered for WebRTC signaling")
    
    async def register_web_client(self, train_id: str, websocket: WebSocket):
        """Register a web client for WebRTC signaling."""
        if train_id not in self.connections:
            self.connections[train_id] = {
                "train": None,
                "web_clients": [websocket]
            }
        else:
            if websocket not in self.connections[train_id]["web_clients"]:
                self.connections[train_id]["web_clients"].append(websocket)
        
        logger.info(f"Web client registered for train {train_id} WebRTC signaling")
    
    async def unregister_train_client(self, train_id: str):
        """Unregister a train client."""
        if train_id in self.connections:
            self.connections[train_id]["train"] = None
            # If no web clients, remove entry
            if not self.connections[train_id]["web_clients"]:
                del self.connections[train_id]
        
        logger.info(f"Train client {train_id} unregistered from WebRTC signaling")
    
    async def unregister_web_client(self, train_id: str, websocket: WebSocket):
        """Unregister a web client."""
        if train_id in self.connections:
            if websocket in self.connections[train_id]["web_clients"]:
                self.connections[train_id]["web_clients"].remove(websocket)
            
            # If no train and no web clients, remove entry
            if not self.connections[train_id]["train"] and not self.connections[train_id]["web_clients"]:
                del self.connections[train_id]
        
        logger.info(f"Web client unregistered from train {train_id} WebRTC signaling")
    
    async def forward_to_web_clients(self, train_id: str, message: dict):
        """Forward signaling message from train to all web clients."""
        if train_id not in self.connections:
            logger.warning(f"No connections for train {train_id}")
            return
        
        web_clients = self.connections[train_id]["web_clients"]
        if not web_clients:
            logger.warning(f"No web clients for train {train_id}")
            return
        
        # Send to all web clients
        disconnected_clients = []
        for client in web_clients:
            try:
                await client.send_json(message)
            except Exception as e:
                logger.error(f"Error forwarding to web client: {e}")
                disconnected_clients.append(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            await self.unregister_web_client(train_id, client)
    
    async def forward_to_train(self, train_id: str, message: dict):
        """Forward signaling message from web client to train."""
        if train_id not in self.connections:
            logger.warning(f"No connections for train {train_id}")
            return
        
        train_ws = self.connections[train_id]["train"]
        if not train_ws:
            logger.warning(f"No train client for {train_id}")
            return
        
        try:
            await train_ws.send_json(message)
        except Exception as e:
            logger.error(f"Error forwarding to train: {e}")


# Global manager instance
signaling_manager = WebRTCSignalingManager()


@router.websocket("/webrtc/train/{train_client_id}")
async def webrtc_signaling_train(websocket: WebSocket, train_client_id: str):
    """
    WebRTC signaling endpoint for train clients.
    Handles offer/answer exchange and ICE candidate forwarding.
    """
    logger.info(f"WebRTC signaling connection attempt from train {train_client_id}")
    logger.debug(f"WebSocket headers: {websocket.headers}")
    await websocket.accept()
    await signaling_manager.register_train_client(train_client_id, websocket)
    
    try:
        logger.info(f"WebRTC signaling connection established with train {train_client_id}")
        
        while True:
            # Receive message from train
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type")
            logger.debug(f"Received {msg_type} from train {train_client_id}")
            
            if msg_type == "offer":
                # Forward offer to web clients
                await signaling_manager.forward_to_web_clients(train_client_id, {
                    "type": "offer",
                    "trainClientId": train_client_id,
                    "sdp": message.get("sdp")
                })
                
            elif msg_type == "ice":
                # Forward ICE candidate to web clients
                await signaling_manager.forward_to_web_clients(train_client_id, {
                    "type": "ice",
                    "trainClientId": train_client_id,
                    "candidate": message.get("candidate"),
                    "sdpMid": message.get("sdpMid"),
                    "sdpMLineIndex": message.get("sdpMLineIndex")
                })
            
            else:
                logger.warning(f"Unknown message type from train: {msg_type}")
    
    except WebSocketDisconnect:
        logger.info(f"Train {train_client_id} disconnected from WebRTC signaling")
    except Exception as e:
        logger.error(f"Error in train WebRTC signaling: {e}")
    finally:
        await signaling_manager.unregister_train_client(train_client_id)


@router.websocket("/webrtc/web/{train_client_id}")
async def webrtc_signaling_web(websocket: WebSocket, train_client_id: str):
    """
    WebRTC signaling endpoint for web clients.
    Handles answer and ICE candidate forwarding to train.
    """
    await websocket.accept()
    await signaling_manager.register_web_client(train_client_id, websocket)
    
    try:
        logger.info(f"WebRTC signaling connection established with web client for train {train_client_id}")
        
        # If train is already connected, notify web client
        if train_client_id in signaling_manager.connections:
            train_ws = signaling_manager.connections[train_client_id]["train"]
            if train_ws:
                await websocket.send_json({
                    "type": "ready",
                    "trainClientId": train_client_id,
                    "message": "Train client is connected and ready"
                })
        
        while True:
            # Receive message from web client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type")
            logger.debug(f"Received {msg_type} from web client for train {train_client_id}")
            
            if msg_type == "answer":
                # Forward answer to train
                await signaling_manager.forward_to_train(train_client_id, {
                    "type": "answer",
                    "sdp": message.get("sdp")
                })
                
            elif msg_type == "ice":
                # Forward ICE candidate to train
                await signaling_manager.forward_to_train(train_client_id, {
                    "type": "ice",
                    "candidate": message.get("candidate"),
                    "sdpMid": message.get("sdpMid"),
                    "sdpMLineIndex": message.get("sdpMLineIndex")
                })
            
            else:
                logger.warning(f"Unknown message type from web client: {msg_type}")
    
    except WebSocketDisconnect:
        logger.info(f"Web client disconnected from train {train_client_id} WebRTC signaling")
    except Exception as e:
        logger.error(f"Error in web WebRTC signaling: {e}")
    finally:
        await signaling_manager.unregister_web_client(train_client_id, websocket)


@router.get("/webrtc/status/{train_client_id}")
async def get_webrtc_status(train_client_id: str):
    """
    Get WebRTC connection status for a train.
    """
    if train_client_id in signaling_manager.connections:
        conn = signaling_manager.connections[train_client_id]
        return {
            "trainClientId": train_client_id,
            "trainConnected": conn["train"] is not None,
            "webClientsConnected": len(conn["web_clients"]),
            "status": "active"
        }
    else:
        return {
            "trainClientId": train_client_id,
            "trainConnected": False,
            "webClientsConnected": 0,
            "status": "inactive"
        }


@router.get("/webrtc/status")
async def get_all_webrtc_status():
    """
    Get WebRTC connection status for all trains.
    """
    status = {}
    for train_id, conn in signaling_manager.connections.items():
        status[train_id] = {
            "trainConnected": conn["train"] is not None,
            "webClientsConnected": len(conn["web_clients"])
        }
    return status
