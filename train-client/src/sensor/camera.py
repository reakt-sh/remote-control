import cv2
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from datetime import datetime
from loguru import logger

class Camera(QObject):
    frame_ready = pyqtSignal(object, object, int, int)

    def __init__(self, parent=None, index: int = 0):
        super().__init__(parent)
        self.index = index
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.capture_frame)
        self.width = 0
        self.height = 0
        self.frame_count = 0
        self.start_time = None
        self.base_fps = 30
        self.current_fps = 30
        self.direction = 1  # forward/backward placeholder for API compatibility

    def init_capture(self):
        self.cap = cv2.VideoCapture(self.index)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera")
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        if fps and fps > 1:
            self.base_fps = fps
        self.current_fps = min(self.current_fps, self.base_fps)
        self.frame_count = 0
        self.start_time = cv2.getTickCount()
        self.timer.start(int(1000 / max(self.current_fps, 1)))

    def set_speed(self, speed_kmh: int):
        # Speed does not affect physical camera, just log it.
        logger.debug("Do nothing about set_speed it's just a camera, speed_kmh=%d", speed_kmh)

    def set_direction(self, direction: int):
        # Direction does not affect physical camera, just store it.
        if direction in (1, -1):
            self.direction = direction

    def stop(self):
        self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None

    def capture_frame(self):
        if not self.cap:
            return
        ret, frame = self.cap.read()
        if not ret:
            return
        self.frame_count += 1
        elapsed_time = (cv2.getTickCount() - self.start_time) / cv2.getTickFrequency()
        current_fps = self.frame_count / elapsed_time if elapsed_time > 0 else 0

        # Overlay text similar to FileProcessor for consistency
        text_res = f"Resolution: {self.width}x{self.height}"
        text_fps = f"FPS: {current_fps:.1f}"
        text_frame_id = f"Frame ID: {self.frame_count}"
        now = datetime.now()
        text_date = now.strftime("Date: %y:%m:%d")
        text_time = now.strftime("Time: %H:%M:%S:%f")[:-3]

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        color = (229, 230, 216)
        thickness = 1
        bg_color = (50, 50, 50)
        opacity = 0.6
        positions = [
            (10, 30, text_res),
            (10, 60, text_fps),
            (10, 90, text_frame_id),
            (10, 120, text_date),
            (10, 150, text_time),
        ]
        for x, y, text in positions:
            (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
            top_left = (x - 5, y - text_height - 5)
            bottom_right = (x + text_width + 5, y + 5)
            overlay = frame.copy()
            cv2.rectangle(overlay, top_left, bottom_right, bg_color, -1)
            cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)
        for x, y, text in positions:
            cv2.putText(frame, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)

        # add try catch here
        try:
            self.frame_ready.emit(self.frame_count, frame, self.width, self.height)
        except Exception as e:
            logger.error(f"Error emitting frame_ready signal: {e}")