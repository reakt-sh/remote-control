import threading
from typing import Any

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
        # Add your initialization code here

    def start_server(self) -> None:
        """Example method with thread-safe operations"""
        with self._lock:
            if not self._running:
                self._running = True
                # Actual server start logic here

    def register_client(self, client_id: str, client_info: dict) -> None:
        with self._lock:
            self._clients[client_id] = client_info

    # Add other server management methods...