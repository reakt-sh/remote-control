import cv2
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from globals import *

class Camera(QObject):
    frame_ready = pyqtSignal(object, object)  # Emits the frame (numpy array)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.capture_frame)

    def init_camera(self):
        # Initialize camera capture
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera")

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

        print(f"Camera Resolution: {self.width}x{self.height}")
        print(f"Camera FPS: {self.fps}")
        self.timer.start(int(self.fps))


        self.frame_count = 0  # Initialize frame count
        self.start_time = cv2.getTickCount()  # Initialize start time

    def stop(self):
        self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None

    def capture_frame(self):
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                self.frame_count += 1
                elapsed_time = (cv2.getTickCount() - self.start_time) / cv2.getTickFrequency()
                current_fps = self.frame_count / elapsed_time

                # Overlay resolution and FPS on the frame
                text_res = f"Resolution: {self.width}x{self.height}"
                text_fps = f"FPS: {current_fps:.1f}"
                text_frame_id = f"Frame ID: {self.frame_count}"

                # Position and style the text
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.5
                color = (229, 230, 216)
                thickness = 2

                # Draw resolution text (top-left corner)
                cv2.putText(
                    frame,
                    text_res,
                    (10, 30),
                    font,
                    font_scale,
                    color,
                    thickness,
                    cv2.LINE_AA
                )

                # Draw FPS text (below resolution)
                cv2.putText(
                    frame,
                    text_fps,
                    (10, 60),
                    font,
                    font_scale,
                    color,
                    thickness,
                    cv2.LINE_AA
                )

                # Draw FrameID text (below FPS)
                cv2.putText(
                    frame,
                    text_frame_id,
                    (10, 90),
                    font,
                    font_scale,
                    color,
                    thickness,
                    cv2.LINE_AA
                )

                # Emit the frame signal with the processed frame
                self.frame_ready.emit(self.frame_count, frame)