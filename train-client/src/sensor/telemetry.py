import datetime
import random
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, QDateTime
from globals import *

class Telemetry(QObject):
    telemetry_ready = pyqtSignal(dict)  # Emits a dictionary with telemetry data

    def __init__(self, train_id: str, poll_interval_ms=1000, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll_telemetry)
        self.poll_interval_ms = poll_interval_ms

        self.name = "Train"
        self.train_id = train_id
        self.status = TRAIN_STATUS["POWER_ON"]
        self.direction = DIRECTION["FORWARD"]
        self.speed = 60
        self.max_speed = 60
        self.brake_status = "released"
        self.location_index = random.randint(0, len(STATION_LIST) - 1)
        self.next_station_index = self.get_next_station(self.location_index)
        self.passenger_count = random.randint(100, 200)

        self.temperature_min = random.randint(-5, 30)
        self.temperature_max = self.temperature_min + random.randint(3, 10)
        self.temperature = random.randint(self.temperature_min, self.temperature_max)

        self.battery_level = round(random.uniform(70, 99), 2)
        self.video_stream_url = "/stream/" + train_id

        self.engine_temperature_min = random.randint(70, 85)
        self.engine_temperature_max = self.engine_temperature_min + random.randint(3, 10)
        self.engine_temperature = random.randint(self.engine_temperature_min, self.engine_temperature_max)

        self.fuel_level = round(random.uniform(70, 99), 2)
        self.network_signal_strength = random.randint(0,100)
        self.last_simulation_at_frame = 0
        self.frame_counter = 0

    def get_next_station(self, current_station: int) -> int:
        return (current_station + 1) % len(STATION_LIST)

    def get_speed(self):
        return self.speed

    def set_speed(self, speed: int):
        if 0 <= speed <= self.max_speed:
            self.speed = speed
            if speed == 0:
                self.brake_status = "applied"
            else:
                self.brake_status = "released"
        else:
            raise ValueError(f"Speed must be between 0 and {self.max_speed}")

    def set_status(self, status: str):
        self.status = status

    def set_direction(self, direction: int):
        self.direction = direction

    def start(self):
        self.timer.start(self.poll_interval_ms)

    def stop(self):
        self.timer.stop()

    def notify_new_frame_processed(self):
        self.frame_counter += 1
        if self.frame_counter > self.last_simulation_at_frame + (60*5):
            self.last_simulation_at_frame = self.frame_counter
            self.simulte_data(True)

    def simulte_data(self, everything=False):
        if everything:
            self.location_index = self.next_station_index
            self.next_station_index = self.get_next_station(self.location_index)
            self.network_signal_strength = random.randint(10,100)
            self.temperature = random.randint(self.temperature_min, self.temperature_max)


        self.battery_level -= random.uniform(0.1, 0.4)  # Simulate battery drain
        if self.battery_level < 0:
            self.battery_level = 0

        self.fuel_level -= random.uniform(0.1, 0.4) # Simulate fuel drain
        if self.fuel_level < 0:
            self.fuel_level = 0


    def _poll_telemetry(self):
        # Replace this with actual telemetry data acquisition logic
        data =  {
            "name": self.name,
            "train_id": self.train_id,
            "status": self.status,
            "direction": self.direction,
            "speed": self.speed,
            "max_speed": self.max_speed,
            "brake_status": self.brake_status,
            "location": STATION_LIST[self.location_index]["name"],
            "next_station": STATION_LIST[self.next_station_index]["name"],
            "passenger_count": self.passenger_count,
            "temperature": self.temperature,
            "battery_level": self.battery_level,
            "video_stream_url": self.video_stream_url,
            "gps": {
                "latitude": STATION_LIST[self.location_index]["latitude"],
                "longitude": STATION_LIST[self.location_index]["longitude"],
            },
            "timestamp": int(datetime.datetime.now().timestamp() * 1000),  # Current timestamp in milliseconds,
            "engine_temperature": random.randint(self.engine_temperature_min, self.engine_temperature_max),
            "fuel_level": self.fuel_level,
            "network_signal_strength": self.network_signal_strength
        }

        self.simulte_data()

        # Emit the telemetry data
        self.telemetry_ready.emit(data)