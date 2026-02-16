from sensor.camera_rpi_5 import CameraRPi5
from sensor.camera import Camera
from motor_actuator import MotorActuator
from base_client import BaseClient
from globals import DIRECTION, MAX_SPEED, TRAIN_STATUS
from PyQt5.QtCore import QThread
from utils.app_logger import logger

class RPi5Client(BaseClient, QThread):
    def __init__(self):
        super().__init__(video_source=CameraRPi5(), has_motor=True)
        self.motor_actuator = MotorActuator()
        self.motor_actuator.start_motor()
        self.target_speed = MAX_SPEED
        self.telemetry.set_speed(self.target_speed)
        logger.info("RPi5Client initialized.")

    def update_speed(self, speed):
        logger.info(f"Updating speed to: {speed}")
        self.motor_actuator.set_speed(speed)
        self.telemetry.set_speed(speed)

    def on_power_on(self):
        logger.info("Powering on the motor.")
        self.motor_actuator.start_motor()

    def on_power_off(self):
        logger.info("Powering off the motor.")
        self.motor_actuator.stop_motor()

    def on_change_direction(self, direction):
        logger.info(f"Changing direction to: {direction}")
        if direction == DIRECTION["FORWARD"]:
            self.motor_actuator.move_forward()
        elif direction == DIRECTION["BACKWARD"]:
            self.motor_actuator.move_backward()
        self.telemetry.set_status(TRAIN_STATUS["POWER_ON"])
