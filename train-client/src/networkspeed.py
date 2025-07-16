import subprocess
import json
from typing import Dict, Optional, Tuple
from PyQt5.QtCore import pyqtSignal, QThread, QTimer
from loguru import logger
from globals import SERVER
import asyncio

class NetworkSpeed(QThread):
    speed_calculated = pyqtSignal(float, float)  # Fixed typo in signal name
    def __init__(self, server_host: str = SERVER, port: int = 5201, duration: int = 10):
        super().__init__()
        self.server_host = server_host
        self.port = port
        self.duration = duration
        self.loop = asyncio.new_event_loop()
        self.start()
        logger.debug(f"NetworkSpeedTester initialized for server {server_host}:{port}")

    def _run_iperf_test(self, reverse: bool = False) -> Optional[Dict]:
        cmd = [
            "iperf3",
            "-c", self.server_host,
            "-p", str(self.port),
            "-t", str(self.duration),
            "-J",
            "--forceflush",
        ]
        if reverse:
            cmd.append("-R")

        try:
            logger.info(f"Starting iperf3 test: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"iperf3 test failed: {e.stderr.strip()}")
        except json.JSONDecodeError:
            logger.error("Failed to parse iperf3 JSON output")
        except Exception as e:
            logger.error(f"Unexpected error during iperf3 test: {str(e)}")
        return None

    def run(self):
        self.measure_speeds()

    def measure_speeds(self):
        """Synchronous wrapper for the speed test"""
        download = self._run_iperf_test(reverse=False)
        upload = self._run_iperf_test(reverse=True)
        download_speed = download['end']['sum_received']['bits_per_second'] / 1e6 if download else None
        upload_speed = upload['end']['sum_sent']['bits_per_second'] / 1e6 if upload else None
        self.speed_calculated.emit(download_speed, upload_speed)
