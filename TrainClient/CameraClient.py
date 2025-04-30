import cv2
import av
import zmq
from fractions import Fraction
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, pyqtSlot
from globals import *
from NetworkWorker import NetworkWorker

class CameraClient(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_camera()
        self.init_encoder()
        self.init_network()
        
    def init_ui(self):
        self.setWindowTitle("Train Client")
        self.setGeometry(START_X, START_Y, START_X + WINDOW_WIDTH, START_Y + WINDOW_HEIGHT)
        self.setStyleSheet(f"background-color: {BG_COLOR};")
        
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~30 FPS
        
    def init_camera(self):
        # available_resolutions = self.get_available_resolutions()
        # print("Available Resolutions:", available_resolutions)


        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera")
            
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

        print(f"Camera Resolution: {self.width}x{self.height}")
        print(f"Camera FPS: {self.fps}")

        
        # Ensure we have a valid FPS (some cameras return 0)
        if self.fps <= 0:
            self.fps = 30  # Default to 30 FPS
            
    def init_encoder(self):
        # Create in-memory output container
        self.output_container = av.open('pipe:', mode='w', format='mp4')
        
        # Convert FPS to a fraction
        fps_fraction = Fraction(self.fps).limit_denominator(1000)
        
        # Add H.264 video stream
        self.stream = self.output_container.add_stream('h264', rate=fps_fraction)
        self.stream.width = self.width
        self.stream.height = self.height
        self.stream.pix_fmt = 'yuv420p'
        
        # Set some encoding options
        self.stream.options = {
            'preset': 'fast',
            'crf': '23',
            'tune': 'zerolatency'
        }
        
    def init_network(self):
        self.network_worker = NetworkWorker()
        self.network_worker.packet_sent.connect(self.on_packet_sent)
        self.network_worker.start()
        
    @pyqtSlot(int)
    def on_packet_sent(self, size):
        # Optional: Update UI with sent packet info
        pass
        
    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # Calculate current FPS (if not static)
            if not hasattr(self, 'frame_count'):
                self.frame_count = 0
                self.start_time = cv2.getTickCount()
            
            self.frame_count += 1
            elapsed_time = (cv2.getTickCount() - self.start_time) / cv2.getTickFrequency()
            current_fps = self.frame_count / elapsed_time

            # Overlay resolution and FPS on the frame
            text_res = f"Resolution: {self.width}x{self.height}"
            text_fps = f"FPS: {current_fps:.1f}"
            text_frame_id = f"Frame ID: {self.frame_count}"
            
            # Position and style the text
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.7
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

            # Convert to RGB for PyQt display
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.image_label.setPixmap(QPixmap.fromImage(qt_image))
            
            # Encode frame
            self.encode_frame(frame)
            
    def encode_frame(self, frame):
        av_frame = av.VideoFrame.from_ndarray(frame, format='bgr24')
        for packet in self.stream.encode(av_frame):
            # Convert packet to bytes and send
            self.network_worker.enqueue_packet(bytes(packet))
            
    def closeEvent(self, event):
        self.timer.stop()
        self.cap.release()
        self.output_container.close()
        self.network_worker.stop()
        event.accept()
