from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from server_controller import ServerController
from utils.app_logger import logger
s_controller = ServerController()
router = APIRouter()

@router.websocket("/ws/remote_control/{train_id}")
async def remote_control_interface(websocket: WebSocket, train_id: str):
    logger.debug(f"Remote control connection established for train {train_id}")
    await websocket.accept()
    await s_controller.add_remote_controller(websocket)
    try:
        while True:
            command = await websocket.receive_json()
            s_controller.send_to_train(command)
    except WebSocketDisconnect:
        await s_controller.remove_remote_controller(websocket)

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