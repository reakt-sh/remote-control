from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from managers.train_manager import TrainManager
from managers.remote_control_manager import RemoteControlManager

train_manager = TrainManager()
remote_control_manager = RemoteControlManager()
router = APIRouter()

@router.websocket("/ws/train/{train_id}")
async def train_video_feed(websocket: WebSocket, train_id: str):
    await train_manager.connect(train_id, websocket)
    try:
        while True:
            data = await websocket.receive_bytes()
            # Forward to all control clients
            await remote_control_manager.broadcast_video(data)
    except WebSocketDisconnect:
        await train_manager.disconnect(train_id)