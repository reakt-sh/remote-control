from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from server_controller import ServerController
s_controller = ServerController()
router = APIRouter()

@router.websocket("/ws/remote_control")
async def remote_control_interface(websocket: WebSocket):
    await websocket.accept()
    await s_controller.add_remote_controller(websocket)
    try:
        while True:
            command = await websocket.receive_json()
            s_controller.send_to_train(command)
    except WebSocketDisconnect:
        await s_controller.remove_remote_controller(websocket)
