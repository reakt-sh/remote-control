import paho.mqtt.client as mqtt
from loguru import logger
from globals import *

class NetworkWorkerMqtt:
    def __init__(self, train_id):
        # Use callback_api_version for paho-mqtt 2.0+ compatibility
        self.mqtt_client = mqtt.Client(
            client_id=train_id,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1
        )
        self.train_id = train_id
        self.topic = f"train/{train_id}/telemetry"
        self.is_connected = False

        # Set up callbacks
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_disconnect = self._on_disconnect
        self.mqtt_client.on_publish = self._on_publish

        self.connect()

    def connect(self):
        try:
            logger.info(f"Connecting to MQTT broker at {SERVER}:{MQTT_PORT}")
            self.mqtt_client.connect(SERVER, MQTT_PORT, keepalive=60)
            # Start the network loop to process callbacks
            self.mqtt_client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            self.is_connected = False

    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker"""
        if rc == 0:
            self.is_connected = True
            logger.success(f"Connected to MQTT broker with result code {rc}")
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

    def _on_publish(self, client, userdata, mid):
        """Callback for when a message is successfully published"""
        pass

    def send_data(self, data):
        if not self.is_connected:
            logger.warning("Cannot send data: MQTT client not connected")
            return False

        try:
            result = self.mqtt_client.publish(
                topic=self.topic,
                payload=data,
                qos=1,  # Quality of Service level 1 ensures message delivery at least once
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                return True
            else:
                logger.error(f"Failed to publish MQTT message: {result.rc}")
                return False

        except Exception as e:
            logger.error(f"Error publishing MQTT message: {e}")
            return False

    def disconnect(self):
        try:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info("MQTT client disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting MQTT client: {e}")

    def is_mqtt_connected(self):
        """Check if MQTT client is connected"""
        return self.is_connected