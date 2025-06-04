import asyncio
from src.utils.app_logger import logger

class Calculator:
    def __init__(self):
        self.bandwidth_start_time = None
        self.bandwidth_bytes = 0

    def calculate_bandwidth(self, bytes_received: int):
        now = asyncio.get_event_loop().time()
        if self.bandwidth_start_time is None:
            self.bandwidth_start_time = now
            self.bandwidth_bytes = 0

        self.bandwidth_bytes += bytes_received

        if now - self.bandwidth_start_time >= 1.0:
            logger.debug(f"Current Bandwidth for Video Transmission:  {self.bandwidth_bytes / 1024:.2f} KB/s")
            self.bandwidth_start_time = now
            self.bandwidth_bytes = 0