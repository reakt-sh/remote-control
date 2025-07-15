import subprocess
import json
from typing import Dict, Optional, Tuple
from loguru import logger  # Assuming you have this logger setup
from globals import SERVER

class NetworkSpeed:
    def __init__(self, server_host: str = SERVER, port: int = 5201, duration: int = 10):
        self.server_host = server_host
        self.port = port
        self.duration = duration
        logger.debug(f"NetworkSpeedTester initialized for server {server_host}:{port}")

    def _run_iperf_test(self, reverse: bool = False) -> Optional[Dict]:
        cmd = [
            "iperf3",
            "-c", self.server_host,
            "-p", str(self.port),
            "-t", str(self.duration),
            "-J",  # JSON output
            "--forceflush",  # Ensure timely output
        ]

        if reverse:
            cmd.append("-R")  # Reverse mode for upload test

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

    def measure_speeds(self) -> Tuple[Optional[float], Optional[float]]:
        download = self._run_iperf_test(reverse=False)
        upload = self._run_iperf_test(reverse=True)
        download_speed = download['end']['sum_received']['bits_per_second'] / 1e6 if download else None
        upload_speed = upload['end']['sum_sent']['bits_per_second'] / 1e6 if upload else None
        logger.info(
            f"Speed test results - Download: {download_speed:.2f} Mbps, "
            f"Upload: {upload_speed:.2f} Mbps"
        )
        return download_speed, upload_speed


# Example usage
if __name__ == "__main__":
    
    
    if download is not None and upload is not None:
        print(f"Download: {download:.2f} Mbps | Upload: {upload:.2f} Mbps")
    else:
        print("Speed test failed")