import subprocess
from utils.app_logger import logger

class Iperf3Process:
    def __init__(self):
        logger.debug("Iperf3Process initialized")
        self.process = None

    def create_process(self):
        try:
            self.process = subprocess.Popen(["iperf3", "-s", "-p", "5201"])
            logger.info("Spawned iperf3 server subprocess: iperf3 -s -p 5201")
        except Exception as e:
            logger.error(f"Failed to spawn iperf process: {e}")

    def destroy_process(self):
        if self.process is not None:
            try:
                self.process.kill()  # Forceful kill
                self.process.wait(timeout=5)
                logger.info("Killed iperf3 server subprocess")
            except Exception as e:
                logger.error(f"Failed to kill iperf3 subprocess: {e}")
            self.process = None