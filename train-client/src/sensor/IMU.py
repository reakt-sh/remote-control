import datetime
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

class IMU(QObject):
    imu_ready = pyqtSignal(dict)  # Emits a dictionary with IMU data

    def __init__(self, poll_interval_ms=3000, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll_imu)
        self.poll_interval_ms = poll_interval_ms

    def start(self):
        self.timer.start(self.poll_interval_ms)

    def stop(self):
        self.timer.stop()

    def _poll_imu(self):
        # Replace this with actual IMU data acquisition logic
        data = {
            "accel_x": 0.01,  # Example values
            "accel_y": -0.02,
            "accel_z": 9.81,
            "gyro_x": 0.001,
            "gyro_y": 0.002,
            "gyro_z": 0.003,
            "timestamp": int(datetime.datetime.now().timestamp() * 1000),  # Current timestamp in milliseconds
        }
        self.imu_ready.emit(data)