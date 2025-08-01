import asyncio
import json
import threading
from typing import Dict, Callable, Optional
import paho.mqtt.client as mqtt
from loguru import logger


class MqttBridge:
    """
    MQTT Bridge for receiving telemetry data from trains via NanoMQ broker using paho-mqtt
    """

    def __init__(self,
                 broker_host: str = "localhost",
                 broker_port: int = 1883,
                 client_id: str = "central-server-bridge"):
        """
        Initialize MQTT Bridge

        Args:
            broker_host: NanoMQ broker hostname/IP
            broker_port: NanoMQ broker port
            client_id: Unique client identifier
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        self.client: Optional[mqtt.Client] = None
        self.is_connected = False
        self.is_running = False

        # Topic patterns
        self.telemetry_topic_pattern = "train/+/telemetry"
        self.status_topic_pattern = "train/+/status"
        self.heartbeat_topic_pattern = "train/+/heartbeat"

        # Callback handlers
        self.telemetry_handlers: Dict[str, Callable] = {}
        self.status_handlers: Dict[str, Callable] = {}

        # Threading for async integration
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.mqtt_thread: Optional[threading.Thread] = None

        logger.info(f"MQTT Bridge initialized for broker {broker_host}:{broker_port}")

    def start(self):
        """Start the MQTT bridge and connect to NanoMQ broker"""
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
        """Stop the MQTT bridge and disconnect from broker"""
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
        """Callback for when the client connects to the broker"""
        if rc == 0:
            self.is_connected = True
            logger.success(f"Connected to NanoMQ broker with result code {rc}")

            # Subscribe to topics after successful connection
            self._subscribe_to_topics()

        else:
            self.is_connected = False
            logger.error(f"Failed to connect to MQTT broker with result code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker"""
        self.is_connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker (code: {rc})")
        else:
            logger.info("Disconnected from MQTT broker")

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback for when subscription is confirmed"""
        logger.info(f"Subscription confirmed with QoS: {granted_qos}")

    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')

            logger.debug(f"Received MQTT message on topic: {topic}")

            # Parse topic to extract train_id and message type
            topic_parts = topic.split('/')
            if len(topic_parts) >= 3:
                train_id = topic_parts[1]
                message_type = topic_parts[2]

                # Route message based on type
                if message_type == "telemetry":
                    self._handle_telemetry_message(train_id, payload)
                elif message_type == "status":
                    self._handle_status_message(train_id, payload)
                elif message_type == "heartbeat":
                    self._handle_heartbeat_message(train_id, payload)
                else:
                    logger.warning(f"Unknown message type: {message_type} from train {train_id}")
            else:
                logger.warning(f"Invalid topic format: {topic}")

        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")

    def _subscribe_to_topics(self):
        """Subscribe to all relevant MQTT topics"""
        topics = [
            (self.telemetry_topic_pattern, 1),  # (topic, qos)
            (self.status_topic_pattern, 1),
            (self.heartbeat_topic_pattern, 0)   # Heartbeat can use QoS 0
        ]

        for topic, qos in topics:
            result, mid = self.client.subscribe(topic, qos=qos)
            if result == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Subscribed to MQTT topic: {topic} (QoS: {qos})")
            else:
                logger.error(f"Failed to subscribe to topic: {topic} (Error: {result})")

    def _handle_telemetry_message(self, train_id: str, payload: str):
        """Handle telemetry data from trains"""
        try:
            # Parse JSON payload
            telemetry_data = json.loads(payload)

            # Log telemetry data as requested
            logger.info(f"Telemetry from train {train_id}: {telemetry_data}")

            # Extract key metrics for summary logging
            speed = telemetry_data.get('speed', 'N/A')
            status = telemetry_data.get('status', 'N/A')
            location = telemetry_data.get('location', 'N/A')
            battery = telemetry_data.get('battery_level', 'N/A')

            logger.info(f"Train {train_id} - Speed: {speed}, Status: {status}, "
                       f"Location: {location}, Battery: {battery}%")

            # Call registered telemetry handlers
            for handler_name, handler in self.telemetry_handlers.items():
                try:
                    if asyncio.iscoroutinefunction(handler):
                        # Handle async functions
                        if self.loop and self.loop.is_running():
                            asyncio.run_coroutine_threadsafe(
                                handler(train_id, telemetry_data), self.loop
                            )
                    else:
                        # Handle sync functions
                        handler(train_id, telemetry_data)
                except Exception as e:
                    logger.error(f"Error in telemetry handler {handler_name}: {e}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in telemetry message from train {train_id}: {e}")
        except Exception as e:
            logger.error(f"Error processing telemetry from train {train_id}: {e}")

    def _handle_status_message(self, train_id: str, payload: str):
        """Handle status updates from trains"""
        try:
            status_data = json.loads(payload)
            logger.info(f"Status update from train {train_id}: {status_data}")

            # Call registered status handlers
            for handler_name, handler in self.status_handlers.items():
                try:
                    if asyncio.iscoroutinefunction(handler):
                        # Handle async functions
                        if self.loop and self.loop.is_running():
                            asyncio.run_coroutine_threadsafe(
                                handler(train_id, status_data), self.loop
                            )
                    else:
                        # Handle sync functions
                        handler(train_id, status_data)
                except Exception as e:
                    logger.error(f"Error in status handler {handler_name}: {e}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in status message from train {train_id}: {e}")
        except Exception as e:
            logger.error(f"Error processing status from train {train_id}: {e}")

    def _handle_heartbeat_message(self, train_id: str, payload: str):
        """Handle heartbeat messages from trains"""
        try:
            heartbeat_data = json.loads(payload)
            timestamp = heartbeat_data.get('timestamp', 'N/A')
            logger.debug(f"Heartbeat from train {train_id} at {timestamp}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in heartbeat from train {train_id}: {e}")
        except Exception as e:
            logger.error(f"Error processing heartbeat from train {train_id}: {e}")

    def register_telemetry_handler(self, name: str, handler: Callable):
        """Register a callback function for telemetry data"""
        self.telemetry_handlers[name] = handler
        logger.info(f"Registered telemetry handler: {name}")

    def register_status_handler(self, name: str, handler: Callable):
        """Register a callback function for status updates"""
        self.status_handlers[name] = handler
        logger.info(f"Registered status handler: {name}")

    def unregister_handler(self, handler_type: str, name: str):
        """Unregister a callback function"""
        if handler_type == "telemetry" and name in self.telemetry_handlers:
            del self.telemetry_handlers[name]
            logger.info(f"Unregistered telemetry handler: {name}")
        elif handler_type == "status" and name in self.status_handlers:
            del self.status_handlers[name]
            logger.info(f"Unregistered status handler: {name}")

    def publish_command(self, train_id: str, command: Dict):
        """Publish command to a specific train"""
        if not self.is_connected:
            logger.error("Cannot publish command: MQTT client not connected")
            return False

        try:
            topic = f"commands/{train_id}/control"
            payload = json.dumps(command)

            result = self.client.publish(topic, payload, qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published command to train {train_id}: {command}")
                return True
            else:
                logger.error(f"Failed to publish command to train {train_id}: {result.rc}")
                return False

        except Exception as e:
            logger.error(f"Error publishing command to train {train_id}: {e}")
            return False

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
                self.status_topic_pattern,
                self.heartbeat_topic_pattern
            ]
        }


# Example usage and testing
def example_telemetry_handler(train_id: str, telemetry_data: Dict):
    """Example handler for processing telemetry data"""
    logger.info(f"Custom handler processing telemetry from {train_id}")
    # Add your custom processing logic here
    pass


def run_mqtt_bridge():
    """Example usage of MqttBridge"""

    # Create MQTT bridge instance
    mqtt_bridge = MqttBridge(
        broker_host="localhost",  # Your NanoMQ host
        broker_port=1883,         # Your NanoMQ port
        client_id="central-server-mqtt-bridge"
    )

    # Register custom handlers
    mqtt_bridge.register_telemetry_handler("example", example_telemetry_handler)

    try:
        # Start the bridge
        mqtt_bridge.start()

        # Keep the main thread alive
        import time
        while mqtt_bridge.is_running:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down MQTT bridge...")
    except Exception as e:
        logger.error(f"MQTT bridge error: {e}")
    finally:
        mqtt_bridge.stop()
