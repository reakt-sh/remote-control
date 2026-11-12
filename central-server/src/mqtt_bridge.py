import asyncio
import json
import threading
import time
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

        logger.info(f"MQTT Bridge initialized for broker {broker_host}:{broker_port}")

    def start(self):
        if self.is_running:
            logger.warning("MQTT Bridge is already running")
            return

        try:
            logger.info(f"Connecting to NanoMQ broker at {self.broker_host}:{self.broker_port}")

            # Create MQTT client
            self.client = mqtt.Client(client_id=self.client_id)

            # Set up callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_subscribe = self._on_subscribe

            # Connect to broker
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)

            # Start the MQTT loop in a separate thread
            self.client.loop_start()
            self.is_running = True

            logger.success(f"MQTT Bridge started, connecting to broker...")

        except Exception as e:
            logger.error(f"Failed to start MQTT bridge: {e}")
            self.is_running = False
            raise

    def stop(self):
        if not self.is_running:
            return

        self.is_running = False

        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
                logger.info("Disconnected from MQTT broker")
            except Exception as e:
                logger.error(f"Error disconnecting from MQTT broker: {e}")

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

    def _on_disconnect(self, client, userdata, rc):
        self.is_connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker (code: {rc})")
        else:
            logger.info("Disconnected from MQTT broker")

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        logger.info(f"Subscription confirmed with QoS: {granted_qos}")

    def _on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')

            if topic == MQTT_TOPICS.WAN:
                logger.debug(f"Received WAN message: {payload}")
                influx_writer.write_wan(json.loads(payload))
            elif topic == MQTT_TOPICS.TELEMETRY:
                logger.debug(f"Received Telemetry message: {payload}")
            elif topic == MQTT_TOPICS.FRAME_LATENCY:
                logger.debug(f"Received Frame Latency message: {payload}")
            elif topic == MQTT_TOPICS.COMMAND_LATENCY:
                logger.debug(f"Received Command Latency message: {payload}")
            elif topic == MQTT_TOPICS.CLOCK_TRAIN:
                logger.debug(f"Received Clock Offset (Train) message: {payload}")
            elif topic == MQTT_TOPICS.CLOCK_RC:
                logger.debug(f"Received Clock Offset (Remote Control) message: {payload}")
            else:
                logger.warning(f"Invalid topic format: {topic}")

        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")

    def _subscribe_to_topics(self):
        topics = [
            (MQTT_TOPICS.WAN, 1), # (topic, qos)
            (MQTT_TOPICS.TELEMETRY, 1),  # (topic, qos)
            (MQTT_TOPICS.FRAME_LATENCY, 1), # (topic, qos)
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
    """Example usage of MqttBridge"""

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
