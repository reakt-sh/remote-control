import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.server_controller import ServerController
from src.utils.app_logger import logger
from src.globals import PACKET_TYPE


s_controller = ServerController()
router = APIRouter()

@router.websocket("/ws/remote_control/{remote_control_id}")
async def remote_control_interface(websocket: WebSocket, remote_control_id: str):
    logger.debug(f"WebSocket: connection established for web client:  {remote_control_id}")
    await websocket.accept()
    await s_controller.add_remote_controller(websocket, remote_control_id)
    try:
        while True:
            data = await websocket.receive_bytes()
            await s_controller.send_data_to_train(remote_control_id, data)
            packet_type = data[0]
            payload = data[1:]
            if packet_type == PACKET_TYPE["command"]:
                message = json.loads(payload.decode('utf-8'))
                train_id = message['train_id']
                logger.debug(f"WebSocket: {train_id} : {message}")
            else:
                logger.debug("WebSocket: Unknown message type")
            #s_controller.send_to_train(command, remote_control_id)
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