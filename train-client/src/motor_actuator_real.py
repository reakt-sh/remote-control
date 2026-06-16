import asyncio
import datetime
import qasync
from app_logger import logger
from globals import DIRECTION, IS_REAKTOR_DRIVER_ENABLED
from app_context import AppContext

# Connector related imports
from connector.test.context import Connection, Status, Control, Mode

INITIAL_SPEED_REAKTOR = 3.0  # Initial speed in m/s
MAX_SPEED_REAKTOR = 6.0  # Maximum speed in m/s

class MotorActuator():
    def __init__(self):
        self.appcontext = AppContext()
        self.current_mode = Mode.FORWARD
        self.current_speed = 0
        self.status = None
        self.last_log_time = 0

        if IS_REAKTOR_DRIVER_ENABLED:
            loop = qasync.QEventLoop()
            logger.info("Reaktor driver enabled. Initializing connection.")
            self.connection = None
            task = loop.create_task(self.setup_connection())
            loop.run_until_complete(task)

    async def setup_connection(self):
        logger.info("Setting up connection...")
        # logging.basicConfig(level=logging.DEBUG)
        # Open connection
        self.connection = Connection()
        self.connection.add_status_listener(lambda x: self.set_status(x))
        await self.connection.open("/dev/ttyUSB0")

        # Test if connection is ready
        if not self.connection.is_ready():
            logger.warning("Warning: Connection not yet ready. Check connection.")
        while not self.status:
            logger.warning("Waiting for initial status...")
            await asyncio.sleep(.1)

    def set_status(self, s: Status):
        self.status = s
        current_time = datetime.datetime.now().timestamp() * 1000
        if current_time - self.last_log_time > 3000:
            self.last_log_time = current_time
            logger.info(f"New status: {s}")

        current_speed_kmh = s.motor_speed * 3.6
        current_mode = ""
        if s.mode == Mode.EMERGENCY_STOP:
            current_mode = "STOP"
        elif s.mode == Mode.FORWARD:
            current_mode = "FORWARD"
        elif s.mode == Mode.REVERSE:
            current_mode = "REVERSE"
        elif s.mode == Mode.PARKING:
            current_mode = "PARKING"
        elif s.mode == Mode.NEUTRAL:
            current_mode = "NEUTRAL"
        else:
            current_mode = "UNKNOWN"

        self.appcontext.telemetryObj.set_speed(current_speed_kmh)
        self.appcontext.telemetryObj.set_mode(current_mode)
        

    def set_speed(self, speed): # speed here in KM/H
        try:
            converted_speed = speed / 3.6 # convert to m/s

            if converted_speed > MAX_SPEED_REAKTOR:
                logger.warning(f"Requested speed {converted_speed} m/s exceeds MAX_SPEED {MAX_SPEED_REAKTOR} m/s. Capping to MAX_SPEED.")
                converted_speed = MAX_SPEED_REAKTOR

            self.current_speed = converted_speed

            control = Control(
                mode = self.current_mode,
                target_speed = self.current_speed
            )
            logger.info(f"Sending new target speed: {control.target_speed}")
            self.connection.send_control(control)
        except Exception as e:
            logger.error(f"Error updating speed: {e}")

    def start_motor(self):
        try:
            # Start Command
            control = Control(
                mode = self.current_mode,
                target_speed = self.current_speed
            )
            logger.info(f"Powering on motor with target speed: {control.target_speed}")
            self.connection.send_control(control)
        except Exception as e:
            logger.error(f"Error powering ON motor: {e}")

    def stop_motor(self):
        try:
            # Stop Command
            control = Control(
                mode = self.current_mode,
                target_speed = 0
            )
            logger.info("Powering off motor.")
            self.connection.send_control(control)
        except Exception as e:
            logger.error(f"Error powering OFF motor: {e}")

    def set_direction(self, direction):
        try:
            if direction == DIRECTION["FORWARD"]:
                self.current_mode = Mode.FORWARD
                logger.info("Changing direction command received to FORWARD.")
            elif direction == DIRECTION["BACKWARD"]:
                self.current_mode = Mode.REVERSE
                logger.info("Changing direction command received to BACKWARD.")
        except Exception as e:
            logger.error(f"Error changing direction: {e}")
