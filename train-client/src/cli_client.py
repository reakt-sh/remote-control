import cv2
import datetime
import struct
import os
import uuid
import json

from PyQt5.QtCore import QThread, QDateTime
from loguru import logger

from globals import *
from network_worker_ws import NetworkWorkerWS
from network_worker_quic import NetworkWorkerQUIC
from sensor.camera import Camera
from sensor.telemetry import Telemetry
from sensor.imu import IMU
from encoder import Encoder
from sensor.file_processor import FileProcessor

class CLIClient(QThread):
    def __init__(self):
        super().__init__()
        self.train_client_id = self.initialize_train_client_id()
        self.init_network()
        self.create_dump_file()
        self.write_to_file = False  # Initially set to False

        self.is_capturing = True   # Track capture state
        self.is_sending = False    # Start with sending disabled

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
        self._running = True

    def run(self):
        logger.info("TrainClientHeadless thread started.")
        try:
            while self._running:
                self.msleep(100)  # Sleep for 100ms to keep the thread alive
        except Exception as e:
            logger.error(f"Exception in TrainClientHeadless thread: {e}")
        finally:
            self.close()

    def initialize_train_client_id(self):
        client_id = str(uuid.uuid4())
        logger.info(f"TrainClient ID initialized: {client_id}")
        return client_id

    def create_dump_file(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dump_dir = os.path.dirname(H264_DUMP)
        if (dump_dir and not os.path.exists(dump_dir)):
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
            self.target_speed = max(self.target_speed, 15)
        elif message['instruction'] == 'POWER_OFF':
            logger.info("Found instruction POWER_OFF")
            self.telemetry.set_status(TRAIN_STATUS["POWER_OFF"])
            self.target_speed = 0
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

    def on_new_frame(self, frame_id, frame, width, height):
        # Encode frame
        self.encoder.encode_frame(frame_id, frame, width, height, self.log_message)

    def on_telemetry_data(self, data):
        self.log_message(data)
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
        imu_message = f"IMU Data: {data}"
        self.log_message(imu_message)

    def on_encoded_frame(self, frame_id, encoded_bytes):
        if self.write_to_file:
            self.output_file.write(encoded_bytes)
            self.output_file.flush()
        if self.is_sending:
            self.network_worker_quic.enqueue_frame(frame_id, encoded_bytes)
            self.telemetry.notify_new_frame_processed()

    def log_message(self, message):
        timestamp = QDateTime.currentDateTime().toString("[hh:mm:ss.zzz]")
        full_message = f"{timestamp} {message}"
        logger.info(full_message)

    def toggle_capture(self):
        self.is_capturing = not self.is_capturing
        if self.is_capturing:
            self.video_source.init_capture()
            self.telemetry.start()
            self.imu.start()
            self.log_message("Capture started - camera active")
        else:
            self.video_source.stop()
            self.telemetry.stop()
            self.imu.stop()
            self.log_message("Capture stopped - camera released")

    def toggle_sending(self):
        self.is_sending = not self.is_sending
        if self.is_sending:
            self.log_message("Sending enabled")
        else:
            self.log_message("Sending disabled")

    def toggle_write_to_file(self):
        self.write_to_file = not self.write_to_file
        if self.write_to_file:
            self.log_message("Write to file enabled")
        else:
            self.log_message("Write to file disabled")

    def close(self):
        self._running = False
        self.video_source.stop()
        self.encoder.close()
        self.network_worker_ws.stop()
        self.network_worker_quic.stop()
        self.output_file.close()
        logger.info("TrainClientHeadless closed.")