from utils.app_logger import logger
import asyncio
from typing import Dict, Set
from aioquic.asyncio.protocol import QuicConnectionProtocol
import json
import struct
from globals import PACKET_TYPE

class ClientManager:
    def __init__(self):
        self.train_clients: Dict[str, QuicConnectionProtocol] = {}
        self.remote_control_clients: Dict[str, QuicConnectionProtocol] = {}

        self.train_to_remote_controls_map: Dict[str, Set[str]] = {}
        self.remote_control_to_train_map: Dict[str, str] = {}
        self.packet_queue: asyncio.Queue = asyncio.Queue()
        asyncio.create_task(self.relay_datagram_to_remote_controls())
        self.lock = asyncio.Lock()

    async def enqueue_video_packet(self, train_id: str, data: bytes):
        await self.packet_queue.put((train_id, data))

    async def add_train_client(self, train_id: str, protocol: QuicConnectionProtocol):
        async with self.lock:
            self.train_clients[train_id] = protocol
            logger.info(f"QUIC: Train client connected: {train_id}, Trains: {self.train_clients.keys()}")

    async def remove_train_client(self, train_id: str):
        async with self.lock:
            # first remove mapping from remote controls connected to this train
            if train_id in self.train_to_remote_controls_map:
                remote_control_ids = self.train_to_remote_controls_map[train_id]
                for remote_control_id in remote_control_ids:
                    self.remote_control_to_train_map.pop(remote_control_id, None)
                del self.train_to_remote_controls_map[train_id]

            # then remove the train client
            if train_id in self.train_clients:
                del self.train_clients[train_id]
                logger.info(f"QUIC: Train client disconnected: {train_id}")

    async def add_remote_control_client(self, remote_control_id: str, protocol: QuicConnectionProtocol):
        async with self.lock:
            self.remote_control_clients[remote_control_id] = protocol
            logger.info(f"QUIC: Remote Control client connected {remote_control_id}, Remote Controls: {self.remote_control_clients.keys()}")

    async def remove_remote_control_client(self, remote_control_id: str):
        async with self.lock:
            # Remove mapping if it exists
            if remote_control_id in self.remote_control_to_train_map:
                train_id = self.remote_control_to_train_map.pop(remote_control_id)
                if train_id in self.train_to_remote_controls_map:
                    self.train_to_remote_controls_map[train_id].discard(remote_control_id)
                    if not self.train_to_remote_controls_map[train_id]:
                        del self.train_to_remote_controls_map[train_id]
                        logger.debug(f"Removed empty entry for train {train_id} from train_to_remote_controls_map")

            if remote_control_id in self.remote_control_clients:
                del self.remote_control_clients[remote_control_id]
                logger.info(f"QUIC: Remote Control client disconnected: {remote_control_id}")

    async def connect_remote_control_to_train(self, remote_control_id: str, train_id: str):
        async with self.lock:
            # Check if the remote control is already mapped to a train
            if remote_control_id in self.remote_control_to_train_map:
                existing_train_id = self.remote_control_to_train_map[remote_control_id]
                if existing_train_id != train_id:
                    # Unmap from the existing train
                    if existing_train_id in self.train_to_remote_controls_map:
                        self.train_to_remote_controls_map[existing_train_id].discard(remote_control_id)
                        if not self.train_to_remote_controls_map[existing_train_id]:
                            del self.train_to_remote_controls_map[existing_train_id]
                            logger.debug(f"QUIC: Removed empty entry for train {existing_train_id} from train_to_remote_controls_map")

                            # send instruction to train, stop sending any more data
                            protocol = self.train_clients.get(existing_train_id)
                            if protocol:
                                try:
                                    instruction_packet = {
                                        "type": "command",
                                        "instruction": "STOP_SENDING_DATA",
                                    }
                                    packet_data = json.dumps(instruction_packet).encode('utf-8')
                                    packet = struct.pack("B", PACKET_TYPE["command"]) + packet_data
                                    protocol._quic.send_stream_data(protocol.stream_id, packet, end_stream=False)
                                    protocol.transmit()
                                    logger.info(f"Sent STOP_STREAM to train {existing_train_id} for remote control {remote_control_id}")
                                except Exception as e:
                                    logger.error(f"Failed to send STOP_STREAM to train {existing_train_id}: {e}")

            logger.debug(f"QUIC: Mapping remote control {remote_control_id} to train {train_id}")

            # Map the remote control to the new train
            self.remote_control_to_train_map[remote_control_id] = train_id
            if train_id not in self.train_to_remote_controls_map:
                self.train_to_remote_controls_map[train_id] = set()
            self.train_to_remote_controls_map[train_id].add(remote_control_id)
            logger.info(f"QUIC: Updated train_to_remote_controls_map: {self.train_to_remote_controls_map}")

            # Send instruction to the remote control to start sending data
            protocol = self.train_clients.get(train_id)
            if protocol:
                try:
                    instruction_packet = {
                        "type": "command",
                        "instruction": "START_SENDING_DATA",
                    }
                    packet_data = json.dumps(instruction_packet).encode('utf-8')
                    packet = struct.pack("B", PACKET_TYPE["command"]) + packet_data
                    protocol._quic.send_stream_data(protocol.stream_id, packet, end_stream=False)
                    protocol.transmit()
                    logger.info(f"QUIC: Sending instruction START_SENDING_DATA to train {train_id}")
                except Exception as e:
                    logger.error(f"Failed to send START_STREAM to train {train_id}: {e}")

    async def relay_datagram_to_remote_controls(self):
        while True:
            try:
                train_id, data = await self.packet_queue.get()
                remote_controls = self.train_to_remote_controls_map.get(train_id, set())
                for remote_control_id in remote_controls:
                    protocol = self.remote_control_clients.get(remote_control_id)
                    if protocol:
                        try:
                            protocol.h3_connection.send_datagram(protocol.session_id, data)
                            protocol.transmit()
                        except Exception as e:
                            logger.error(f"Failed to relay video to remote_control {remote_control_id}: {e}")
            except self.packet_queue.Empty:
                await asyncio.sleep(0.1)

    async def relay_stream_to_remote_controls(self, train_id: str, data: bytes):
        remote_controls = self.train_to_remote_controls_map.get(train_id, set())
        for remote_control_id in remote_controls:
            protocol = self.remote_control_clients.get(remote_control_id)
            if protocol:
                try:
                    protocol._quic.send_stream_data(protocol.stream_id, data, end_stream=False)
                    protocol.transmit()
                except Exception as e:
                    logger.error(f"Failed to relay video to remote_control {remote_control_id}: {e}")

    async def relay_stream_to_train(self, remote_control_id: str, data: bytes):
        train_id = self.remote_control_to_train_map.get(remote_control_id)
        if train_id:
            protocol = self.train_clients.get(train_id)
            if protocol:
                try:
                    protocol._quic.send_stream_data(protocol.stream_id, data, end_stream=False)
                    protocol.transmit()
                    logger.info(f"Relayed stream data(Reliable) to train {train_id} from remote_control {remote_control_id}")
                except Exception as e:
                    logger.error(f"Failed to relay stream to train {train_id}: {e}")
        else:
            logger.warning(f"No train found for remote control {remote_control_id}")