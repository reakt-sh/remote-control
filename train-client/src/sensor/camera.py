import cv2
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, QThread
from datetime import datetime
from utils.app_logger import logger

class CameraWorker(QThread):
    """Worker thread for camera frame capture to avoid blocking UI thread."""
    frame_captured = pyqtSignal(int, object, int, int)  # frame_count, frame, width, height

    def __init__(self, index: int = 0):
        super().__init__()
        self.index = index
        self.cap = None
        self.width = 0
        self.height = 0
        self.frame_count = 0
        self.start_time = None
        self.base_fps = 30
        self.current_fps = 30
        self._running = False
        self._mutex_running = False

    def _set_maximum_resolution(self):
        """Try to set the camera to its maximum supported resolution."""
        high_quality_resolutions = [
            # (1280, 720),   # 720p
            # (1024, 768),   # XGA
            # (800, 600),    # SVGA
            (640, 480),    # VGA (fallback)
        ]

        logger.info("Attempting to set camera to maximum resolution...")

        for width, height in high_quality_resolutions:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            if actual_width == width and actual_height == height:
                logger.info(f"Successfully set camera resolution to {width}x{height}")
                break
            else:
                logger.debug(f"Camera doesn't support {width}x{height}, got {actual_width}x{actual_height}")

        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        self.cap.set(cv2.CAP_PROP_FPS, 30)

    def get_camera_capabilities(self):
        """Get and log camera capabilities for debugging."""
        if not self.cap:
            return

        backend = self.cap.getBackendName()
        logger.info(f"Camera device: Index {self.index}, Backend: {backend}")

        capabilities = {
            'Width': self.cap.get(cv2.CAP_PROP_FRAME_WIDTH),
            'Height': self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
            'FPS': self.cap.get(cv2.CAP_PROP_FPS),
            'Brightness': self.cap.get(cv2.CAP_PROP_BRIGHTNESS),
            'Contrast': self.cap.get(cv2.CAP_PROP_CONTRAST),
            'Saturation': self.cap.get(cv2.CAP_PROP_SATURATION),
            'Hue': self.cap.get(cv2.CAP_PROP_HUE),
            'Gain': self.cap.get(cv2.CAP_PROP_GAIN),
            'Exposure': self.cap.get(cv2.CAP_PROP_EXPOSURE),
        }

        logger.info("Camera capabilities:")
        for prop, value in capabilities.items():
            logger.info(f"  {prop}: {value}")

        return capabilities

    def initialize_camera(self):
        """Initialize camera in worker thread."""
        self.cap = cv2.VideoCapture(self.index)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera")

        self._set_maximum_resolution()

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480

        logger.info(f"Camera initialized with resolution: {self.width}x{self.height}")
        self.get_camera_capabilities()

        fps = self.cap.get(cv2.CAP_PROP_FPS)
        if fps and fps > 1:
            self.base_fps = fps
        self.current_fps = min(self.current_fps, self.base_fps)
        self.frame_count = 0
        self.start_time = cv2.getTickCount()

    def run(self):
        """Main worker thread loop."""
        self._running = True
        self.initialize_camera()

        frame_interval = 1.0 / max(self.current_fps, 1)

        while self._running:
            if not self.cap:
                break

            start_capture = cv2.getTickCount()

            ret, frame = self.cap.read()
            if not ret:
                continue

            self.frame_count += 1
            elapsed_time = (cv2.getTickCount() - self.start_time) / cv2.getTickFrequency()
            current_fps = self.frame_count / elapsed_time if elapsed_time > 0 else 0

            # Add overlay text
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
            for x, y, text in positions:
                (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
                top_left = (x - 5, y - text_height - 5)
                bottom_right = (x + text_width + 5, y + 5)
                overlay = frame.copy()
                cv2.rectangle(overlay, top_left, bottom_right, bg_color, -1)
                cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)
            for x, y, text in positions:
                cv2.putText(frame, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)

            try:
                self.frame_captured.emit(self.frame_count, frame, self.width, self.height)
            except Exception as e:
                logger.error(f"Error emitting frame_captured signal: {e}")

            # Frame rate limiting
            capture_time = (cv2.getTickCount() - start_capture) / cv2.getTickFrequency()
            sleep_time = frame_interval - capture_time
            if sleep_time > 0:
                self.msleep(int(sleep_time * 1000))

        self.cleanup()

    def cleanup(self):
        """Clean up camera resources."""
        if self.cap:
            self.cap.release()
            self.cap = None

    def stop_capture(self):
        """Stop the capture thread."""
        self._running = False


class Camera(QObject):
    frame_ready = pyqtSignal(object, object, int, int, bool)

    def __init__(self, parent=None, index: int = 0):
        super().__init__(parent)
        self.index = index
        self.worker = None
        self.width = 0
        self.height = 0
        self.direction = 1  # forward/backward placeholder for API compatibility


    def init_capture(self):
        """Start camera capture in worker thread."""
        if self.worker and self.worker.isRunning():
            self.worker.stop_capture()
            self.worker.wait()

        self.worker = CameraWorker(self.index)
        self.worker.frame_captured.connect(self._on_frame_captured)
        self.worker.start()
        logger.info("Camera worker thread started")

    def _on_frame_captured(self, frame_count, frame, width, height):
        """Receive frame from worker thread and emit to main application."""
        self.width = width
        self.height = height
        try:
            self.frame_ready.emit(frame_count, frame, width, height, False)
        except Exception as e:
            logger.error(f"Error emitting frame_ready signal: {e}")

    def set_speed(self, speed_kmh: int):
        """Speed does not affect physical camera, just log it."""
        logger.debug("Do nothing about set_speed it's just a camera, speed_kmh=%d", speed_kmh)

    def set_direction(self, direction: int):
        """Direction does not affect physical camera, just store it."""
        if direction in (1, -1):
            self.direction = direction

    def stop(self):
        """Stop camera capture and worker thread."""
        if self.worker:
            self.worker.stop_capture()
            self.worker.wait()
            self.worker = None
        logger.info("Camera stopped")
