from PyQt5.QtWidgets import QMainWindow, QLabel, QGridLayout, QVBoxLayout, QWidget, QTextEdit, QPushButton
from PyQt5.QtGui import QImage, QPixmap, QIcon, QTextCursor
from PyQt5.QtCore import Qt, QSize, QDateTime
import os
import cv2
import numpy as np
from sensor.file_processor import FileProcessor
from sensor.camera import Camera
from base_client import BaseClient
from globals import *

class TrainClient(BaseClient, QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        BaseClient.__init__(self, video_source=FileProcessor(), has_motor=False)
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.setWindowTitle("Train Client")
        self.setGeometry(START_X, START_Y, START_X + WINDOW_WIDTH, START_Y + WINDOW_HEIGHT)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)  # Fix window size
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        # Set fixed size for video display area
        video_display_width = WINDOW_WIDTH - BUTTON_WIDTH - 200  # Account for button width and margins
        video_display_height = int(WINDOW_HEIGHT * 0.8)  # Use 80% of window height for video
        self.image_label.setFixedSize(video_display_width, video_display_height)
        self.image_label.setStyleSheet("border: 1px solid #444; background-color: #2a2a2a;")
        self.image_label.setScaledContents(True)  # Enable scaling

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

        self.button_style = """
            QPushButton {
                background-color: #2d89ef;
                color: #fff;
                border: none;
                border-radius: 18px;
                padding: 10px 0 10px 36px;
                font-size: 13pt;
                min-width: 175px;
                font-weight: 600;
                qproperty-iconSize: 24px 24px;
                text-align: left;
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
        self.capture_button.setIcon(QIcon(os.path.join(icon_dir, "video-solid.png")))
        self.capture_button.setIconSize(QSize(24, 24))
        self.capture_button.clicked.connect(self.toggle_capture)

        # Sending button (green)
        self.sending_button = QPushButton("  Start Sending")
        self.sending_button.setMinimumWidth(BUTTON_WIDTH)
        self.sending_button.setMaximumWidth(BUTTON_WIDTH)
        self.sending_button_style = self.button_style.replace("#2d89ef", "#43b581").replace("#1b5fa7", "#2e8c5a").replace("#174c88", "#256b45")
        self.sending_button_style_red = self.button_style.replace("#2d89ef", "#f44336").replace("#1b5fa7", "#f44335").replace("#174c88", "#b71c1c")
        self.sending_button.setStyleSheet(self.sending_button_style)
        self.sending_button.setIcon(QIcon(os.path.join(icon_dir, "paper-plane-solid.png")))
        self.sending_button.setIconSize(QSize(24, 24))
        self.sending_button.clicked.connect(self.toggle_sending)

        # Write button (orange)
        self.write_button = QPushButton("  Enable Write")
        self.write_button.setMinimumWidth(BUTTON_WIDTH)
        self.write_button.setMaximumWidth(BUTTON_WIDTH)
        self.write_button_style = self.button_style.replace("#2d89ef", "#ff9800").replace("#1b5fa7", "#e68900").replace("#174c88", "#b36b00")
        self.write_button_style_red = self.button_style.replace("#2d89ef", "#f44336").replace("#1b5fa7", "#f44335").replace("#174c88", "#b71c1c")
        self.write_button.setStyleSheet(self.write_button_style)
        self.write_button.setIcon(QIcon(os.path.join(icon_dir, "file-arrow-down-solid.png")))
        self.write_button.setIconSize(QSize(24, 24))
        self.write_button.clicked.connect(self.toggle_write_to_file)

        # Video source switch button (purple)
        self.source_button = QPushButton("  Camera Source")
        self.source_button.setMinimumWidth(BUTTON_WIDTH)
        self.source_button.setMaximumWidth(BUTTON_WIDTH)
        self.source_button_style = self.button_style.replace("#2d89ef", "#9c27b0").replace("#1b5fa7", "#6d1b7b").replace("#174c88", "#4a0d52")
        self.source_button.setStyleSheet(self.source_button_style)
        camera_icon_path = os.path.join(icon_dir, "camera-solid.png")
        if os.path.exists(camera_icon_path):
            self.source_button.setIcon(QIcon(camera_icon_path))
        self.source_button.setIconSize(QSize(24, 24))
        self.source_button.clicked.connect(self.toggle_video_source)
        self.using_file_source = True

        # Create VBox layout for the buttons
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.capture_button)
        button_layout.addWidget(self.sending_button)
        button_layout.addWidget(self.write_button)
        button_layout.addWidget(self.source_button)
        button_layout.addStretch()

        layout = QGridLayout()
        layout.addWidget(self.image_label, 0, 0)
        layout.addLayout(button_layout, 0, 1)
        layout.addWidget(self.console_log, 1, 0, 1, 2)

        self.central_widget.setLayout(layout)

    def on_new_frame(self, frame_id, frame, width, height):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        
        # Get the fixed size of the image label
        label_width = self.image_label.width()
        label_height = self.image_label.height()
        
        # Calculate scaling to fit within label while maintaining aspect ratio
        scale_w = label_width / w
        scale_h = label_height / h
        scale = min(scale_w, scale_h)  # Use smaller scale to ensure it fits
        
        # Calculate new dimensions
        new_width = int(w * scale)
        new_height = int(h * scale)
        
        # Resize the frame
        resized_image = cv2.resize(rgb_image, (new_width, new_height))
        
        # Create a black background image with the label dimensions
        background = np.zeros((label_height, label_width, 3), dtype=np.uint8)
        
        # Calculate position to center the resized video
        x_offset = (label_width - new_width) // 2
        y_offset = (label_height - new_height) // 2
        
        # Place the resized video on the black background
        background[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized_image
        
        # Convert to QImage
        bytes_per_line = 3 * label_width
        qt_image = QImage(background.data, label_width, label_height, bytes_per_line, QImage.Format_RGB888)
        
        # Create pixmap and set it to the label
        pixmap = QPixmap.fromImage(qt_image)
        self.image_label.setPixmap(pixmap)
        
        super().on_new_frame(frame_id, frame, width, height)

    def toggle_capture(self):
        super().toggle_capture()
        self.capture_button.setText("  Stop Capture" if self.is_capturing else "  Start Capture")
        self.capture_button.setStyleSheet(self.capture_button_style_red if self.is_capturing else self.button_style)

    def toggle_sending(self):
        super().toggle_sending()
        self.sending_button.setText("  Stop Sending" if self.is_sending else "  Start Sending")
        self.sending_button.setStyleSheet(self.sending_button_style_red if self.is_sending else self.sending_button_style)

    def toggle_write_to_file(self):
        super().toggle_write_to_file()
        self.write_button.setText("  Disable Write" if self.write_to_file else "  Enable Write")
        self.write_button.setStyleSheet(self.write_button_style_red if self.write_to_file else self.write_button_style)

    def toggle_video_source(self):
        # Switch between FileProcessor and Camera
        if self.using_file_source:
            new_source = Camera()
            self.source_button.setText("  File Source")
        else:
            new_source = FileProcessor()
            self.source_button.setText("  Camera Source")
        self.switch_video_source(new_source)
        self.using_file_source = not self.using_file_source

    def log_message(self, message):
        super().log_message(message)
        self.console_log.append(f"{QDateTime.currentDateTime().toString('[hh:mm:ss.zzz]')} {message}")
        cursor = self.console_log.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.console_log.setTextCursor(cursor)

    def update_speed(self, speed):
        self.video_source.set_speed(speed)
        self.telemetry.set_speed(speed)

    def on_power_on(self):
        self.update_speed(self.target_speed)

    def on_power_off(self):
        self.update_speed(0)

    def on_change_direction(self, direction):
        pass  # No additional logic for TrainClient

    def closeEvent(self, event):
        self.close()
        event.accept()