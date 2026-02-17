from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput
from libcamera import controls, Transform
import libcamera
import cv2
import numpy as np
from utils.app_logger import logger
import io
import threading
import time
from globals import *

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = threading.Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

class CameraRPi5(QObject):
    frame_ready = pyqtSignal(object, object, int, int, bool)  # Emits frame_count, encoded_data, width, height

    def __init__(self, parent=None):
        super().__init__(parent)
        self.picam2 = None
        self.encoder = None
        self.output = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.capture_frame)
        self.frame_count = 0
        self.start_time = None

    def init_capture(self):
        try:
            self.picam2 = Picamera2()

            frame_duration = int(1e6 / VIDEO_FPS)  # in microseconds

            # Determine transform based on IS_CAMERA_UPSIDE_DOWN_ENABLED
            transform = Transform.ROT180 if IS_CAMERA_UPSIDE_DOWN_ENABLED else Transform.IDENTITY

            # Configure for H.264 encoding
            video_config = self.picam2.create_video_configuration(
                main={"size": VIDEO_RESOLUTION, "format": VIDEO_FORMAT_PICAMERA},
                controls={"FrameDurationLimits": (frame_duration, frame_duration)},
                transform=transform
            )
            self.picam2.configure(video_config)

            # Setup H.264 encoder
            self.encoder = H264Encoder(bitrate=VIDEO_BITRATE)
            self.output = StreamingOutput()

            self.picam2.start_recording(self.encoder, FileOutput(self.output))

            # Get camera properties
            main_stream = self.picam2.stream_configuration("main")
            self.width, self.height = main_stream["size"]
            self.fps = VIDEO_FPS

            print(f"Camera Resolution: {self.width}x{self.height}")
            print(f"Camera FPS: {self.fps}")

            self.frame_count = 0
            self.start_time = int(time.time() * 1000)
            self.timer.start(int(1000 / self.fps))

        except Exception as e:
            raise RuntimeError(f"Could not initialize Raspberry Pi camera: {str(e)}")

    def stop(self):
        self.timer.stop()
        if self.picam2:
            self.picam2.stop_recording()
            self.picam2.stop()
            self.picam2.close()
            self.picam2 = None
            self.encoder = None
            self.output = None

    def capture_frame(self):
        if self.picam2 and self.output:
            try:
                # Get H.264 encoded data from streaming output
                with self.output.condition:
                    self.output.condition.wait()
                    encoded_data = self.output.frame

                self.frame_count += 1

                # Emit encoded H.264 data directly
                self.frame_ready.emit(self.frame_count, encoded_data, self.width, self.height, True)

            except Exception as e:
                logger.error(f"Error capturing frame: {str(e)}")

    def set_speed(self, speed: int):
        logger.info("Set_speed is called now")