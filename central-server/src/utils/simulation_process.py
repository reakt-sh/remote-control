import subprocess, os, sys
from utils.app_logger import logger

class SimulationProcess:
    def __init__(self):
        logger.debug("SimulationProcess initialized")
        self.simulation_process = None

    def create_simulation_process(self):
        # Build the command to run the CLI train client
        train_client_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../train-client/src/main.py'))
        python_executable = sys.executable
        try:
            # Suppress all logs from the subprocess by redirecting stdout and stderr to DEVNULL
            self.simulation_process = subprocess.Popen(
                [python_executable, train_client_path, 'cli'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.info(f"Spawned train client subprocess: {python_executable} {train_client_path} cli (logs suppressed)")
        except Exception as e:
            logger.error(f"Failed to spawn train client subprocess: {e}")

    def destroy_simulation_process(self):
        if self.simulation_process is not None:
            try:
                self.simulation_process.kill()  # Forceful kill
                self.simulation_process.wait(timeout=5)
                logger.info("Killed train client subprocess")
            except Exception as e:
                logger.error(f"Failed to kill train sim subprocess: {e}")
            self.simulation_process = None