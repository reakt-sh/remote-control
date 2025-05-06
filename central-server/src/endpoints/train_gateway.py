from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from server_controller import ServerController
from utils.app_logger import logger

s_controller = ServerController()
# Packet Types
PACKET_TYPE = {
    "video": 13,
    "audio": 14,
    "control": 15,
    "command": 16,
    "telemetry": 17,
    "imu": 18,
    "lidar": 19,
    "keepalive": 20
}

router = APIRouter()

@router.websocket("/ws/train/{train_id}")
async def train_interface(websocket: WebSocket, train_id: str):
    await websocket.accept()
    await s_controller.add_train(train_id, websocket)
    logger.debug(f"For Train {train_id}, websocket connection established")
    try:
        while True:
            data = await websocket.receive_bytes()
            logger.debug(f"Received data from train {train_id}, {data[0]}")
            if data[0] == PACKET_TYPE["video"]:
                await s_controller.send_to_remote_control(data[1:])
            elif data[0] == PACKET_TYPE["keepalive"]:
                logger.debug(f"Keepalive packet received from train {train_id}, {data}")
    except WebSocketDisconnect:
        logger.debug(f"Train {train_id} disconnected.")
    except Exception as e:
        logger.error(f"Error in WebSocket connection for train {train_id}: {e}")
    finally:
        # Ensure the WebSocket is properly closed and the train is disconnected
        await s_controller.remove_train(train_id)
