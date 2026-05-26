import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput
from libcamera import controls, Transform
import libcamera
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

class CameraRPi5(Node):

    def __init__(self):
        super().__init__('camera_rpi5')
        self.picam2 = None
        self.encoder = None
        self.output = None
        self._timer = None
        self.frame_count = 0
        self.start_time = None
        self.width = 0
        self.height = 0

        self._publisher = self.create_publisher(CompressedImage, 'frame_ready', 10)

    def init_capture(self):
        try:
            self.picam2 = Picamera2()

            frame_duration = int(1e6 / VIDEO_FPS)  # in microseconds

            # Determine transform based on IS_CAMERA_UPSIDE_DOWN_ENABLED
            # 180-degree rotation is achieved by flipping both horizontally and vertically
            transform = Transform(hflip=0, vflip=0) if IS_CAMERA_UPSIDE_DOWN_ENABLED else Transform()

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

            self.get_logger().info(f"Camera Resolution: {self.width}x{self.height}")
            self.get_logger().info(f"Camera FPS: {self.fps}")

            self.frame_count = 0
            self.start_time = int(time.time() * 1000)
            self._timer = self.create_timer(1.0 / self.fps, self.capture_frame)

        except Exception as e:
            raise RuntimeError(f"Could not initialize Raspberry Pi camera: {str(e)}")

    def stop(self):
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
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

                msg = CompressedImage()
                msg.header.stamp = self.get_clock().now().to_msg()
                msg.header.frame_id = f"{self.frame_count}:{self.width}:{self.height}"
                msg.format = "h264"
                msg.data = bytes(encoded_data)
                self._publisher.publish(msg)

            except Exception as e:
                logger.error(f"Error capturing frame: {str(e)}")

    def set_speed(self, speed: int):
        self.get_logger().info("Set_speed is called now")