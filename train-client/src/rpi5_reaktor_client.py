import asyncio
import logging
from sensor.camera_rpi_5 import CameraRPi5
from motor_actuator import MotorActuator
from base_client import BaseClient
from globals import DIRECTION
from PyQt5.QtCore import QThread

# Connector related imports
from connector.test.context import Connection, Status, Control, Mode

TARGET_SPEED = 1000  # Target speed in RPM

# Status handling
status = None
def set_status(s: Status):
    global status
    status = s
    logging.info("New status: %s", s)


class RPi5ReaktorClient(BaseClient, QThread):
    def __init__(self):
        super().__init__(video_source=CameraRPi5(), has_motor=True)
        asyncio.create_task(self.setup_connection())

    async def setup_connection(self):
        # Open connection
        self.connection = Connection()
        self.connection.add_status_listener(set_status)
        await self.connection.open("/dev/ttyUSB0")

        # Test if connection is ready
        if not self.connection.is_ready():
            print("Warning: Connection not yet ready. Check connection.")
        while not status:
            print("Waiting for initial status...")
            await asyncio.sleep(.1)

    def update_speed(self, speed):
        # Set speed
        control = Control(
            mode = Mode.FORWARD,
            target_rpm = speed
        )
        logging.info("Sending new RPM: %d", control.target_rpm)
        self.connection.send_control(control)

    def on_power_on(self):
        # Set initial speed
        control = Control(
            mode = Mode.FORWARD,
            target_rpm = TARGET_SPEED
        )
        logging.info("Powering on motor with RPM: %d", control.target_rpm)
        self.connection.send_control(control)

    def on_power_off(self):
        # Stop motor
        control = Control(
            mode = Mode.NEUTRAL,
            target_rpm = 0
        )
        logging.info("Powering off motor.")
        self.connection.send_control(control)

    def on_change_direction(self, direction):
        if direction == DIRECTION["FORWARD"]:
            logging.info("Changing direction command received to FORWARD.")
        elif direction == DIRECTION["BACKWARD"]:
            logging.info("Changing direction command received to BACKWARD.")
