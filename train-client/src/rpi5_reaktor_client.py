import asyncio
import qasync
from loguru import logger
from sensor.camera import Camera
from motor_actuator import MotorActuator
from base_client import BaseClient
from globals import DIRECTION
from PyQt5.QtCore import QThread

# Connector related imports
from connector.test.context import Connection, Status, Control, Mode

INITIAL_SPEED_REAKTOR = 3.0  # Initial speed in m/s
MAX_SPEED_REAKTOR = 6.0  # Maximum speed in m/s

# Status handling
status = None
def set_status(s: Status):
    global status
    status = s
    # logger.info(f"New status: {s}")


class RPi5ReaktorClient(BaseClient, QThread):
    def __init__(self):
        super().__init__(video_source=Camera(), has_motor=True)
        self.connection = None
        self.setup_task = None
        loop = qasync.QEventLoop(self)
        self.current_mode = Mode.FORWARD
        self.current_speed = 0
        task = loop.create_task(self.setup_connection())
        loop.run_until_complete(task)

    async def setup_connection(self):
        logger.info("Setting up connection...")
        # Open connection
        self.connection = Connection()
        self.connection.add_status_listener(set_status)
        await self.connection.open("/dev/ttyUSB0")

        # Test if connection is ready
        if not self.connection.is_ready():
            logger.warning("Warning: Connection not yet ready. Check connection.")
        while not status:
            logger.warning("Waiting for initial status...")
            await asyncio.sleep(.1)

    def update_speed(self, speed): # speed here in KM/H

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

    def on_power_on(self):
        # Start Command
        control = Control(
            mode = self.current_mode,
            target_speed = self.current_speed
        )
        logger.info(f"Powering on motor with target speed: {control.target_speed}")
        self.connection.send_control(control)

    def on_power_off(self):
        # Stop Command
        control = Control(
            mode = self.current_mode,
            target_speed = 0
        )
        logger.info("Powering off motor.")
        self.connection.send_control(control)

    def on_change_direction(self, direction):
        if direction == DIRECTION["FORWARD"]:
            self.current_mode = Mode.FORWARD
            logger.info("Changing direction command received to FORWARD.")
        elif direction == DIRECTION["BACKWARD"]:
            self.current_mode = Mode.REVERSE
            logger.info("Changing direction command received to BACKWARD.")
