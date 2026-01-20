from abc import ABC, abstractmethod
import asyncio
import datetime
import os
import uuid
import json
import struct
from PyQt5.QtCore import QThread, QDateTime, QTimer
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
from hw_info import HWInfo

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
        self.target_speed = MAX_SPEED
        self._running = True
        self.connected_remote_control_ids = set()
        self.clock_offsets = {}  # Clock offset between train and remote controls (ms)
        self.number_of_rtt_packets = 5
        self.clock_offset_samples = {}
        self.create_dump_file_for_latency()

        # Initialize components
        self.telemetry = Telemetry(self.train_client_id)
        self.imu = IMU()
        self.encoder = Encoder()
        self.init_network()
        self.create_dump_file()
        self.hw_info = HWInfo()
        self.hw_info_generator_timer = QTimer()
        self.hw_info_generator_timer.timeout.connect(self.generate_hw_info)
        self.hw_info_generator_timer.start(1000)  # every 1 seconds

        # Connect signals
        self.video_source.frame_ready.connect(self.on_new_frame)
        self.telemetry.telemetry_ready.connect(self.on_telemetry_data)
        self.imu.imu_ready.connect(self.on_imu_data)
        self.encoder.encode_ready.connect(self.on_encoded_frame)
        self.video_source.init_capture()
        self.telemetry.start()
        self.imu.start()

    def generate_hw_info(self):
        self.hw_info.get_hw_info(write_to_file=True)

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

    def create_dump_file_for_latency(self):
        dump_dir = os.path.dirname(LATENCY_DUMP)
        if dump_dir and not os.path.exists(dump_dir):
            os.makedirs(dump_dir, exist_ok=True)

        time_suffix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{LATENCY_DUMP}_{time_suffix}.log"


        # create a new file only if it doesn't exist
        if not os.path.exists(output_filename):
            self.latency_output_file = open(output_filename, 'w')
        else:
            self.latency_output_file = open(output_filename, 'a')

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
            f"Network speed calculated - Download: {data['download_speed']:.2f} Mbps, "
            f"Upload: {data['upload_speed']:.2f} Mbps"
        )
        self.telemetry.set_network_speed(data['download_speed'], data['upload_speed'], data['jitter'], data['ping'])

    def on_quic_connected(self):
        logger.info("QUIC connection established")

    def on_quic_failed(self, error):
        logger.error(f"QUIC connection failed: {error}")

    def on_quic_closed(self):
        logger.info("QUIC connection closed")

    def on_data_received_quic(self, data):
        logger.info(f"QUIC data received: {data}")
        packet_type = data[0]
        payload = data[1:]
        if packet_type == PACKET_TYPE["map_ack"]:
            ## Map ACK received: data =  b'{"type": "mapping_acknowledgement", "remote_control_id": "44ffefc5-878e-4558-b846-37a3acdfd8af"}'
            remote_control_id = json.loads(payload.decode('utf-8')).get('remote_control_id')
            self.connected_remote_control_ids.add(remote_control_id)
            logger.info(f"Map ACK received from remote control ID: {remote_control_id}")
            # Reset samples for this remote and start RTT measurement
            self.clock_offset_samples[remote_control_id] = []
            self.send_rtt_packets(remote_control_id)
            self.hw_info.notify_new_remote_control_connected(remote_control_id)

        elif packet_type == PACKET_TYPE["rtt_train"]:
            jsonString = payload.decode('utf-8')
            jsonData = json.loads(jsonString)

            # Extract timestamps
            remote_control_timestamp = jsonData.get('remote_control_timestamp', 0)
            train_timestamp_sent = jsonData.get('train_timestamp', 0)
            current_time = int(datetime.datetime.now().timestamp() * 1000)
            remote_control_id = jsonData.get('remote_control_id')

            # Calculate RTT (Round Trip Time)
            rtt = current_time - train_timestamp_sent

            # Calculate clock offset
            # Clock offset = remote_time - local_time (at the midpoint of RTT)
            # Approximation: remote_control_timestamp was captured at roughly (train_timestamp_sent + rtt/2)
            clock_offset = remote_control_timestamp - (train_timestamp_sent + rtt / 2)

            # Collect offset samples per remote and compute average after N samples
            samples = self.clock_offset_samples.setdefault(remote_control_id, [])
            samples.append(clock_offset)

            logger.info(
                f"RTT packet received - "
                f"RTT: {rtt}ms, "
                f"Clock Offset sample: {clock_offset:.2f}ms, "
                f"Sample count for {remote_control_id}: {len(samples)}/{self.number_of_rtt_packets}, "
                f"Remote timestamp: {remote_control_timestamp}, "
                f"Train timestamp sent: {train_timestamp_sent}, "
                f"Current time: {current_time}"
            )

            if len(samples) >= self.number_of_rtt_packets:
                avg_offset = sum(samples[:self.number_of_rtt_packets]) / self.number_of_rtt_packets
                avg_offset = round(avg_offset)
                self.clock_offsets[remote_control_id] = avg_offset
                logger.info(
                    f"Clock offset established for {remote_control_id}: {avg_offset:.2f}ms "
                    f"(averaged over {self.number_of_rtt_packets} RTT samples)"
                )
                # Reset samples to avoid unbounded growth; new ACK can re-initiate measurement
                self.clock_offset_samples[remote_control_id] = []

        else:
            logger.warning(f"Unknown QUIC packet type received: {packet_type}")



    def send_rtt_packets(self, remote_control_id):
        for _ in range(self.number_of_rtt_packets):
            rtt_train_Packet = {
                "type": "rtt_train",
                "remote_control_timestamp": 0,
                "remote_control_id": remote_control_id,
                "train_timestamp": int(datetime.datetime.now().timestamp() * 1000)
            }

            rtt_train_data = json.dumps(rtt_train_Packet).encode('utf-8')
            rtt_train_packet = struct.pack("B", PACKET_TYPE["rtt_train"]) + rtt_train_data
            self.network_worker_quic.enqueue_stream_packet(rtt_train_packet)

    def calculate_latency(self, remote_control_id, remote_timestamp):
        current_time = int(datetime.datetime.now().timestamp() * 1000)

        # Check if clock offset has been calculated for this remote control
        if remote_control_id not in self.clock_offsets:
            logger.warning(f"Clock offset not available for remote_control_id: {remote_control_id}. Cannot calculate accurate latency. Clock offsets: {self.clock_offsets}")
            return None

        # Adjust remote timestamp to local time by subtracting clock offset
        # Clock offset = remote_time - local_time, so local_time = remote_time - clock_offset
        adjusted_remote_time = remote_timestamp - self.clock_offsets[remote_control_id]
        # Latency = current_time - adjusted_remote_time
        latency = current_time - adjusted_remote_time
        return latency

    def on_webrtc_connected(self):
        logger.info("WebRTC connection established")

    def on_webrtc_failed(self, error):
        logger.error(f"WebRTC connection failed: {error}")

    def on_webrtc_closed(self):
        logger.info("WebRTC connection closed")

    def on_data_received_webrtc(self, data):
        logger.debug(f"WebRTC data received: {len(data)} bytes")

    def on_new_command(self, payload):
        message = json.loads(payload.decode('utf-8'))
        remote_control_id = message.get('remote_control_id', 0)
        latency = self.calculate_latency(remote_control_id, message.get('remote_control_timestamp', 0))

        if latency is not None:
            logger.info(f"Received command: {message} with latency: {latency}ms")
            latency_log_entry = {
                "remote_control_id": remote_control_id,
                "command_id": message.get("command_id"),
                "instruction": message['instruction'],
                "latency": latency,
                "created_at": message.get('remote_control_timestamp', 0),
                "received_at": int(datetime.datetime.now().timestamp() * 1000),
                "size" : len(payload),
                "target_speed": message.get('target_speed', None),
                "direction": message.get('direction', None),
                "quality": message.get('quality', None),
            }
            self.latency_output_file.write(json.dumps(latency_log_entry) + "\n")
            self.latency_output_file.flush()
        else:
            logger.info(f"Received command: {message} (latency not available - clock not synchronized)")

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
            self.target_speed = max(self.target_speed, MAX_SPEED)
            self.on_power_on()
        elif message['instruction'] == 'POWER_OFF':
            self.telemetry.set_status(TRAIN_STATUS["POWER_OFF"])
            self.target_speed = 0
            self.on_power_off()
        elif message['instruction'] == 'CHANGE_DIRECTION':
            direction = message.get('direction')
            if direction in ("FORWARD", "BACKWARD"):
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
        elif message['instruction'] == 'SWITCH_PROTOCOL':
            protocol = message.get('protocol', '').upper()
            if protocol in ['WEBSOCKET', 'QUIC', 'WEBRTC']:
                self.switch_protocol(protocol)
            else:
                logger.warning(f"Unknown protocol: {protocol}")
        else:
            logger.warning(f"Unknown instruction: {message['instruction']}")

    def on_new_frame(self, frame_id, frame, width, height):
        self.encoder.encode_frame(frame_id, frame, width, height, self.log_message)

    def on_telemetry_data(self, data):
        self.log_message(f"Telemetry data: {data}")
        if self.is_sending:
            packet_data = json.dumps(data).encode('utf-8')
            packet = struct.pack("B", PACKET_TYPE["telemetry"]) + packet_data
            # Send telemetry on all active connections
            # self.network_worker_quic.enqueue_stream_packet(packet)
            # self.network_worker_ws.enqueue_packet(packet)
            self.network_worker_mqtt.send_data(packet_data)

    def on_imu_data(self, data):
        self.log_message(f"IMU Data: {data}")

    def on_encoded_frame(self, frame_id, timestamp, encoded_bytes):
        if self.write_to_file:
            self.output_file.write(encoded_bytes)
            self.output_file.flush()
        if self.is_sending:
            # Send the encoded frame over the network
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