import cv2
import av
import zmq
import datetime
from fractions import Fraction
from PyQt5.QtWidgets import QMainWindow, QLabel, QGridLayout, QVBoxLayout, QWidget, QTextEdit, QPushButton
from PyQt5.QtGui import QImage, QPixmap, QTextCursor
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtCore import QDateTime

from globals import *
from NetworkWorker import NetworkWorker
from sensor.Camera import Camera

class TrainClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_encoder()
        self.init_network()

        self.is_capturing = True   # Track capture state
        self.is_sending = False    # Start with sending disabled

        # Camera setup
        self.camera = Camera()
        self.camera.frame_ready.connect(self.on_new_frame)
        self.camera.init_camera()

        # Add timestamp to H264_DUMP filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{H264_DUMP}_{timestamp}.h264"
        self.output_file = open(output_filename, 'wb')

    def init_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.setWindowTitle("Train Client")
        self.setGeometry(START_X, START_Y, START_X + WINDOW_WIDTH, START_Y + WINDOW_HEIGHT)
        self.setStyleSheet(f"background-color: {BG_COLOR};")


        # create a image label to display the camera feed
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)

        # create console log widget
        self.console_log = QTextEdit()
        self.console_log.setReadOnly(True)
        self.console_log.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: Consolas, Courier New, monospace;
                font-size: 10pt;
                border: 1px solid #444;
            }
        """)

        # Create the toggle capture button
        self.capture_button = QPushButton("Stop Capture")
        self.capture_button.setMinimumWidth(BUTTON_WIDTH)
        self.capture_button.setMaximumWidth(BUTTON_WIDTH)
        self.capture_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;  /* Red */
                color: white;
                border: none;
                padding: 8px;
                font-size: 12pt;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #f44335;
            }
        """)
        self.capture_button.clicked.connect(self.toggle_capture)

        # Create the toggle sending button
        self.sending_button = QPushButton("Start Sending")
        self.sending_button.setMinimumWidth(BUTTON_WIDTH)
        self.sending_button.setMaximumWidth(BUTTON_WIDTH)
        self.sending_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px;
                font-size: 12pt;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.sending_button.clicked.connect(self.toggle_sending)

        # Create VBox layout for the buttons
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.capture_button)
        button_layout.addWidget(self.sending_button)
        button_layout.addStretch()  # This adds spacing at the bottom


        layout = QGridLayout()
        layout.addWidget(self.image_label, 0, 0)
        layout.addLayout(button_layout, 0, 1)
        layout.addWidget(self.console_log, 1, 0, 1, 2)

        self.central_widget.setLayout(layout)

    def init_encoder(self):
        # Create in-memory output container
        self.output_container = av.open('pipe:', mode='w', format='mp4')

        # Convert FPS to a fraction
        fps_fraction = Fraction(FRAME_RATE).limit_denominator(1000)

        # Add H.264 video stream
        self.stream = self.output_container.add_stream('h264', rate=fps_fraction)
        self.stream.width = FRAME_WIDTH
        self.stream.height = FRAME_HEIGHT
        self.stream.pix_fmt = PIXEL_FORMAT

        # Set some encoding options
        self.stream.options = {
            'g': '30',
            'gop_size': '30',
            'idr_interval': '30',
            'keyint_min': '30',
            'forced-idr': '1',
            'preset': 'fast',
            'level': '3.1',
            'crf': '23',
            'tune': 'zerolatency',
            'sc_threshold': '0',
            'x264-params': (
                'keyint=30:min-keyint=30:scenecut=0:'
                'force-idr=1:repeat_headers=1'  # ← Forces SPS/PPS with each IDR
            ),
        }
        self.manual_sps_pps = False

    def init_network(self):
        self.network_worker = NetworkWorker()
        self.network_worker.packet_sent.connect(self.on_packet_sent)
        self.network_worker.start()

    @pyqtSlot(int)
    def on_packet_sent(self, size):
        # Optional: Update UI with sent packet info
        pass

    def on_new_frame(self, frame_id, frame):
        # Convert to RGB for PyQt display
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))

        # Encode frame
        self.encode_frame(frame_id, frame)

    def encode_frame(self, frame_id, frame):
        av_frame = av.VideoFrame.from_ndarray(frame, format='bgr24')

        for packet in self.stream.encode(av_frame):
            # First packet: SPS/PPS (NAL type 7/8) (if needed)
            # Last packet: IDR frame (NAL type 5) or P-frame (NAL type 1) or B-frame (NAL type 0)

            # After creating the stream, extract headers
            current_sps_pps = self.stream.codec_context.extradata

            # Get raw bytes from the packet
            packet_bytes = bytes(packet)

            # Print basic info (first 16 bytes + total size)
            # print(f"\nEncoded Packet ({frame_id}): {len(packet_bytes)} bytes")
            # print(f"First 16 bytes: {packet_bytes[:16].hex(' ')}")

            # Optional: Print NAL unit type (for H.264)
            if len(packet_bytes) > 0:
                nal_type = packet_bytes[4] & 0x1F  # H.264 NAL unit type
                if nal_type == 7:
                    self.log_message(f"SPS NAL unit detected for Frame ID: {frame_id}")
                elif nal_type == 8:
                    self.log_message(f"PPS NAL unit detected for Frame ID: {frame_id}")
                elif nal_type == 5:
                    self.log_message(f"IDR NAL unit detected for Frame ID: {frame_id}")
                elif nal_type == 1:
                    print(f"P-frame NAL unit detected for Frame ID: {frame_id}")
                elif nal_type == 0:
                    self.log_message(f"B-frame NAL unit detected for Frame ID: {frame_id}")
                else:
                    pass

                # write to file
                if nal_type in [0, 1, 7, 8]:
                    self.output_file.write(packet_bytes)
                    self.output_file.flush()
                elif nal_type == 5:
                    # IDR frame (NAL type 5) - write to file
                    self.output_file.write(current_sps_pps)
                    self.output_file.write(packet_bytes)
                    self.output_file.flush()

            # Only send if sending is enabled
            if self.is_sending:
                self.network_worker.enqueue_packet(packet_bytes)

    def log_message(self, message):
        timestamp = QDateTime.currentDateTime().toString("[hh:mm:ss.zzz]")
        full_message = f"{timestamp} {message}"

        self.console_log.append(full_message)

        # Auto-scroll to bottom
        cursor = self.console_log.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.console_log.setTextCursor(cursor)

    def toggle_capture(self):
        self.is_capturing = not self.is_capturing

        if self.is_capturing:
            self.camera.init_camera()
            self.capture_button.setText("Stop Capture")
            self.capture_button.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;  /* Red */
                    color: white;
                    border: none;
                    padding: 8px;
                    font-size: 12pt;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #f44335;
                }
            """)

            # Add timestamp to H264_DUMP filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{H264_DUMP}_{timestamp}.h264"
            self.output_file = open(output_filename, 'wb')
            self.log_message("Capture started - camera active")
        else:
            # Properly release camera resources
            self.camera.stop()
            self.output_file.flush()
            self.output_file.close()

            self.capture_button.setText("Start Capture")
            self.capture_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;  /* Green */
                    color: white;
                    border: none;
                    padding: 8px;
                    font-size: 12pt;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            self.log_message("Capture stopped - camera released")

    def toggle_sending(self):
        self.is_sending = not self.is_sending
        if self.is_sending:
            self.sending_button.setText("Stop Sending")
            self.sending_button.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;  /* Red */
                    color: white;
                    border: none;
                    padding: 8px;
                    font-size: 12pt;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #f44335;
                }
            """)
            self.log_message("Sending enabled")
        else:
            self.sending_button.setText("Start Sending")
            self.sending_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px;
                    font-size: 12pt;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            self.log_message("Sending disabled")

    def closeEvent(self, event):
        self.camera.stop()
        self.output_container.close()
        self.network_worker.stop()
        event.accept()
        print("CameraClient closed.")

