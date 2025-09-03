from abc import ABC, abstractmethod
import datetime
import os
import uuid
import json
import struct
from PyQt5.QtCore import QThread, QDateTime
from loguru import logger
from globals import *
from network_worker_ws import NetworkWorkerWS
from network_worker_quic import NetworkWorkerQUIC
from network_worker_mqtt import NetworkWorkerMqtt
from networkspeed import NetworkSpeed
from sensor.telemetry import Telemetry
from sensor.imu import IMU
from encoder import Encoder
from PyQt5.QtCore import QObject

# Fix for metaclass conflict with QObject
class QABCMeta(type(QObject), type(ABC)):
    pass

class BaseClient(ABC, metaclass=QABCMeta):
    def __init__(self, video_source, has_motor=False):
        super().__init__()
        self.train_client_id = self.initialize_train_client_id()
        self.video_source = video_source
        self.has_motor = has_motor
        self.write_to_file = False
        self.is_capturing = True
        self.is_sending = False
        self.target_speed = 60
        self._running = True

        # Initialize components
        self.telemetry = Telemetry(self.train_client_id)
        self.imu = IMU()
        self.encoder = Encoder()
        self.init_network()
        self.create_dump_file()

        # Connect signals
        self.video_source.frame_ready.connect(self.on_new_frame)
        self.telemetry.telemetry_ready.connect(self.on_telemetry_data)
        self.imu.imu_ready.connect(self.on_imu_data)
        self.encoder.encode_ready.connect(self.on_encoded_frame)
        self.video_source.init_capture()
        self.telemetry.start()
        self.imu.start()

    def switch_video_source(self, new_source):
        """Switch the active video source at runtime.

        Stops current source, disconnects signal, assigns new source, connects it and initializes capture if capturing.
        Maintains speed & direction state if supported.
        """
        try:
            # Disconnect and stop old source
            if hasattr(self.video_source, 'frame_ready'):
                try:
                    self.video_source.frame_ready.disconnect(self.on_new_frame)
                except Exception:
                    pass
            if hasattr(self.video_source, 'stop'):
                try:
                    self.video_source.stop()
                except Exception:
                    pass

            # Replace
            self.video_source = new_source
            self.video_source.frame_ready.connect(self.on_new_frame)

            # Apply current direction & speed if methods exist
            if hasattr(new_source, 'set_direction'):
                try:
                    new_source.set_direction(DIRECTION["FORWARD"])  # default forward
                except Exception:
                    pass
            if hasattr(new_source, 'set_speed'):
                try:
                    new_source.set_speed(self.target_speed)
                except Exception:
                    pass

            if self.is_capturing:
                self.video_source.init_capture()
            self.log_message(f"Video source switched to {new_source.__class__.__name__}")
        except Exception as e:
            self.log_message(f"Failed to switch video source: {e}")

    def initialize_train_client_id(self):
        client_id = str(uuid.uuid4())
        logger.info(f"TrainClient ID initialized: {client_id}")
        return client_id

    def create_dump_file(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dump_dir = os.path.dirname(H264_DUMP)
        if dump_dir and not os.path.exists(dump_dir):
            os.makedirs(dump_dir, exist_ok=True)
        output_filename = f"{H264_DUMP}_{timestamp}.h264"
        self.output_file = open(output_filename, 'wb')

    def init_network(self):
        # WebSocket
        self.network_worker_ws = NetworkWorkerWS(self.train_client_id)
        self.network_worker_ws.process_command.connect(self.on_new_command)
        self.network_worker_ws.start()

        # QUIC
        self.network_worker_quic = NetworkWorkerQUIC(self.train_client_id)
        self.network_worker_quic.connection_established.connect(self.on_quic_connected)
        self.network_worker_quic.connection_failed.connect(self.on_quic_failed)
        self.network_worker_quic.connection_closed.connect(self.on_quic_closed)
        self.network_worker_quic.data_received.connect(self.on_data_received_quic)
        self.network_worker_quic.process_command.connect(self.on_new_command)
        self.network_worker_quic.start()

        # MQTT
        self.network_worker_mqtt = NetworkWorkerMqtt(self.train_client_id)

        self.networkspeed = NetworkSpeed(duration=5)
        self.networkspeed.speed_calculated.connect(self.on_network_speed_calculated)



    def on_network_speed_calculated(self, data):
        logger.info(
            f"Network speed calculated - Download: {data["download_speed"]:.2f} Mbps, "
            f"Upload: {data["upload_speed"]:.2f} Mbps"
        )
        self.telemetry.set_network_speed(data["download_speed"], data["upload_speed"], data["jitter"], data["ping"])

    def on_quic_connected(self):
        logger.info("QUIC connection established")

    def on_quic_failed(self, error):
        logger.error(f"QUIC connection failed: {error}")

    def on_quic_closed(self):
        logger.info("QUIC connection closed")

    def on_data_received_quic(self, data):
        logger.info(f"QUIC data received: {data}")

    def on_new_command(self, payload):
        message = json.loads(payload.decode('utf-8'))
        logger.info(f"Received command: {message}")
        if message['instruction'] == 'CHANGE_TARGET_SPEED':
            self.target_speed = message['target_speed']
            self.update_speed(self.target_speed)
        elif message['instruction'] == 'STOP_SENDING_DATA':
            if self.is_sending:
                self.toggle_sending()
        elif message['instruction'] == 'START_SENDING_DATA':
            if not self.is_sending:
                self.toggle_sending()
        elif message['instruction'] == 'POWER_ON':
            self.telemetry.set_status(TRAIN_STATUS["POWER_ON"])
            self.target_speed = max(self.target_speed, 30)
            self.on_power_on()
        elif message['instruction'] == 'POWER_OFF':
            self.telemetry.set_status(TRAIN_STATUS["POWER_OFF"])
            self.target_speed = 0
            self.on_power_off()
        elif message['instruction'] == 'CHANGE_DIRECTION':
            direction = message.get('direction')
            if direction in ("FORWARD", "BACKWARD"):
                self.video_source.set_direction(DIRECTION[direction])
                self.telemetry.set_direction(DIRECTION[direction])
                self.on_change_direction(DIRECTION[direction])
            else:
                logger.warning(f"Unknown direction: {direction}")
        elif message['instruction'] == 'CALCULATE_NETWORK_SPEED':
            self.networkspeed.start()
        elif message['instruction'] == 'CHANGE_VIDEO_QUALITY':
            video_quality = message.get('quality')
            logger.info(f"Video quality is changing to {video_quality}")
            if video_quality ==  "low":
                logger.info(f"Setting encoder bitrate to LOW_BITRATE: {LOW_BITRATE}")
                self.encoder.set_bitrate(LOW_BITRATE)
            elif video_quality == "medium":
                logger.info(f"Setting encoder bitrate to MEDIUM_BITRATE: {MEDIUM_BITRATE}")
                self.encoder.set_bitrate(MEDIUM_BITRATE)
            elif video_quality == "high":
                logger.info(f"Setting encoder bitrate to HIGH_BITRATE: {HIGH_BITRATE}")
                self.encoder.set_bitrate(HIGH_BITRATE)
            else:
                logger.warning(f"Unknown video quality: {video_quality}")

        else:
            logger.warning(f"Unknown instruction: {message['instruction']}")

    def on_new_frame(self, frame_id, frame, width, height):
        self.encoder.encode_frame(frame_id, frame, width, height, self.log_message)

    def on_telemetry_data(self, data):
        self.log_message(f"Telemetry data: {data}")
        if self.is_sending:
            packet_data = json.dumps(data).encode('utf-8')
            packet = struct.pack("B", PACKET_TYPE["telemetry"]) + packet_data
            self.network_worker_quic.enqueue_stream_packet(packet)
            self.network_worker_ws.enqueue_packet(packet)
            self.network_worker_mqtt.send_data(packet_data)

    def on_imu_data(self, data):
        self.log_message(f"IMU Data: {data}")

    def on_encoded_frame(self, frame_id, timestamp, encoded_bytes):
        if self.write_to_file:
            self.output_file.write(encoded_bytes)
            self.output_file.flush()
        if self.is_sending:
            # Send the encoded frame over QUIC
            self.network_worker_quic.enqueue_frame(frame_id, timestamp, encoded_bytes)
            self.telemetry.notify_new_frame_processed()

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
        self.log_message(f"Sending {'enabled' if self.is_sending else 'disabled'}")

    def toggle_write_to_file(self):
        self.write_to_file = not self.write_to_file
        self.log_message(f"Write to file {'enabled' if self.write_to_file else 'disabled'}")

    def log_message(self, message):
        timestamp = QDateTime.currentDateTime().toString("[hh:mm:ss.zzz]")
        # logger.info(f"{timestamp} {message}")

    def close(self):
        self._running = False
        self.video_source.stop()
        self.encoder.close()
        self.network_worker_ws.stop()
        self.network_worker_quic.stop()
        self.output_file.close()
        logger.info("BaseClient closed.")

    @abstractmethod
    def update_speed(self, speed):
        pass

    @abstractmethod
    def on_power_on(self):
        pass

    @abstractmethod
    def on_power_off(self):
        pass

    @abstractmethod
    def on_change_direction(self, direction):
        pass