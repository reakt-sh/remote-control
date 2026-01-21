import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import time, os

from server_controller import ServerController
from utils.app_logger import logger
from globals import PACKET_TYPE


s_controller = ServerController()
router = APIRouter()
size_mb = 20  # 20MB test file
test_data = os.urandom(size_mb * 1024 * 1024)  # Generate random binary data


# Pydantic models for WebRTC signaling
class WebRTCOffer(BaseModel):
    remote_control_id: str

class WebRTCAnswer(BaseModel):
    remote_control_id: str
    sdp: dict

class WebRTCIceCandidate(BaseModel):
    remote_control_id: str
    candidate: dict


@router.websocket("/ws/remote_control/{remote_control_id}")
async def remote_control_interface(websocket: WebSocket, remote_control_id: str):
    logger.debug(f"WebSocket: connection established for web client:  {remote_control_id}")
    await websocket.accept()
    await s_controller.add_remote_controller(websocket, remote_control_id)
    try:
        while True:
            data = await websocket.receive_bytes()
            await s_controller.send_data_to_train(remote_control_id, data)
    except WebSocketDisconnect:
        await s_controller.remove_remote_controller(remote_control_id)
        s_controller.unmap_client_from_train(remote_control_id)

@router.get("/api/trains")
async def get_trains():
    data = s_controller.get_trains()
    logger.debug(f"HTTP: currently connected list of train ids: {data}")
    return data

@router.get("/stream/{train_id}")
async def get_stream(train_id: str):
    logger.debug(f"HTTP: etching stream for train {train_id}")
    return ""


@router.post("/api/remote_control/{remote_control_id}/train/{train_id}")
async def map_client_to_train(remote_control_id: str, train_id: str):
    logger.debug(f"HTTP: Mapping remote control {remote_control_id} to train {train_id}")
    s_controller.map_client_to_train(remote_control_id, train_id)
    return {
        "status": "success",
        "message": f"Mapped {remote_control_id} to {train_id}"
    }

@router.delete("/api/remote_control/{remote_control_id}/train")
async def unmap_client_from_train(remote_control_id: str):
    logger.debug(f"HTTP: Unmapping remote control {remote_control_id} from train")
    s_controller.unmap_client_from_train(remote_control_id)
    return {
        "status": "success",
        "message": f"Unmapped {remote_control_id}"
    }

@router.get("/api/speedtest/download")
async def speedtest_download():
    return Response(content=test_data, media_type="application/octet-stream")


@router.post("/api/speedtest/upload")
async def speedtest_upload(request: Request):
    # Just acknowledge receipt (timing is done on the client)
    await request.body()
    return {"status": "ok"}


# WebRTC Signaling Endpoints
@router.post("/api/webrtc/offer")
async def webrtc_offer(offer_request: WebRTCOffer):
    """
    Create a WebRTC offer for the remote control client.
    Server acts as the offerer, creating data channels for video streaming.
    """
    try:
        logger.info(f"WebRTC: Creating offer for {offer_request.remote_control_id}")
        offer = await s_controller.get_webrtc_offer(offer_request.remote_control_id)
        
        # Validate the offer
        if not offer or "error" in offer:
            error_msg = offer.get("error", "Unknown error") if offer else "No offer generated"
            logger.error(f"WebRTC: Failed to create offer for {offer_request.remote_control_id}: {error_msg}")
            return {
                "status": "error",
                "message": error_msg,
                "offer": None
            }
        
        # Verify offer has required fields
        if not offer.get("sdp") or not offer.get("type"):
            logger.error(f"WebRTC: Invalid offer for {offer_request.remote_control_id}: missing sdp or type")
            return {
                "status": "error",
                "message": "Invalid offer: missing sdp or type",
                "offer": None
            }
        
        return {
            "status": "success",
            "offer": offer
        }
    except Exception as e:
        logger.error(f"WebRTC: Exception creating offer for {offer_request.remote_control_id}: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e),
            "offer": None
        }

@router.post("/api/webrtc/answer")
async def webrtc_answer(answer_request: WebRTCAnswer):
    """
    Receive and process the WebRTC answer from the remote control client.
    """
    logger.info(f"WebRTC: Received answer from {answer_request.remote_control_id}")
    await s_controller.set_webrtc_answer(answer_request.remote_control_id, answer_request.sdp)
    return {
        "status": "success",
        "message": "Answer processed successfully"
    }

@router.post("/api/webrtc/ice-candidate")
async def webrtc_ice_candidate(ice_request: WebRTCIceCandidate):
    """
    Receive and add ICE candidate from the remote control client.
    """
    logger.debug(f"WebRTC: Received ICE candidate from {ice_request.remote_control_id}")
    await s_controller.add_webrtc_ice_candidate(ice_request.remote_control_id, ice_request.candidate)
    return {
        "status": "success",
        "message": "ICE candidate added successfully"
    }

class WebRTCIceRestart(BaseModel):
    remote_control_id: str
    offer: dict

@router.post("/api/webrtc/ice-restart")
async def webrtc_ice_restart(restart_request: WebRTCIceRestart):
    """
    Handle ICE restart from the remote control client.
    """
    logger.info(f"WebRTC: ICE restart requested from {restart_request.remote_control_id}")
    try:
        # Set the new offer with ICE restart
        from aiortc import RTCSessionDescription
        offer = RTCSessionDescription(
            sdp=restart_request.offer["sdp"],
            type=restart_request.offer["type"]
        )
        
        # Get the peer connection
        pc = s_controller.remote_control_manager.webrtc_manager.peer_connections.get(
            restart_request.remote_control_id
        )
        
        if not pc:
            return {
                "status": "error",
                "message": "Peer connection not found"
            }
        
        # Set remote description (the new offer with ICE restart)
        await pc.setRemoteDescription(offer)
        
        # Create answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        
        logger.info(f"WebRTC: ICE restart answer created for {restart_request.remote_control_id}")
        
        return {
            "status": "success",
            "answer": {
                "type": pc.localDescription.type,
                "sdp": pc.localDescription.sdp
            }
        }
    except Exception as e:
        logger.error(f"WebRTC: ICE restart failed for {restart_request.remote_control_id}: {e}")
        return {
            "status": "error",
            "message": str(e)
        }