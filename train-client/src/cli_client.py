from sensor.file_processor import FileProcessor
from PyQt5.QtCore import QThread
from base_client import BaseClient
from globals import LOW_BITRATE
class CLIClient(BaseClient, QThread):
    def __init__(self):
        super().__init__(video_source=FileProcessor(), has_motor=False)
        self.encoder.set_bitrate(LOW_BITRATE) # Set initial bitrate to 1Mbps

    def update_speed(self, speed):
        self.video_source.set_speed(speed)
        self.telemetry.set_speed(speed)

    def on_power_on(self):
        self.update_speed(self.target_speed)

    def on_power_off(self):
        self.update_speed(0)

    def on_change_direction(self, direction):
        pass  # No additional logic for CLI