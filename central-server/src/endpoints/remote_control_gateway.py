from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from server_controller import ServerController
s_controller = ServerController()
router = APIRouter()

@router.websocket("/ws/remote_control")
async def remote_control_interface(websocket: WebSocket):
    await s_controller.connect_remote_controller(websocket)
    try:
        while True:
            command = await websocket.receive_json()
            s_controller.send_to_train(command)
    except WebSocketDisconnect:
        await s_controller.disconnect_remote_controller(websocket)