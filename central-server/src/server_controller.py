import threading
from typing import Any

from managers.train_manager import TrainManager
from managers.remote_control_manager import RemoteControlManager
from utils.app_logger import logger
class ServerController:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> 'ServerController':
        if cls._instance is None:
            with cls._lock:
                # Double-check in case another thread created it while we waited
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize(*args, **kwargs)
        return cls._instance

    def _initialize(self, *args: Any, **kwargs: Any) -> None:
        self._running = False
        self._clients = {}
        self._lock = threading.RLock()  # For instance-level thread safety

        self.train_manager = TrainManager()
        self.remote_control_manager = RemoteControlManager()
        self.write_to_file = True
        self.dump_file = open("dump.h264", 'wb')
        self.train_to_clients_map = {}
        self.client_to_train_map = {}

    def start_server(self) -> None:
        with self._lock:
            if not self._running:
                self._running = True

    async def stop_server(self) -> None:
        with self._lock:
            if self._running:
                # Clean up resources
                await self.train_manager.disconnect_all()
                await self.remote_control_manager.disconnect_all()
                del self.train_manager
                del self.remote_control_manager
                self._running = False

    async def add_remote_controller(self, websocket: Any, remote_control_id: str) -> None:
        await self.remote_control_manager.add(websocket, remote_control_id)

    async def remove_remote_controller(self,remote_control_id: str) -> None:
        await self.remote_control_manager.remove(remote_control_id)

    async def send_to_train(self, command: dict) -> None:
            train_id = command.get("train_id")
            if train_id in self.train_manager.active_connections:
                await self.train_manager.active_connections[train_id].send_json(command)

    async def add_train(self, train_id: str, websocket: Any) -> None:
        await self.train_manager.add(train_id, websocket)

    async def remove_train(self, train_id: str) -> None:
        await self.train_manager.remove(train_id)

    def get_trains(self) -> dict:
        return self.train_manager.get_trains()

    def map_client_to_train(self, remote_control_id: str, train_id: str) -> None:
        with self._lock:
            # remove existing mapping if it exists
            if remote_control_id in self.client_to_train_map:
                existing_train_id = self.client_to_train_map[remote_control_id]
                if existing_train_id != train_id:
                    self.train_to_clients_map[existing_train_id].discard(remote_control_id)
                    if not self.train_to_clients_map[existing_train_id]:
                        del self.train_to_clients_map[existing_train_id]
                        logger.debug(f"Removed empty entry for train {existing_train_id} from train_to_clients_map")

            # add new mapping
            self.client_to_train_map[remote_control_id] = train_id
            logger.debug(f"Mapped {remote_control_id} to {train_id}")

            if train_id not in self.train_to_clients_map:
                self.train_to_clients_map[train_id] = set()

            self.train_to_clients_map[train_id].add(remote_control_id)
            logger.debug(f"Updated train_to_clients_map: {self.train_to_clients_map}")

    def unmap_client_from_train(self, remote_control_id: str) -> None:
        with self._lock:
            if remote_control_id in self.client_to_train_map:
                train_id = self.client_to_train_map.pop(remote_control_id)
                logger.debug(f"Unmapped {remote_control_id} from {train_id}")

                if train_id in self.train_to_clients_map:
                    self.train_to_clients_map[train_id].discard(remote_control_id)
                    logger.debug(f"Updated train_to_clients_map: {self.train_to_clients_map}")
                    if not self.train_to_clients_map[train_id]:
                        del self.train_to_clients_map[train_id]
                        logger.debug(f"Removed empty entry for train {train_id} from train_to_clients_map")
                else:
                    logger.warning(f"Train ID {train_id} not found in train_to_clients_map")
            else:
                logger.warning(f"Remote control ID {remote_control_id} not found in client_to_train_map")

    def get_remote_control_ids_by_train(self, train_id: str) -> list:
        with self._lock:
            return list(self.train_to_clients_map.get(train_id, []))

    def get_train_id_by_remote_control(self, remote_control_id: str) -> str:
        with self._lock:
            return self.client_to_train_map.get(remote_control_id, "")

    async def send_data_to_clients(self, train_id: str, data: bytes) -> None:
        if train_id in self.train_to_clients_map:
            remote_control_ids = self.train_to_clients_map[train_id]
            for remote_control_id in remote_control_ids:
                # Send via WebSocket if connected
                if remote_control_id in self.remote_control_manager.active_connections:
                    websocket = self.remote_control_manager.active_connections[remote_control_id]
                    await websocket.send_bytes(data)
                
                # Also send via WebRTC if video data
                packet_type = data[0] if len(data) > 0 else None
                if packet_type == 13:  # video packet type
                    await self.remote_control_manager.send_video_via_webrtc(remote_control_id, data)

    async def send_data_to_train(self, remote_control_id: str, data: bytes) -> None:
        train_id = self.client_to_train_map.get(remote_control_id)
        logger.debug(f"train_id fond = {train_id}")
        if train_id and train_id in self.train_manager.active_connections:
            logger.debug(f"websocket connection also found for {train_id}")
            websocket = self.train_manager.active_connections[train_id]
            await websocket.send_bytes(data)

    async def notify_all_clients(self, data: bytes) -> None:
        logger.debug(f"Sending notification to all clients, active_connections size: {len(self.remote_control_manager.active_connections)}")
        for remote_control_id in self.remote_control_manager.active_connections:
            websocket = self.remote_control_manager.active_connections[remote_control_id]
            logger.debug(f"Sending notification to {remote_control_id}")
            await websocket.send_bytes(data)

    async def get_webrtc_offer(self, remote_control_id: str) -> dict:
        """Get WebRTC offer for remote control client"""
        return await self.remote_control_manager.get_webrtc_offer(remote_control_id)

    async def set_webrtc_answer(self, remote_control_id: str, answer: dict):
        """Set WebRTC answer from remote control client"""
        await self.remote_control_manager.set_webrtc_answer(remote_control_id, answer)

    async def add_webrtc_ice_candidate(self, remote_control_id: str, candidate: dict):
        """Add WebRTC ICE candidate from remote control client"""
        await self.remote_control_manager.add_webrtc_ice_candidate(remote_control_id, candidate)