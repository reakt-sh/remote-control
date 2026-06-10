
import threading
from typing import Any
from telemetry import Telemetry


class AppContext:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> 'AppContext':
        if cls._instance is None:
            with cls._lock:
                # Double-check in case another thread created it while we waited
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize(*args, **kwargs)
        return cls._instance

    def _initialize(self, *args: Any, **kwargs: Any) -> None:
        self.train_client_id = None
        self.clock_offset_samples = {}
        self.clock_offsets = {}  # Clock offset between train and remote controls (ms)
        self.clock_offset_calculated = False
        self.connected_remote_control_ids = set()
        self.remote_control_client_id = None
        self.number_of_rtt_packets = 10

        self.latency_command_output_file = None
        self.frame_output_file = None
        self.latency_keepalive_output_file = None

        self.keepalive_sequence = 0  # Sequence number for keepalive packets

    def init_telemetry(self):
        self.telemetryObj = Telemetry(self.train_client_id)
        self.telemetryObj.start()