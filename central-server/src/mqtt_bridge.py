import asyncio
import json
import threading
import time
from queue import Empty, Full, Queue
from typing import Dict, Callable, Optional
import paho.mqtt.client as mqtt
from loguru import logger
from globals import MQTT_TOPICS
from influxdb import influx_writer

class MqttBridge:

    def __init__(self, broker_host: str = "localhost", broker_port: int = 1883, client_id: str = "central-server-bridge"):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        self.client: Optional[mqtt.Client] = None
        self.is_connected = False
        self.is_running = False

        # Threading for async integration
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.mqtt_thread: Optional[threading.Thread] = None
        self._messages = Queue(maxsize=10000)
        self._worker_stop = threading.Event()
        self._worker: Optional[threading.Thread] = None

        logger.info(f"MQTT Bridge initialized for broker {broker_host}:{broker_port}")

    def start(self):
        if self.is_running:
            logger.warning("MQTT Bridge is already running")
            return

        if self._worker and self._worker.is_alive():
            raise RuntimeError("Cannot restart MQTT bridge while its message worker is still stopping")

        try:
            logger.info(f"Connecting to NanoMQ broker at {self.broker_host}:{self.broker_port}")

            # Create MQTT client
            self.client = mqtt.Client(
                client_id=self.client_id,
                callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
            )
            self.client.reconnect_delay_set(min_delay=1, max_delay=5)

            # Set up callbacks
            self.client.on_connect = self._on_connect
            self.client.on_connect_fail = self._on_connect_fail
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_subscribe = self._on_subscribe

            # Connect to broker
            self.client.connect_async(self.broker_host, self.broker_port, keepalive=10)

            self._worker_stop.clear()
            self._worker = threading.Thread(target=self._process_messages, daemon=True)
            self._worker.start()

            # Start the MQTT loop in a separate thread
            self.is_running = True
            result = self.client.loop_start()
            if result != mqtt.MQTT_ERR_SUCCESS:
                raise RuntimeError(f"Failed to start MQTT network loop: {result}")

            logger.info("MQTT Bridge started, connecting to broker...")

        except Exception as e:
            logger.error(f"Failed to start MQTT bridge: {e}")
            self.is_running = False
            self._worker_stop.set()
            if self._worker and self._worker.is_alive():
                self._worker.join(timeout=5)
            self.client = None
            raise

    def stop(self):
        if not self.is_running:
            return

        self.is_running = False

        if self.client:
            try:
                self.client.disconnect()
                logger.info("Disconnected from MQTT broker")
            except Exception as e:
                logger.error(f"Error disconnecting from MQTT broker: {e}")
            finally:
                self.client.loop_stop()

        self._worker_stop.set()
        if self._worker:
            self._worker.join(timeout=5)
            if self._worker.is_alive():
                logger.warning("MQTT message worker is still draining messages after shutdown")

        self.is_connected = False
        self.client = None

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.is_connected = True
            logger.success(f"Connected to NanoMQ broker with result code {rc}")

            # Subscribe to topics after successful connection
            self._subscribe_to_topics()

        else:
            self.is_connected = False
            logger.error(f"Failed to connect to MQTT broker with result code {rc}")

    def _on_connect_fail(self, client, userdata):
        logger.warning("MQTT broker connection failed; retrying")

    def _on_disconnect(self, client, userdata, rc):
        self.is_connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker (code: {rc}, {mqtt.error_string(rc)}); retrying")
        else:
            logger.info("Disconnected from MQTT broker")

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        logger.info(f"Subscription confirmed with QoS: {granted_qos}")

    def _on_message(self, client, userdata, msg):
        try:
            self._messages.put_nowait(msg)
        except Full:
            logger.error(f"MQTT message queue is full; dropping message on topic {msg.topic}")

    def _process_messages(self):
        while not self._worker_stop.is_set() or not self._messages.empty():
            try:
                logger.debug(f"MQTT message queue size: {self._messages.qsize()}")
                msg = self._messages.getnowait()
            except Empty:
                threading.sleep(0.1) # Sleep briefly to avoid busy waiting
                continue
            try:
                self._handle_message(msg)
            finally:
                self._messages.task_done()

    def _handle_message(self, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')

            if topic == MQTT_TOPICS.WAN:
                influx_writer.write_wan(json.loads(payload))
            elif topic == MQTT_TOPICS.TELEMETRY:
                influx_writer.write_telemetry(json.loads(payload))
            elif topic == MQTT_TOPICS.TELEMETRY_LATENCY:
                influx_writer.write_telemetry_latency(json.loads(payload))
            elif topic == MQTT_TOPICS.FRAME_LATENCY:
                influx_writer.write_frame_latency(json.loads(payload))
            elif topic == MQTT_TOPICS.COMMAND_LATENCY:
                influx_writer.write_command_latency(json.loads(payload))
            elif topic == MQTT_TOPICS.CLOCK_TRAIN:
                influx_writer.write_clock_train(json.loads(payload))
            elif topic == MQTT_TOPICS.CLOCK_RC:
                influx_writer.write_clock_rc(json.loads(payload))
            else:
                logger.warning(f"Invalid topic format: {topic}")

        except Exception as e:
            logger.error(f"Error handling MQTT message on topic {msg.topic}: {e}")

    def _subscribe_to_topics(self):
        topics = [
            (MQTT_TOPICS.WAN, 1), # (topic, qos)
            (MQTT_TOPICS.TELEMETRY, 1),  # (topic, qos)
            (MQTT_TOPICS.TELEMETRY_LATENCY, 0), # (topic, qos)
            (MQTT_TOPICS.FRAME_LATENCY, 0), # (topic, qos)
            (MQTT_TOPICS.COMMAND_LATENCY, 1), # (topic, qos)
            (MQTT_TOPICS.CLOCK_TRAIN, 1), # (topic, qos)
            (MQTT_TOPICS.CLOCK_RC, 1), # (topic, qos)
        ]

        for topic, qos in topics:
            result, mid = self.client.subscribe(topic, qos=qos)
            if result == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Subscribed to MQTT topic: {topic} (QoS: {qos})")
            else:
                logger.error(f"Failed to subscribe to topic: {topic} (Error: {result})")

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        """Set the asyncio event loop for async handler execution"""
        self.loop = loop
        logger.info("Event loop set for async handler execution")

    def get_connection_status(self) -> Dict:
        """Get current connection status"""
        return {
            "connected": self.is_connected,
            "running": self.is_running,
            "broker": f"{self.broker_host}:{self.broker_port}",
            "client_id": self.client_id,
            "subscribed_topics": [
                self.telemetry_topic_pattern,
                "rtsys/wan/rtsys-cau-01",
            ]
        }


def run_mqtt_bridge():
    # Create MQTT bridge instance
    mqtt_bridge = MqttBridge(
        broker_host="localhost",  # Your NanoMQ host
        broker_port=1883,         # Your NanoMQ port
        client_id="central-server-mqtt-bridge"
    )

    try:
        # Start the bridge
        mqtt_bridge.start()
        while mqtt_bridge.is_running:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down MQTT bridge...")
    except Exception as e:
        logger.error(f"MQTT bridge error: {e}")
    finally:
        mqtt_bridge.stop()
