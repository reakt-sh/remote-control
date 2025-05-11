import cv2
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from datetime import datetime

class FileProcessor(QObject):
    frame_ready = pyqtSignal(object, object)  # Emits (frame_count, frame)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_path = "asset/Train_Driver_View_640x480_60FPS_Sample_03.mp4"

        # print current working directory
        import os
        print("Current working directory:", os.getcwd())
        self.video_path = os.path.join(os.getcwd(), self.video_path)


        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.capture_frame)
        self.frame_count = 0
        self.start_time = None
        self.width = 0
        self.height = 0
        self.original_fps = 60
        self.current_fps = 60

    def init_capture(self, speed_kmh=60):
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open video file")

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.original_fps = self.cap.get(cv2.CAP_PROP_FPS) or 60
        self.set_speed(speed_kmh)
        self.frame_count = 0
        self.start_time = cv2.getTickCount()
        self.timer.start(int(1000 / self.current_fps))

    def set_speed(self, speed_kmh):
        # FPS is directly equal to speed (max 60)
        self.current_fps = min(max(int(speed_kmh), 1), 60)
        if self.timer.isActive():
            self.timer.stop()
            self.timer.start(int(1000 / self.current_fps))

    def stop(self):
        self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None

    def capture_frame(self):
        if self.cap:
            ret, frame = self.cap.read()
            if not ret:
                self.stop()
                return
            self.frame_count += 1
            elapsed_time = (cv2.getTickCount() - self.start_time) / cv2.getTickFrequency()
            current_fps = self.frame_count / elapsed_time if elapsed_time > 0 else 0

            # Overlay info
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

            for pos in positions:
                x, y, text = pos
                (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
                top_left = (x - 5, y - text_height - 5)
                bottom_right = (x + text_width + 5, y + 5)
                overlay = frame.copy()
                cv2.rectangle(overlay, top_left, bottom_right, bg_color, -1)
                cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)

            for pos in positions:
                x, y, text = pos
                cv2.putText(
                    frame,
                    text,
                    (x, y),
                    font,
                    font_scale,
                    color,
                    thickness,
                    cv2.LINE_AA
                )

            self.frame_ready.emit(self.frame_count, frame)