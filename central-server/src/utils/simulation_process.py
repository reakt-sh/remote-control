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

        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(__file__), '../../logs')
        os.makedirs(logs_dir, exist_ok=True)

        # Create log file path for subprocess
        subprocess_log_path = os.path.join(logs_dir, 'train_client_subprocess.log')

        try:
            # Redirect subprocess logs to a separate file
            with open(subprocess_log_path, 'a') as log_file:
                self.simulation_process = subprocess.Popen(
                    [python_executable, train_client_path, 'cli'],
                    stdout=log_file,
                    stderr=subprocess.STDOUT  # Redirect stderr to stdout (the log file)
                )
            logger.info(f"Spawned train client subprocess: {python_executable} {train_client_path} cli (logs redirected to {subprocess_log_path})")
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