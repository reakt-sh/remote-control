import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from datetime import datetime
from globals import VIDEO_FPS, VIDEO_RESOLUTION


class Camera(Node):

    def __init__(self, index: int = 0):
        super().__init__('camera')
        self.index = index
        self.cap = None
        self._timer = None
        self.width = 0
        self.height = 0
        self.frame_count = 0
        self.current_fps = VIDEO_FPS
        self.direction = 1

        self._publisher = self.create_publisher(CompressedImage, 'frame_ready', 10)

    def _set_resolution(self):
        resolution = VIDEO_RESOLUTION
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

    def init_capture(self):
        self.cap = cv2.VideoCapture(self.index)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera")

        self._set_resolution()
        self.cap.set(cv2.CAP_PROP_FPS, self.current_fps)

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.get_logger().info(f"Camera initialized with resolution: {self.width}x{self.height}")

        fps = self.cap.get(cv2.CAP_PROP_FPS)
        if fps and fps > 1:
            self.current_fps = min(self.current_fps, fps)

        self.frame_count = 0
        self._timer = self.create_timer(1.0 / self.current_fps, self.capture_frame)

    def set_speed(self, speed_kmh: int):
        self.get_logger().debug(f"Do nothing about set_speed, it's just a camera, speed_kmh={speed_kmh}")

    def set_direction(self, direction: int):
        if direction in (1, -1):
            self.direction = direction

    def stop(self):
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        if self.cap:
            self.cap.release()
            self.cap = None
        self.get_logger().info("Camera stopped")

    def capture_frame(self):
        if self.cap is None:
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        self.frame_count += 1

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
            cv2.putText(frame, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)

        try:
            msg = CompressedImage()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = f"{self.frame_count}:{self.width}:{self.height}"
            msg.format = "bgr24"
            msg.data = frame.tobytes()
            self._publisher.publish(msg)
        except Exception as e:
            self.get_logger().error(f"Error publishing frame: {e}")
