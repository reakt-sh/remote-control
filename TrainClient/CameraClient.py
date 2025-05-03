import cv2
import av
import zmq
from fractions import Fraction
from PyQt5.QtWidgets import QMainWindow, QLabel, QGridLayout, QVBoxLayout, QWidget, QTextEdit, QPushButton
from PyQt5.QtGui import QImage, QPixmap, QTextCursor
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtCore import QDateTime

from globals import *
from NetworkWorker import NetworkWorker

# Initialize output container (raw H.264 stream)
output_file = open(H264_DUMP, 'wb')

class CameraClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_camera()
        self.init_encoder()
        self.init_network()

        self.is_capturing = True  # Track capture state

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

        # Create the toggle button
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

        # Create VBox layout for the button
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.capture_button)
        button_layout.addStretch()  # This adds spacing at the bottom


        layout = QGridLayout()
        layout.addWidget(self.image_label, 0, 0)
        layout.addLayout(button_layout, 0, 1)
        layout.addWidget(self.console_log, 1, 0, 1, 2)

        self.central_widget.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(FRAME_RATE)  # ~30 FPS

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


        # Ensure we have a valid FPS (some cameras return 0)
        if self.fps <= 0:
            self.fps = FRAME_RATE  # Default to 30 FPS

        self.frame_count = 0  # Initialize frame count
        self.start_time = cv2.getTickCount()  # Initialize start time

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

        # After creating the stream, extract headers
        extradata = self.stream.codec_context.extradata

        # Write headers before any video frames
        if extradata:
            output_file.write(extradata)
            output_file.flush()
            print(f"Extradata size: {len(extradata)} bytes")
            print(f"First 16 bytes of extradata: {extradata[:16].hex(' ')}")

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
            self.frame_count += 1
            elapsed_time = (cv2.getTickCount() - self.start_time) / cv2.getTickFrequency()
            current_fps = self.frame_count / elapsed_time


            # Overlay resolution and FPS on the frame
            text_res = f"Resolution: {self.width}x{self.height}"
            text_fps = f"FPS: {current_fps:.1f}"
            text_frame_id = f"Frame ID: {self.frame_count}"

            if self.frame_count % FRAME_RATE == 0:  # Log every 30 frames
                self.log_message(f"Frame ID: {self.frame_count}")

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

            # Convert to RGB for PyQt display
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.image_label.setPixmap(QPixmap.fromImage(qt_image))

            # Encode frame
            self.encode_frame(self.frame_count, frame)

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
                    output_file.write(packet_bytes)
                    output_file.flush()
                elif nal_type == 5:
                    # IDR frame (NAL type 5) - write to file
                    output_file.write(current_sps_pps)
                    output_file.write(packet_bytes)
                    output_file.flush()

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
            self.init_camera()
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
            self.timer.start(FRAME_RATE)
            self.log_message("Capture started - camera active")
        else:
            # Properly release camera resources
            self.timer.stop()
            self.cap.release()
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

    def closeEvent(self, event):
        self.timer.stop()
        self.cap.release()
        self.output_container.close()
        self.network_worker.stop()
        event.accept()
        output_file.close()
        print("CameraClient closed.")

