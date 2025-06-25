import cv2
import av
import zmq
import datetime
import struct
import os
import uuid
import json
import asyncio

from fractions import Fraction
from PyQt5.QtWidgets import QMainWindow, QLabel, QGridLayout, QVBoxLayout, QWidget, QTextEdit, QPushButton
from PyQt5.QtGui import QImage, QPixmap, QTextCursor, QIcon
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, pyqtSlot, QSize
from PyQt5.QtCore import QDateTime
from loguru import logger

from globals import *
from network_worker_ws import NetworkWorkerWS
from network_worker_quic import NetworkWorkerQUIC
from sensor.camera import Camera
from sensor.telemetry import Telemetry
from sensor.imu import IMU
from encoder import Encoder
from sensor.file_processor import FileProcessor

class TrainClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.train_client_id = self.initialize_train_client_id()
        self.init_ui()
        self.init_network()
        self.create_dump_file()
        self.write_to_file = False  # Initially set to False


        self.is_capturing = True   # Track capture state
        self.is_sending = False    # Start with sending disabled

        # # Camera setup
        # self.video_source = Camera()
        # self.video_source.frame_ready.connect(self.on_new_frame)
        # self.video_source.init_capture()

        # FileProcessor setup
        self.video_source = FileProcessor()
        self.video_source.frame_ready.connect(self.on_new_frame)
        self.video_source.init_capture()

        # Telemetry setup
        self.telemetry = Telemetry(self.train_client_id)
        self.telemetry.telemetry_ready.connect(self.on_telemetry_data)
        self.telemetry.start()

        # IMU setup
        self.imu = IMU()
        self.imu.imu_ready.connect(self.on_imu_data)
        self.imu.start()

        # Encoder setup
        self.encoder = Encoder()
        self.encoder.encode_ready.connect(self.on_encoded_frame)

        self.target_speed = 60

    def initialize_train_client_id(self):
        client_id = str(uuid.uuid4())
        print(f"TrainClient ID initialized: {client_id}")
        return client_id

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

        # Store styles as instance variables for reuse
        self.button_style = """
            QPushButton {
                background-color: #2d89ef;
                color: #fff;
                border: none;
                border-radius: 18px;
                padding: 10px 0 10px 36px;  /* left padding for icon space */
                font-size: 13pt;
                min-width: 175px;
                font-weight: 600;
                qproperty-iconSize: 24px 24px;
                text-align: left; /* optional: aligns text to the left */
            }
            QPushButton:hover {
                background-color: #1b5fa7;
                color: #e3e3e3;
            }
            QPushButton:pressed {
                background-color: #174c88;
            }
            QPushButton:disabled {
                background-color: #b0b0b0;
                color: #f0f0f0;
            }
        """

        icon_dir = os.path.join(os.path.dirname(__file__), "icons")

        # Capture button (blue)
        self.capture_button = QPushButton("  Stop Capture")
        self.capture_button.setMinimumWidth(BUTTON_WIDTH)
        self.capture_button.setMaximumWidth(BUTTON_WIDTH)
        self.capture_button_style = self.button_style
        self.capture_button_style_red = self.button_style.replace("#2d89ef", "#f44336").replace("#1b5fa7", "#f44335").replace("#174c88", "#b71c1c")
        self.capture_button.setStyleSheet(self.capture_button_style_red)
        self.capture_button.setIcon(QIcon(os.path.join(icon_dir, "video-solid.png")))  # Font Awesome "video"
        self.capture_button.setIconSize(QSize(24, 24))
        self.capture_button.clicked.connect(self.toggle_capture)

        # Sending button (green)
        self.sending_button = QPushButton("  Start Sending")
        self.sending_button.setMinimumWidth(BUTTON_WIDTH)
        self.sending_button.setMaximumWidth(BUTTON_WIDTH)
        self.sending_button_style = self.button_style.replace("#2d89ef", "#43b581").replace("#1b5fa7", "#2e8c5a").replace("#174c88", "#256b45")
        self.sending_button_style_red = self.button_style.replace("#2d89ef", "#f44336").replace("#1b5fa7", "#f44335").replace("#174c88", "#b71c1c")
        self.sending_button.setStyleSheet(self.sending_button_style)
        self.sending_button.setIcon(QIcon(os.path.join(icon_dir, "paper-plane-solid.png")))  # Font Awesome "paper-plane"
        self.sending_button.setIconSize(QSize(24, 24))
        self.sending_button.clicked.connect(self.toggle_sending)

        # Write button (orange)
        self.write_button = QPushButton("  Enable Write")
        self.write_button.setMinimumWidth(BUTTON_WIDTH)
        self.write_button.setMaximumWidth(BUTTON_WIDTH)
        self.write_button_style = self.button_style.replace("#2d89ef", "#ff9800").replace("#1b5fa7", "#e68900").replace("#174c88", "#b36b00")
        self.write_button_style_red = self.button_style.replace("#2d89ef", "#f44336").replace("#1b5fa7", "#f44335").replace("#174c88", "#b71c1c")
        self.write_button.setStyleSheet(self.write_button_style)
        self.write_button.setIcon(QIcon(os.path.join(icon_dir, "file-arrow-down-solid.png")))  # Font Awesome "file-arrow-down"
        self.write_button.setIconSize(QSize(24, 24))
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
        self.network_worker_ws = NetworkWorkerWS(self.train_client_id)
        self.network_worker_ws.process_command.connect(self.on_new_command)
        self.network_worker_ws.start()

        self.network_worker_quic = NetworkWorkerQUIC(self.train_client_id)
        self.network_worker_quic.connection_established.connect(self.on_quic_connected)
        self.network_worker_quic.connection_failed.connect(self.on_quic_failed)
        self.network_worker_quic.connection_closed.connect(self.on_quic_closed)
        self.network_worker_quic.data_received.connect(self.on_data_received_quic)
        self.network_worker_quic.process_command.connect(self.on_new_command)
        self.network_worker_quic.start()

    def on_quic_connected(self):
        logger.info("QUIC connection established")

    def on_quic_failed(self, error):
        logger.info(f"QUIC connection failed: {error}")

    def on_quic_closed(self):
        logger.info("QUIC connection closed")

    def on_new_command(self, payload):
        message = json.loads(payload.decode('utf-8'))
        logger.info(f"{message}")
        if message['instruction'] == 'CHANGE_TARGET_SPEED':
            self.target_speed = message['target_speed']
        elif message['instruction'] == 'STOP_SENDING_DATA':
            if self.is_sending:
                self.toggle_sending()
        elif message['instruction'] == 'START_SENDING_DATA':
            logger.info("Found instruction START_SENDING_DATA")
            if not self.is_sending:
                self.toggle_sending()
        elif message['instruction'] == 'POWER_ON':
            logger.info("Found instruction POWER_ON")
            self.telemetry.set_status(TRAIN_STATUS["POWER_ON"])
            self.target_speed = max(self.target_speed, 15)  # Ensure minimum speed on power on
        elif message['instruction'] == 'POWER_OFF':
            logger.info("Found instruction POWER_OFF")
            self.telemetry.set_status(TRAIN_STATUS["POWER_OFF"])
            self.target_speed = 0  # Set speed to 0 on power off
        elif message['instruction'] == 'CHANGE_DIRECTION':
            if message['direction'] == 'FORWARD':
                logger.info("Found instruction CHANGE_DIRECTION: FORWARD")
                self.video_source.set_direction(DIRECTION["FORWARD"])
                self.telemetry.set_direction(DIRECTION["FORWARD"])
            elif message['direction'] == 'BACKWARD':
                logger.info("Found instruction CHANGE_DIRECTION: BACKWARD")
                self.video_source.set_direction(DIRECTION["BACKWARD"])
                self.telemetry.set_direction(DIRECTION["BACKWARD"])
            else:
                logger.warning(f"Unknown direction in CHANGE_DIRECTION: {message['direction']}")
        else:
            logger.warning(f"Unknown Instruction from command:  {message['instruction']}")

    def on_data_received_quic(self, data):
        logger.info(f"QUIC data received: {data}")

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
        self.log_message(data)

        # Only send if sending is enabled
        if self.is_sending:
            packet_data = json.dumps(data).encode('utf-8')
            packet = struct.pack("B", PACKET_TYPE["telemetry"]) + packet_data
            self.network_worker_quic.enqueue_stream_packet(packet)


            current_speed = self.telemetry.get_speed()
            delta = 0
            if current_speed > self.target_speed:
                delta = 0 - min(5, current_speed - self.target_speed)
            elif current_speed < self.target_speed:
                delta = min(5, self.target_speed - current_speed)
            else:
                delta = 0

            self.video_source.set_speed(current_speed + delta)
            self.telemetry.set_speed(current_speed + delta)

    def on_imu_data(self, data):
        # Process IMU data
        imu_message = f"IMU Data: {data}"
        self.log_message(imu_message)

    def on_encoded_frame(self, frame_id, encoded_bytes):
        if self.write_to_file:
            self.output_file.write(encoded_bytes)
            self.output_file.flush()
        # Only send if sending is enabled
        if self.is_sending:
            self.network_worker_quic.enqueue_frame(frame_id, encoded_bytes)
            self.telemetry.notify_new_frame_processed()
            # print("Encoded frame to network worker quic enqueue, length:", len(encoded_bytes))

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
            self.video_source.init_capture()
            self.telemetry.start()
            self.imu.start()
            self.capture_button.setText("  Stop Capture")
            self.capture_button.setStyleSheet(self.capture_button_style_red)
            self.log_message("Capture started - camera active")
        else:
            # Properly release camera resources
            self.video_source.stop()
            self.telemetry.stop()
            self.imu.stop()

            self.capture_button.setText("  Start Capture")
            self.capture_button.setStyleSheet(self.capture_button_style)
            self.log_message("Capture stopped - camera released")

    def toggle_sending(self):
        self.is_sending = not self.is_sending
        if self.is_sending:
            self.sending_button.setText("  Stop Sending")
            self.sending_button.setStyleSheet(self.sending_button_style_red)
            self.log_message("Sending enabled")
        else:
            self.sending_button.setText("  Start Sending")
            self.sending_button.setStyleSheet(self.sending_button_style)
            self.log_message("Sending disabled")


    def toggle_write_to_file(self):
        self.write_to_file = not self.write_to_file
        if self.write_to_file:
            self.write_button.setText("  Disable Write")
            self.write_button.setStyleSheet(self.write_button_style_red)
            self.log_message("Write to file enabled")
        else:
            self.write_button.setText("  Enable Write")
            self.write_button.setStyleSheet(self.write_button_style)
            self.log_message("Write to file disabled")

    def closeEvent(self, event):
        self.video_source.stop()
        self.encoder.close()
        self.network_worker_ws.stop()
        self.network_worker_quic.stop()
        self.output_file.close()
        event.accept()
        print("CameraClient closed.")

