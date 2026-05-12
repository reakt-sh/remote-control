import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from datetime import datetime
import random
import os
from globals import ASSET_DIR, MAX_SPEED


class FileProcessor(Node):

    def __init__(self):
        super().__init__('file_processor')

        asset_dir = ASSET_DIR
        video_files = [f for f in os.listdir(asset_dir) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
        if not video_files:
            raise RuntimeError("No video files found in asset directory")
        selected_video = random.choice(video_files)
        self.video_path = os.path.join(asset_dir, selected_video)
        self.get_logger().info(f"Selected video: {self.video_path}")

        self.cap = None
        self._timer = None           # replaces QTimer
        self.frame_count = 0
        self.start_time = None
        self.width = 0
        self.height = 0
        self.original_fps = 30
        self.current_fps = 30
        self.direction = 1

        self._bridge = CvBridge()
        # Replaces: frame_ready = pyqtSignal(object, object, int, int, bool)
        self._publisher = self.create_publisher(Image, 'frame_ready', 10)

        self.set_speed(MAX_SPEED)

    def init_capture(self, speed_kmh=MAX_SPEED):
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open video file")

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.original_fps = 30
        self.set_speed(speed_kmh)
        self.frame_count = 0
        self.start_time = self.get_clock().now()
        # replaces: self.timer.start(int(1000 / self.current_fps))
        self._timer = self.create_timer(1.0 / self.current_fps, self.capture_frame)

    def set_speed(self, speed_kmh):
        self.current_fps = min(self.original_fps, max(1, int((speed_kmh / MAX_SPEED) * self.original_fps)))
        if self._timer is not None:          # replaces: if self.timer.isActive()
            self._timer.cancel()
            self._timer = self.create_timer(1.0 / self.current_fps, self.capture_frame)

    def set_direction(self, direction):
        """Set direction: 1 for forward, -1 for backward."""
        if direction not in (1, -1):
            raise ValueError("Direction must be 1 (forward) or -1 (backward)")
        self.direction = direction

    def stop(self):
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
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

        # Overlay info — identical to original
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

        # Replaces: self.frame_ready.emit(self.frame_count, frame, self.width, self.height, False)
        try:
            msg = self._bridge.cv2_to_imgmsg(frame, encoding='bgr8')
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = str(self.frame_count)   # carries frame_count
            # encoding='bgr8' implies is_encoded=False (raw frame, not H264)
            self._publisher.publish(msg)
        except Exception as e:
            self.get_logger().error(f"Error publishing frame, no subscriber connected: {e}")