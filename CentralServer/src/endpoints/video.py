from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from managers.train_manager import TrainManager
from managers.control_manager import ControlManager

train_manager = TrainManager()
control_manager = ControlManager()

router = APIRouter()

@router.websocket("/ws/train/{train_id}")
async def train_video_feed(websocket: WebSocket, train_id: str):
    await train_manager.connect(train_id, websocket)
    try:
        while True:
            data = await websocket.receive_bytes()
            # Forward to all control clients
            await control_manager.broadcast_video(data)
    except WebSocketDisconnect:
        await train_manager.disconnect(train_id)