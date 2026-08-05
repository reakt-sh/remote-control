import asyncio
import datetime
import threading
from app_logger import logger
from sensor.camera import Camera
from sensor.camera_rpi_5 import CameraRPi5
from motor_actuator import MotorActuator
from base_client import BaseClient
from globals import MOTOR_MODE, CONTROL_MODE, DIRECTION, IS_REAKTOR_DRIVER_ENABLED, ERROR_CODES
from PyQt5.QtCore import QThread
from sensor.rtsp_stream import RTSP_URL_FRONT, RTSP_URL_REAR, RTSPStream
import logging
import json
import struct


# Connector related imports
# from connector.test.context import Connection, Status, Control, Mode

from connector.connector.connection import Connection
from connector.connector.data import Status, Control, Mode


MAX_SPEED_REAKTOR = 6.0  # Maximum speed in m/s

class RPi5ReaktorClient(BaseClient, QThread):
    def __init__(self):
        super().__init__(video_source_front=RTSPStream(RTSP_URL_FRONT), video_source_rear=RTSPStream(RTSP_URL_REAR), has_motor=True)
        self.mode = Mode.FORWARD
        self.actual_mode = "UNKNOWN"
        self.speed = 0
        self.actual_speed_kmh = 0
        self.status = None
        self.last_log_time = 0
        self.connection = None
        logging.basicConfig(filename='reaktor_driver.log', encoding='utf-8', level=logging.INFO)

        if IS_REAKTOR_DRIVER_ENABLED:
            self.reaktor_driver_event = asyncio.new_event_loop()
            asyncio.set_event_loop(self.reaktor_driver_event)
            self.reaktor_driver_event.run_until_complete(self.setup_connection())

            self.reaktor_driver_thread = threading.Thread(target=self.reaktor_driver_event.run_forever, daemon=True)
            self.reaktor_driver_thread.start()

    async def setup_connection(self):
        logger.info("Setting up connection...")
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

        self.actual_speed_kmh = s.motor_speed * 3.6
        self.actual_mode = ""
        if s.mode == Mode.EMERGENCY_STOP:
            self.actual_mode = MOTOR_MODE.EMERGENCY_STOP
        elif s.mode == Mode.FORWARD:
            self.actual_mode = MOTOR_MODE.FORWARD
            self.telemetry.set_direction(DIRECTION.FORWARD)
        elif s.mode == Mode.REVERSE:
            self.actual_mode = MOTOR_MODE.REVERSE
            self.telemetry.set_direction(DIRECTION.BACKWARD)
        elif s.mode == Mode.PARKING:
            self.actual_mode = MOTOR_MODE.PARKING
        elif s.mode == Mode.NEUTRAL:
            self.actual_mode = MOTOR_MODE.NEUTRAL
        else:
            self.actual_mode = MOTOR_MODE.UNKNOWN

        self.telemetry.set_mode(self.actual_mode)
        self.telemetry.set_speed(self.actual_speed_kmh)

        if s.remote_control:
            self.telemetry.set_control_mode(CONTROL_MODE.REMOTE)
        else
            self.telemetry.set_control_mode(CONTROL_MODE.MANUAL)

    def update_speed(self, speed): # speed here in KM/H
        try:
            converted_speed = speed / 3.6 # convert to m/s

            if converted_speed > MAX_SPEED_REAKTOR:
                logger.warning(f"Requested speed {converted_speed} m/s exceeds MAX_SPEED {MAX_SPEED_REAKTOR} m/s. Capping to MAX_SPEED.")
                converted_speed = MAX_SPEED_REAKTOR

            self.speed = converted_speed

            control = Control(
                mode = self.mode,
                target_speed = self.speed
            )
            logger.info(f"Sending new target speed: {control.target_speed}")
            self.connection.send_control(control)
        except Exception as e:
            logger.error(f"Error updating speed: {e}")

    def on_power_on(self):
        try:
            # Start Command
            control = Control(
                mode = self.mode,
                target_speed = self.speed
            )
            logger.info(f"Powering on motor with target speed: {control.target_speed}")
            self.connection.send_control(control)
        except Exception as e:
            logger.error(f"Error powering ON motor: {e}")

    def on_power_off(self):
        # this is our stop command, we set the speed to 0 and send it to the motor
        try:
            # Stop Command
            self.speed = 0
            control = Control(
                mode = self.mode,
                target_speed = self.speed
            )
            logger.info("Stopping the REAKTOR")
            self.connection.send_control(control)
        except Exception as e:
            logger.error(f"Error Stopping motor: {e}")

    def on_change_direction(self, direction):
        # here we need a safety check,
        # if the train is moving, we should not allow changing direction
        if self.actual_speed_kmh > 0 and self.speed > 0:
            logger.warning("Cannot change direction while the train is moving. Please stop the train first.")
            super().send_error_message(ERROR_CODES.CHANGE_DIRECTION_WHILE_MOVING)
            return

        try:
            if direction == DIRECTION.FORWARD:
                self.mode = Mode.FORWARD
                self.speed = 0
            elif direction == DIRECTION.BACKWARD:
                self.mode = Mode.REVERSE
                self.speed = 0
            else:
                logger.warning(f"Unknown direction: {direction}")
                return

            control = Control(
                mode = self.mode,
                target_speed = self.speed
            )
            logger.info(f"Changing direction to: {self.mode}. Sending control: {control}")
            self.connection.send_control(control)
        except Exception as e:
            logger.error(f"Error changing direction: {e}")

    def on_horn_off(self):
        pass

    def on_headlight_off(self):
        pass

