import asyncio
import json
import struct
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from server_controller import ServerController
from utils.app_logger import logger
from utils.packet_builder import PacketBuilder
from globals import PACKET_TYPE

s_controller = ServerController()
packet_builder = PacketBuilder()
router = APIRouter()

@router.websocket("/ws/train/{train_id}")
async def train_interface(websocket: WebSocket, train_id: str):
    await websocket.accept()
    await s_controller.add_train(train_id, websocket)
    logger.debug(f"WebSocket: connection established for Train {train_id}")

    last_time = time.time()
    frame_counter = 0

    # Notify all the remote controllers about the new train connection
    packet = packet_builder.make_train_notification(train_id, "connected")
    await s_controller.notify_all_clients(packet)

    # inner function for keepalive task
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
                logger.debug(f"WebSocket: Sent keepalive packet to train {train_id}")
                await asyncio.sleep(25)  # Send keepalive every 5 seconds
            except Exception as e:
                logger.error(f"WebSocket: Error sending keepalive to train {train_id}: {e}")
                break

    # create a task for sending keepalive messages
    keepalive_task = asyncio.create_task(send_keepalive())

    try:
        while True:
            data = await websocket.receive_bytes()
            packet_type = data[0]
            payload = data[1:]

            if packet_type == PACKET_TYPE["video"] or packet_type == PACKET_TYPE["telemetry"]:
                logger.debug(f"WebSocket: Received packet type {packet_type} from train {train_id}, forwarding to clients")
                await s_controller.send_data_to_clients(train_id, data)
            elif packet_type == PACKET_TYPE["keepalive"]:
                message = json.loads(payload.decode('utf-8'))
                logger.debug(f"WebSocket: {message}")
            else:
                logger.debug(f"WebSocket: Received unknown packet type {packet_type} from train {train_id}")

            # calculate number of frames per seconds for video packets
            if packet_type == PACKET_TYPE["video"]:
                frame_counter += 1
                # difference of current frame_counter and frame_counter received 1 second ago
                if time.time() - last_time > 1:
                    fps = frame_counter / (time.time() - last_time)
                    logger.debug(f"WebSocket: FPS: {fps}")
                    frame_counter = 0
                    last_time = time.time()

    except WebSocketDisconnect:
        logger.debug(f"WebSocket: Train {train_id} disconnected.")
        # Notify all the remote controllers about the new train connection
        packet = packet_builder.make_train_notification(train_id, "disconnected")
        await s_controller.notify_all_clients(packet)
    except Exception as e:
        logger.error(f"WebSocket: Error in connection for train {train_id}: {e}")
    finally:
        # Ensure the WebSocket is properly closed and the train is disconnected
        keepalive_task.cancel()
        try:
            await keepalive_task
        except asyncio.CancelledError:
            pass

        await s_controller.remove_train(train_id)
