from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from server_controller import ServerController
from utils.app_logger import logger
s_controller = ServerController()
router = APIRouter()

@router.websocket("/ws/remote_control/{remote_control_id}")
async def remote_control_interface(websocket: WebSocket, remote_control_id: str):
    logger.debug(f"Remote control connection established for web client:  {remote_control_id}")
    await websocket.accept()
    await s_controller.add_remote_controller(websocket, remote_control_id)
    try:
        while True:
            command = await websocket.receive_json()
            s_controller.send_to_train(command, remote_control_id)
    except WebSocketDisconnect:
        await s_controller.remove_remote_controller(remote_control_id)

@router.get("/api/trains")
async def get_trains():
    logger.debug("Fetching trains from server controller")
    data = s_controller.get_trains()
    logger.debug(f"Trains data: {data}")
    return {
        "trains": data
    }

@router.get("/stream/{train_id}")
async def get_stream(train_id: str):
    logger.debug(f"Fetching stream for train {train_id}")
    return ""