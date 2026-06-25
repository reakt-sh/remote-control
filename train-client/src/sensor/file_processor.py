import cv2
import threading
import time
from datetime import datetime
import random
import os
from globals import ASSET_DIR, MAX_SPEED

"""
# ROS2: Import ROS2 libraries and message types
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage

class FileProcessor(Node):
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


class FileProcessor:

    def __init__(self, parent=None):
        self.frame_ready = _Signal()
        asset_dir = ASSET_DIR
        video_files = [f for f in os.listdir(asset_dir) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
        if not video_files:
            raise RuntimeError("No video files found in asset directory")
        selected_video = random.choice(video_files)
        self.video_path = os.path.join(asset_dir, selected_video)

        """
        # ROS2: timer usage
        self._timer = None           # replaces QTimer
        """

        self._thread = None
        self._running = False

        self.cap = None
        self.frame_count = 0
        self.start_time = None
        self.width = 0
        self.height = 0
        self.original_fps = 30
        self.current_fps = 30
        self.direction = 1

        """
        # ROS2: Publisher for compressed images
        self._publisher = self.create_publisher(CompressedImage, 'frame_ready', 10)
        """


    def init_capture(self, speed_kmh=MAX_SPEED):
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open video file")

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.frame_count = 0

        """
        # ROS2: use ROS2 clock
        self.start_time = self.get_clock().now() 
        """

        self.start_time = datetime.now().timestamp()
        self.set_speed(MAX_SPEED)

        """
        # ROS2: Start timer for frame capture
        self._timer = self.create_timer(1.0 / self.current_fps, self.capture_frame)
        """

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()


    def _capture_loop(self):
        while self._running:
            interval = 1.0 / self.current_fps
            t0 = datetime.now().timestamp()
            self.capture_frame()
            elapsed = datetime.now().timestamp() - t0
            remaining = interval - elapsed
            if remaining > 0:
                time.sleep(remaining)


    def set_speed(self, speed_kmh):
        self.current_fps = min(self.original_fps, max(1, int((speed_kmh / MAX_SPEED) * self.original_fps)))

        """
        # ROS2: use ROS2 timer
        if self._timer is not None:
            self._timer.cancel()
        self._timer = self.create_timer(1.0 / self.current_fps, self.capture_frame)
        """

    def set_direction(self, direction):
        """Set direction: 1 for forward, -1 for backward."""
        if direction not in (1, -1):
            raise ValueError("Direction must be 1 (forward) or -1 (backward)")
        self.direction = direction

    def stop(self):
        """
        # ROS2: stop ROS2 timer
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

        frame_pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if self.direction == 1:
            ret, frame = self.cap.read()
            if not ret:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret:
                    self.stop()
                    return
        else:
            prev_frame = frame_pos - 2
            if prev_frame < 0:
                prev_frame = total_frames - 1
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, prev_frame)
            ret, frame = self.cap.read()
            if not ret:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
                ret, frame = self.cap.read()
                if not ret:
                    self.stop()
                    return

        self.frame_count += 1
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
            self.get_logger().error(f"Error publishing frame, no subscriber connected: {e}")
        """