import cv2
import threading
import time
from datetime import datetime
from globals import VIDEO_FPS, VIDEO_RESOLUTION


"""
# ROS2: Import ROS2 libraries and message types
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
class Camera(Node):
"""

class _Signal:
    """Lightweight callback signal, drop-in for pyqtSignal in non-Qt threads."""

    def __init__(self):
        self._callbacks = []

    def connect(self, callback):
        self._callbacks.append(callback)

    def emit(self, *args):
        for cb in self._callbacks:
            cb(*args)


class Camera:
    def __init__(self, parent=None, index: int = 0):
        self.frame_ready = _Signal()
        self.index = index
        self.cap = None

        """
        # ROS2: timer usage
        self._timer = None
        """
        self._thread = None
        self._running = False
        self.width = 0
        self.height = 0
        self.frame_count = 0
        self.current_fps = VIDEO_FPS
        self.direction = 1

        """
        # ROS2: Publisher for compressed images
        self._publisher = self.create_publisher(CompressedImage, 'frame_ready', 10)
        """

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

        fps = self.cap.get(cv2.CAP_PROP_FPS)
        if fps and fps > 1:
            self.current_fps = min(self.current_fps, fps)

        self.frame_count = 0
        """
        # ROS2: Start timer for frame capture
        self._timer = self.create_timer(1.0 / self.current_fps, self.capture_frame)
        """

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def _capture_loop(self):
        interval = 1.0 / self.current_fps
        while self._running:
            t0 = datetime.now().timestamp()
            self.capture_frame()
            elapsed = datetime.now().timestamp() - t0
            remaining = interval - elapsed
            if remaining > 0:
                time.sleep(remaining)

    def set_speed(self, speed_kmh: int):
        pass

    def set_direction(self, direction: int):
        if direction in (1, -1):
            self.direction = direction

    def stop(self):
        """
        # ROS2: Stop timer and release camera
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        """

        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self.cap:
            self.cap.release()
            self.cap = None

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
            overlay = frame.copy()
            cv2.rectangle(overlay, (x - 5, y - text_height - 5), (x + text_width + 5, y + 5), bg_color, -1)
            cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)

        for pos in positions:
            x, y, text = pos
            cv2.putText(frame, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)

        self.frame_ready.emit(self.frame_count, frame, self.width, self.height, False)

        """
        # ROS2: Publish the frame as a CompressedImage message
        try:
            msg = CompressedImage()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = f"{self.frame_count}:{self.width}:{self.height}"
            msg.format = "bgr24"
            msg.data = frame.tobytes()
            self._publisher.publish(msg)
        except Exception as e:
            self.get_logger().error(f"Error publishing frame: {e}")
        """
