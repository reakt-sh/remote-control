import cv2
import av
import zmq
import datetime
import struct
import os
import uuid
import json
import asyncio
import logging
from fractions import Fraction

from loguru import logger
from picamera2 import Picamera2
from libcamera import controls

from globals import *
from network_worker_ws import NetworkWorkerWS
from network_worker_quic import NetworkWorkerQUIC
from sensor.telemetry import Telemetry
from sensor.imu import IMU
from encoder import Encoder

class RPi5Client:
    def __init__(self):
        self.train_client_id = self.initialize_train_client_id()
        self.init_logging()
        self.init_network()
        self.create_dump_file()
        self.write_to_file = False  # Initially set to False

        self.is_capturing = True   # Track capture state
        self.is_sending = False    # Start with sending disabled

        # Camera setup
        self.video_source = self.init_pi_camera()
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
        logger.info(f"TrainClient ID initialized: {client_id}")
        return client_id

    def init_logging(self):
        # Configure logging to file and console
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('rpi5_client.log'),
                logging.StreamHandler()
            ]
        )

    def init_pi_camera(self):
        # Initialize the Pi-specific camera class
        return PiCameraWrapper()

    def create_dump_file(self):
        # Add timestamp to H264_DUMP filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Ensure directory exists
        dump_dir = os.path.dirname(H264_DUMP)
        if dump_dir and not os.path.exists(dump_dir):
            os.makedirs(dump_dir, exist_ok=True)
        output_filename = f"{H264_DUMP}_{timestamp}.h264"
        self.output_file = open(output_filename, 'wb')

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
        logger.error(f"QUIC connection failed: {error}")

    def on_quic_closed(self):
        logger.info("QUIC connection closed")

    def on_new_command(self, payload):
        message = json.loads(payload.decode('utf-8'))
        logger.info(f"Received command: {message}")
        if message['instruction'] == 'CHANGE_TARGET_SPEED':
            self.target_speed = message['target_speed']
            logger.info(f"Target speed changed to: {self.target_speed}")
        elif message['instruction'] == 'STOP_SENDING_DATA':
            if self.is_sending:
                self.toggle_sending()
        elif message['instruction'] == 'START_SENDING_DATA':
            logger.info("Received START_SENDING_DATA instruction")
            if not self.is_sending:
                self.toggle_sending()
        else:
            logger.warning(f"Unknown Instruction: {message['instruction']}")

    def on_data_received_quic(self, data):
        logger.info(f"QUIC data received: {data}")

    def on_new_frame(self, frame_id, frame):
        # Encode frame
        self.encoder.encode_frame(frame_id, frame, logger.info)

    def on_telemetry_data(self, data):
        # Process telemetry data
        logger.info(f"Telemetry data: {data}")

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
        logger.info(f"IMU Data: {data}")

    def on_encoded_frame(self, frame_id, encoded_bytes):
        if self.write_to_file:
            self.output_file.write(encoded_bytes)
            self.output_file.flush()
        # Only send if sending is enabled
        if self.is_sending:
            self.network_worker_quic.enqueue_frame(frame_id, encoded_bytes)
            self.telemetry.notify_new_frame_processed()

    def toggle_capture(self):
        self.is_capturing = not self.is_capturing

        if self.is_capturing:
            self.video_source.init_capture()
            self.telemetry.start()
            self.imu.start()
            logger.info("Capture started - camera active")
        else:
            # Properly release camera resources
            self.video_source.stop()
            self.telemetry.stop()
            self.imu.stop()
            logger.info("Capture stopped - camera released")

    def toggle_sending(self):
        self.is_sending = not self.is_sending
        if self.is_sending:
            logger.info("Sending enabled")
        else:
            logger.info("Sending disabled")

    def toggle_write_to_file(self):
        self.write_to_file = not self.write_to_file
        if self.write_to_file:
            logger.info("Write to file enabled")
        else:
            logger.info("Write to file disabled")

    def close(self):
        self.video_source.stop()
        self.encoder.close()
        self.network_worker_ws.stop()
        self.network_worker_quic.stop()
        self.output_file.close()
        logger.info("RPi5 Headless Client closed.")

class PiCameraWrapper(QObject):
    frame_ready = pyqtSignal(object, object)  # Emits the frame (numpy array) and frame count

    def __init__(self, parent=None):
        super().__init__(parent)
        self.picam2 = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.capture_frame)
        self.frame_count = 0
        self.start_time = None

    def init_capture(self):
        try:
            # Initialize Pi Camera
            self.picam2 = Picamera2()
            
            # Configure camera (adjust these settings based on your needs)
            config = self.picam2.create_preview_configuration(
                main={"size": (1920, 1080)},  # Adjust resolution as needed
                transform=libcamera.Transform(hflip=1, vflip=1)  # Flip if needed
            )
            self.picam2.configure(config)
            
            # Optional camera controls
            self.picam2.set_controls({
                "AfMode": controls.AfModeEnum.Continuous,  # Continuous autofocus
                "AwbMode": controls.AwbModeEnum.Auto,      # Auto white balance
                "ExposureTime": 10000,                    # Exposure time in microseconds
            })
            
            self.picam2.start()
            
            # Get camera properties
            self.width = self.picam2.camera_properties['PixelArraySize'][0]
            self.height = self.picam2.camera_properties['PixelArraySize'][1]
            self.fps = 30  # Default, can be adjusted in config
            
            logger.info(f"Camera Resolution: {self.width}x{self.height}")
            logger.info(f"Camera FPS: {self.fps}")
            
            self.frame_count = 0
            self.start_time = datetime.now().timestamp()
            self.timer.start(int(1000 / self.fps))  # Convert FPS to milliseconds
            
        except Exception as e:
            logger.error(f"Could not initialize Raspberry Pi camera: {str(e)}")
            raise RuntimeError(f"Camera initialization failed: {str(e)}")

    def stop(self):
        self.timer.stop()
        if self.picam2:
            self.picam2.stop()
            self.picam2.close()
            self.picam2 = None

    def capture_frame(self):
        if self.picam2:
            try:
                # Capture array from Pi camera
                frame = self.picam2.capture_array("main")
                
                # Convert to BGR format (OpenCV default) if needed
                if frame.dtype == np.float32:
                    frame = (frame * 255).astype(np.uint8)
                if len(frame.shape) == 2:  # If grayscale
                    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                elif frame.shape[2] == 4:  # If RGBA
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                elif frame.shape[2] == 3:  # If RGB
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                self.frame_count += 1
                self.frame_ready.emit(self.frame_count, frame)

            except Exception as e:
                logger.error(f"Error capturing frame: {str(e)}")

    def set_speed(self, speed):
        # This can be used to adjust camera settings based on speed if needed
        pass

if __name__ == "__main__":
    from PyQt5.QtCore import QCoreApplication
    import sys
    
    # Initialize QCoreApplication for event loop
    app = QCoreApplication(sys.argv)
    
    # Create and start the client
    client = RPi5HeadlessClient()
    
    # Set up clean exit
    def shutdown():
        client.close()
        app.quit()
    
    # Handle SIGTERM and SIGINT for proper shutdown
    import signal
    signal.signal(signal.SIGTERM, lambda *args: shutdown())
    signal.signal(signal.SIGINT, lambda *args: shutdown())
    
    # Start the application
    sys.exit(app.exec_())