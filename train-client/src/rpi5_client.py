from sensor.camera_rpi_5 import CameraRPi5
from motor_actuator import MotorActuator
from base_client import BaseClient
from globals import DIRECTION
from PyQt5.QtCore import QThread
class RPi5Client(BaseClient, QThread):
    def __init__(self):
        super().__init__(video_source=CameraRPi5(), has_motor=True)
        self.motor_actuator = MotorActuator()
        self.motor_actuator.start_motor()
        self.target_speed = 20
        self.telemetry.set_speed(self.target_speed)

    def update_speed(self, speed):
        self.motor_actuator.set_speed(speed)
        self.telemetry.set_speed(speed)

    def on_power_on(self):
        self.motor_actuator.start_motor()
        self.update_speed(self.target_speed)

    def on_power_off(self):
        self.motor_actuator.stop_motor()
        self.update_speed(0)

    def on_change_direction(self, direction):
        if direction == DIRECTION["FORWARD"]:
            self.motor_actuator.move_forward()
        elif direction == DIRECTION["BACKWARD"]:
            self.motor_actuator.move_backward()
        self.update_speed(self.motor_actuator.get_speed())