import datetime
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, QDateTime

class Telemetry(QObject):
    telemetry_ready = pyqtSignal(dict)  # Emits a dictionary with telemetry data

    def __init__(self, poll_interval_ms=3000, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll_telemetry)
        self.poll_interval_ms = poll_interval_ms

    def start(self):
        self.timer.start(self.poll_interval_ms)

    def stop(self):
        self.timer.stop()

    def _poll_telemetry(self):
        # Replace this with actual telemetry data acquisition logic
        data = {
            "speed": 42.0,  # Example value
            "battery": 87.5,
            "temperature": 36.7,
            "gps": {
                "latitude": 37.7749,    # Example latitude
                "longitude": -122.4194, # Example longitude
                "altitude": 15.2        # Example altitude in meters
            },
            "timestamp": int(datetime.datetime.now().timestamp() * 1000),  # Current timestamp in milliseconds
        }
        self.telemetry_ready.emit(data)