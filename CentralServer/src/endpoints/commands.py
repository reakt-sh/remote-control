from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from managers.control_manager import ControlManager
from managers.train_manager import TrainManager

control_manager = ControlManager()
train_manager = TrainManager()
router = APIRouter()

@router.websocket("/ws/control")
async def control_interface(websocket: WebSocket):
    await control_manager.connect(websocket)
    try:
        while True:
            command = await websocket.receive_json()
            # Forward command to target train
            train_id = command.get("train_id")
            if train_id in train_manager.active_connections:
                await train_manager.active_connections[train_id].send_json(command)
    except WebSocketDisconnect:
        await control_manager.disconnect(websocket)