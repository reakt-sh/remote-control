import asyncio
import json
import struct
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
    async def send_keepalive():
        keepalive_sequence = 0
        while True:
            try:
                keepalive_sequence += 1
                keepalive_packet = {
                    "type": "keepalive",
                    "timestamp": asyncio.get_event_loop().time(),
                    "sequence": keepalive_sequence
                }
                packet_data = json.dumps(keepalive_packet).encode('utf-8')
                packet = struct.pack("B", PACKET_TYPE["keepalive"]) + packet_data
                await websocket.send_bytes(packet)
                logger.debug(f"Sent keepalive packet to train {train_id}")
                await asyncio.sleep(3)  # Send keepalive every 5 seconds
            except Exception as e:
                logger.error(f"Error sending keepalive to train {train_id}: {e}")
                break
    # Start the keepalive task
    keepalive_task = asyncio.create_task(send_keepalive())

    try:
        while True:
            data = await websocket.receive_bytes()
            packet_type = data[0]
            payload = data[1:]

            if packet_type == PACKET_TYPE["video"]:
                await s_controller.send_to_remote_control(payload)
            elif packet_type == PACKET_TYPE["keepalive"]:
                message = json.loads(payload.decode('utf-8'))
                logger.debug(f"{message}")
            else:
                logger.debug(f"Received unknown packet type {packet_type} from train {train_id}")
    except WebSocketDisconnect:
        logger.debug(f"Train {train_id} disconnected.")
    except Exception as e:
        logger.error(f"Error in WebSocket connection for train {train_id}: {e}")
    finally:
        # Ensure the WebSocket is properly closed and the train is disconnected
        keepalive_task.cancel()
        try:
            await keepalive_task
        except asyncio.CancelledError:
            pass

        await s_controller.remove_train(train_id)
