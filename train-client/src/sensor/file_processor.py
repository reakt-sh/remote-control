import cv2
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from datetime import datetime
import random
import os
from loguru import logger
from globals import ASSET_DIR, MAX_SPEED

class FileProcessor(QObject):
    frame_ready = pyqtSignal(object, object, int, int, bool)  # Emits (frame_count, frame)

    def __init__(self, parent=None):
        super().__init__(parent)

        asset_dir = ASSET_DIR
        # List all video files in the asset directory (you can filter by extension if needed)
        video_files = [f for f in os.listdir(asset_dir) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
        if not video_files:
            raise RuntimeError("No video files found in asset directory")
        selected_video = random.choice(video_files)
        self.video_path = os.path.join(asset_dir, selected_video)
        print(f"Selected video: {self.video_path}")

        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.capture_frame)
        self.frame_count = 0
        self.start_time = None
        self.width = 0
        self.height = 0
        self.original_fps = 60
        self.current_fps = 20
        self.set_speed(MAX_SPEED)

        self.direction = 1  # 1 for forward, -1 for backward

    def init_capture(self, speed_kmh=MAX_SPEED):
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

    def set_direction(self, direction):
        """Set direction: 1 for forward, -1 for backward."""
        if direction not in (1, -1):
            raise ValueError("Direction must be 1 (forward) or -1 (backward)")
        self.direction = direction

    def stop(self):
        self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None

    def capture_frame(self):
        if self.cap:
            frame_pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

            if self.direction == 1:
                ret, frame = self.cap.read()
                if not ret:
                    # Loop to start if at end
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()
                    if not ret:
                        self.stop()
                        return
            else:  # Backward
                # Move back two frames (since reading moves forward by one)
                prev_frame = frame_pos - 2
                if prev_frame < 0:
                    prev_frame = total_frames - 1
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, prev_frame)
                ret, frame = self.cap.read()
                if not ret:
                    # Loop to end if at start
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
                    ret, frame = self.cap.read()
                    if not ret:
                        self.stop()
                        return

            self.frame_count += 1
            elapsed_time = (cv2.getTickCount() - self.start_time) / cv2.getTickFrequency()
            current_fps = self.frame_count / elapsed_time if elapsed_time > 0 else 0

            # Overlay info
            text_res = f"Resolution: {self.width}x{self.height}"
            text_frame_id = f"Frame ID: {self.frame_count}"
            now = datetime.now()
            text_date = now.strftime("Date: %d-%B-%Y")
            text_time = now.strftime("Time: %H:%M:%S:%f")[:-3]

            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            color = (229, 230, 216)
            thickness = 1
            bg_color = (50, 50, 50)
            opacity = 0.6

            positions = [
                (10, 30, text_res),
                (10, 60, text_frame_id),
                (10, 90, text_date),
                (10, 120, text_time),
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
            # add a try catch here
            try:
                self.frame_ready.emit(self.frame_count, frame, self.width, self.height, False)
            except Exception as e:
                logger.error(f"Error emitting frame_ready signal, call back is not connected: {e}")