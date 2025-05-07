import threading
from typing import Any
from managers.train_manager import TrainManager
from managers.remote_control_manager import RemoteControlManager
from utils.app_logger import logger
class ServerController:
    """
    Thread-safe singleton implementation for managing server state and operations.
    Uses double-checked locking pattern for optimal performance.
    """
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
        """Initialize instance variables (called only once)"""
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
        """Example method with thread-safe operations"""
        with self._lock:
            if not self._running:
                self._running = True

    async def stop_server(self) -> None:
        """Example method to stop the server"""
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

    async def send_to_remote_control(self, data: bytes) -> None:
        # logger.debug(f"Sending data to remote control, data size: {len(data)}")
        if self.write_to_file:
            self.dump_file.write(data)
            self.dump_file.flush()
        # await self.remote_control_manager.broadcast_video(data)

    def get_trains(self) -> dict:
        return self.train_manager.get_trains()

    def map_client_to_train(self, remote_control_id: str, train_id: str) -> None:
        with self._lock:
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