from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from datetime import datetime
from picamera2 import Picamera2
from libcamera import controls
import libcamera
import cv2
import numpy as np
from loguru import logger

class CameraRPi5(QObject):
    frame_ready = pyqtSignal(object, object)  # Emits the frame (numpy array) and frame count

    def __init__(self, parent=None):
        super().__init__(parent)
        self.picam2 = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.capture_frame)
        self.frame_count = 0
        self.start_time = None

    def init_capture(self):
        try:
            # Initialize Pi Camera
            self.picam2 = Picamera2()

            # Configure camera (adjust these settings based on your needs)
            config = self.picam2.create_preview_configuration(
                main={"size": (1280, 720)},  # Adjust resolution as needed
                transform=libcamera.Transform(hflip=1, vflip=1)  # Flip if needed
            )
            self.picam2.configure(config)

            self.picam2.start()

            # Get camera properties
            self.width = self.picam2.camera_properties['PixelArraySize'][0]
            self.height = self.picam2.camera_properties['PixelArraySize'][1]
            self.fps = 30  # Default, can be adjusted in config

            print(f"Camera Resolution: {self.width}x{self.height}")
            print(f"Camera FPS: {self.fps}")

            self.frame_count = 0
            self.start_time = datetime.now().timestamp()
            self.timer.start(int(1000 / self.fps))  # Convert FPS to milliseconds

        except Exception as e:
            raise RuntimeError(f"Could not initialize Raspberry Pi camera: {str(e)}")

    def stop(self):
        self.timer.stop()
        if self.picam2:
            self.picam2.stop()
            self.picam2.close()
            self.picam2 = None

    def capture_frame(self):
        if self.picam2:
            try:
                # Capture array from Pi camera
                frame = self.picam2.capture_array("main")

                # Convert to BGR format (OpenCV default) if needed
                if frame.dtype == np.float32:
                    frame = (frame * 255).astype(np.uint8)
                if len(frame.shape) == 2:  # If grayscale
                    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                elif frame.shape[2] == 4:  # If RGBA
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                elif frame.shape[2] == 3:  # If RGB
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                self.frame_count += 1
                elapsed_time = datetime.now().timestamp() - self.start_time
                current_fps = self.frame_count / elapsed_time

                # Overlay resolution and FPS on the frame (same as your original code)
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

            except Exception as e:
                print(f"Error capturing frame: {str(e)}")

    def set_speed(self, speed: int):
        logger.info("Set_speed is called now")