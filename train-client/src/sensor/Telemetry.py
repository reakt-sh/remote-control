import datetime
import random
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, QDateTime
from globals import STATION_LIST

class Telemetry(QObject):
    telemetry_ready = pyqtSignal(dict)  # Emits a dictionary with telemetry data

    def __init__(self, train_id: str, poll_interval_ms=3000, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll_telemetry)
        self.poll_interval_ms = poll_interval_ms

        self.name = "Train"
        self.status = "running"
        self.speed = 60
        self.max_speed = 60
        self.brake_status = "released"
        self.location_index = random.randint(0, len(STATION_LIST) - 1)
        self.next_station_index = self.get_next_station(self.location_index)
        self.passenger_count = random.randint(100, 200)
        self.temperature_min = random.randint(-5, 30)
        self.temperature_max = self.temperature_min + random.randint(3, 10)
        self.battery_level = round(random.uniform(70, 99), 2)
        self.video_stream_url = "/stream/" + train_id

        self.engine_temperature_min = random.randint(70, 85)
        self.engine_temperature_max = self.engine_temperature_min + random.randint(3, 10)
        self.fuel_level = round(random.uniform(70, 99), 2)
        self.network_signal_strength = random.randint(0,100)

    def get_next_station(self, current_station: int) -> int:
        return (current_station + 1) % len(STATION_LIST)

    def set_speed(self, speed: int):
        if 0 <= speed <= self.max_speed:
            self.speed = speed
            if speed == 0:
                self.brake_status = "applied"
            else:
                self.brake_status = "released"
        else:
            raise ValueError(f"Speed must be between 0 and {self.max_speed}")

    def start(self):
        self.timer.start(self.poll_interval_ms)

    def stop(self):
        self.timer.stop()

    def _poll_telemetry(self):
        # Replace this with actual telemetry data acquisition logic
        data =  {
            "name": self.name,
            "status": self.status,
            "speed": self.speed,
            "max_speed": self.max_speed,
            "brake_status": self.brake_status,
            "location": STATION_LIST[self.location_index]["name"],
            "next_station": STATION_LIST[self.next_station_index]["name"],
            "passenger_count": self.passenger_count,
            "temperature": random.randint(self.temperature_min, self.temperature_max),
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
        self.location_index = self.next_station_index
        self.next_station_index = self.get_next_station(self.location_index)
        self.battery_level -= random.uniform(0.1, 0.5)  # Simulate battery drain
        if self.battery_level < 0:
            self.battery_level = 0

        self.fuel_level -= random.uniform(0.1, 0.5) # Simulate fuel drain
        if self.fuel_level < 0:
            self.fuel_level = 0
        self.network_signal_strength = random.randint(0,100)

        # Emit the telemetry data
        self.telemetry_ready.emit(data)