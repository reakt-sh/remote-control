from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from server_controller import ServerController

s_controller = ServerController()

router = APIRouter()

@router.websocket("/ws/train/{train_id}")
async def train_interface(websocket: WebSocket, train_id: str):
    await s_controller.connect_train(train_id, websocket)
    try:
        while True:
            data = await websocket.receive_bytes()
            await s_controller.send_to_remote_control(data)
    except WebSocketDisconnect:
        await s_controller.disconnect_train(train_id)