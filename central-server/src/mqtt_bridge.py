import asyncio
import json
import threading
import time
from queue import Empty, Full, Queue
from typing import Dict, Optional
import paho.mqtt.client as mqtt
from loguru import logger
from globals import MQTT_TOPICS
from influxdb import InfluxDBWriter

MQTT_SUBSCRIPTIONS = (
    (MQTT_TOPICS.WAN, 1),
    (MQTT_TOPICS.TELEMETRY, 1),
    (MQTT_TOPICS.TELEMETRY_LATENCY, 1),
    (MQTT_TOPICS.FRAME_LATENCY, 1),
    (MQTT_TOPICS.COMMAND_LATENCY, 1),
    (MQTT_TOPICS.CLOCK_TRAIN, 1),
    (MQTT_TOPICS.CLOCK_RC, 1),
)

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
        self._messages = {topic: Queue(maxsize=10000) for topic, _ in MQTT_SUBSCRIPTIONS}
        self._worker_stop = threading.Event()
        self._workers: Dict[str, threading.Thread] = {}

        logger.info(f"MQTT Bridge initialized for broker {broker_host}:{broker_port}")

    def start(self):
        if self.is_running:
            logger.warning("MQTT Bridge is already running")
            return

        if any(worker.is_alive() for worker in self._workers.values()):
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
            self._workers = {}
            for topic, messages in self._messages.items():
                worker = threading.Thread(
                    target=self._process_messages, args=(topic, messages), daemon=True,
                    name=f"mqtt-{topic}",
                )
                worker.start()
                self._workers[topic] = worker

            # Start the MQTT loop in a separate thread
            self.is_running = True
            result = self.client.loop_start()
            if result != mqtt.MQTT_ERR_SUCCESS:
                raise RuntimeError(f"Failed to start MQTT network loop: {result}")

            logger.info("MQTT Bridge started, connecting to broker...")

        except Exception as e:
            logger.error(f"Failed to start MQTT bridge: {e}")
            self.is_running = False
            self._stop_workers()
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

        self._stop_workers()

        self.is_connected = False
        self.client = None

    def _stop_workers(self):
        self._worker_stop.set()
        deadline = time.monotonic() + 5
        for topic, worker in self._workers.items():
            worker.join(timeout=max(0, deadline - time.monotonic()))
            if worker.is_alive():
                logger.warning(f"MQTT message worker for {topic} is still draining messages after shutdown")

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
        messages = self._messages.get(msg.topic)
        if messages is None:
            logger.warning(f"Invalid topic format: {msg.topic}")
            return
        try:
            messages.put_nowait(msg)
        except Full:
            logger.error(f"MQTT message queue is full; dropping message on topic {msg.topic}")

    def _process_messages(self, topic, messages):
        writer = InfluxDBWriter()
        try:
            while not self._worker_stop.is_set() or not messages.empty():
                try:
                    msg = messages.get(timeout=0.5)
                except Empty:
                    continue
                try:
                    # logger.debug(f"MQTT message queue size for {topic}: {messages.qsize()}")
                    self._handle_message(msg, writer)
                finally:
                    messages.task_done()
        finally:
            try:
                writer.close()
            except Exception as e:
                logger.error(f"Error closing InfluxDB writer for topic {topic}: {e}")

    def _handle_message(self, msg, writer: InfluxDBWriter):
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')

            if topic == MQTT_TOPICS.WAN:
                writer.write_wan(json.loads(payload))
            elif topic == MQTT_TOPICS.TELEMETRY:
                writer.write_telemetry(json.loads(payload))
            elif topic == MQTT_TOPICS.TELEMETRY_LATENCY:
                writer.write_telemetry_latency(json.loads(payload))
            elif topic == MQTT_TOPICS.FRAME_LATENCY:
                writer.write_frame_latency(json.loads(payload))
            elif topic == MQTT_TOPICS.COMMAND_LATENCY:
                writer.write_command_latency(json.loads(payload))
            elif topic == MQTT_TOPICS.CLOCK_TRAIN:
                writer.write_clock_train(json.loads(payload))
            elif topic == MQTT_TOPICS.CLOCK_RC:
                writer.write_clock_rc(json.loads(payload))
            else:
                logger.warning(f"Invalid topic format: {topic}")

        except Exception as e:
            logger.error(f"Error handling MQTT message on topic {msg.topic}: {e}")

    def _subscribe_to_topics(self):
        for topic, qos in MQTT_SUBSCRIPTIONS:
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
