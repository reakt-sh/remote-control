import sys
import cv2
import av
import zmq
import queue
from fractions import Fraction
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, pyqtSlot

class NetworkWorker(QThread):
    packet_sent = pyqtSignal(int)  # Signal to emit when packet is sent
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.packet_queue = queue.Queue()
        self.running = True
        
    def run(self):
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        socket.bind("tcp://*:5555")
        
        while self.running:
            try:
                packet = self.packet_queue.get(timeout=0.1)
                if packet:
                    # For H.264 packets, we might want to send NAL units separately
                    # Here we'll just send the whole packet
                    socket.send(packet)
                    self.packet_sent.emit(len(packet))
            except queue.Empty:
                continue
                
        socket.close()
        context.term()
        
    def stop(self):
        self.running = False
        self.wait()
        
    def enqueue_packet(self, packet):
        self.packet_queue.put(packet)

class CameraClient(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_camera()
        self.init_encoder()
        self.init_network()
        
    def init_ui(self):
        self.setWindowTitle("Camera Streamer")
        self.setGeometry(100, 100, 800, 600)
        
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~30 FPS
        
    def init_camera(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera")
            
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        
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
            # Display in UI
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = CameraClient()
    client.show()
    sys.exit(app.exec_())