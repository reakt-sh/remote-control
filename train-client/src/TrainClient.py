import cv2
import av
import zmq
import datetime
import struct
import os
from fractions import Fraction
from PyQt5.QtWidgets import QMainWindow, QLabel, QGridLayout, QVBoxLayout, QWidget, QTextEdit, QPushButton
from PyQt5.QtGui import QImage, QPixmap, QTextCursor
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtCore import QDateTime

from globals import *
from NetworkWorker import NetworkWorker
from sensor.Camera import Camera
from sensor.Telemetry import Telemetry
from sensor.IMU import IMU
from Encoder import Encoder

class TrainClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_network()
        self.create_dump_file()
        self.write_to_file = False  # Initially set to False


        self.is_capturing = True   # Track capture state
        self.is_sending = False    # Start with sending disabled

        # Camera setup
        self.camera = Camera()
        self.camera.frame_ready.connect(self.on_new_frame)
        self.camera.init_camera()

        # Telemetry setup
        self.telemetry = Telemetry()
        self.telemetry.telemetry_ready.connect(self.on_telemetry_data)
        self.telemetry.start()

        # IMU setup
        self.imu = IMU()
        self.imu.imu_ready.connect(self.on_imu_data)
        self.imu.start()

        # Encoder setup
        self.encoder = Encoder()
        self.encoder.encode_ready.connect(self.on_encoded_frame)

    def create_dump_file(self):
        # Add timestamp to H264_DUMP filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Ensure directory exists
        dump_dir = os.path.dirname(H264_DUMP)
        if (dump_dir and not os.path.exists(dump_dir)):
            os.makedirs(dump_dir, exist_ok=True)
        output_filename = f"{H264_DUMP}_{timestamp}.h264"
        self.output_file = open(output_filename, 'wb')

    def init_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.setWindowTitle("Train Client")
        self.setGeometry(START_X, START_Y, START_X + WINDOW_WIDTH, START_Y + WINDOW_HEIGHT)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        # Create an image label to display the camera feed
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)

        # Create console log widget
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

        # Create the toggle write-to-file button
        self.write_button = QPushButton("Enable Write")
        self.write_button.setMinimumWidth(BUTTON_WIDTH)
        self.write_button.setMaximumWidth(BUTTON_WIDTH)
        self.write_button.setStyleSheet("""
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
        self.write_button.clicked.connect(self.toggle_write_to_file)

        # Create VBox layout for the buttons
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.capture_button)
        button_layout.addWidget(self.sending_button)
        button_layout.addWidget(self.write_button)
        button_layout.addStretch()  # This adds spacing at the bottom

        layout = QGridLayout()
        layout.addWidget(self.image_label, 0, 0)
        layout.addLayout(button_layout, 0, 1)
        layout.addWidget(self.console_log, 1, 0, 1, 2)

        self.central_widget.setLayout(layout)

    def init_network(self):
        self.network_worker = NetworkWorker()
        self.network_worker.packet_sent.connect(self.on_packet_sent)

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
        self.encoder.encode_frame(frame_id, frame, self.log_message)

    def on_telemetry_data(self, data):
        # Process telemetry data
        telemetry_message = f"Telemetry Data: {data}"
        self.log_message(telemetry_message)

    def on_imu_data(self, data):
        # Process IMU data
        imu_message = f"IMU Data: {data}"
        self.log_message(imu_message)

    def on_encoded_frame(self, encoded_bytes):
        if self.write_to_file:
            self.output_file.write(encoded_bytes)
            self.output_file.flush()
        # Only send if sending is enabled
        if self.is_sending:
            encoded_bytes = struct.pack('B', PACKET_TYPE["video"]) + encoded_bytes
            self.network_worker.enqueue_packet(encoded_bytes)

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
            self.telemetry.start()
            self.imu.start()
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
            self.log_message("Capture started - camera active")
        else:
            # Properly release camera resources
            self.camera.stop()
            self.telemetry.stop()
            self.imu.stop()

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
            self.network_worker.start()
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
            self.network_worker.stop()
            self.log_message("Sending disabled")


    def toggle_write_to_file(self):
        self.write_to_file = not self.write_to_file
        if self.write_to_file:
            self.write_button.setText("Disable Write")
            self.write_button.setStyleSheet("""
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
            self.log_message("Write to file enabled")
        else:
            self.write_button.setText("Enable Write")
            self.write_button.setStyleSheet("""
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
            self.log_message("Write to file disabled")

    def closeEvent(self, event):
        self.camera.stop()
        self.encoder.close()
        self.network_worker.stop()
        self.output_file.close()
        event.accept()
        print("CameraClient closed.")

