import paho.mqtt.client as mqtt
from loguru import logger
from globals import *
class NetworkWorkerMqtt:
    def __init__(self, train_id):
        self.mqtt_client = mqtt.Client(train_id)
        self.topic = f"trains/{train_id}/telemetry"
        self.connect()

    def connect(self):
        self.mqtt_client.connect(SERVER, MQTT_PORT)

    def publish(self, message):
        self.mqtt_client.publish(
            topic = self.topic,
            payload=message,
            qos=1, # Quality of Service level 1 ensures message delivery at least once
        )
        logger.info(f"MQTT Published message to {self.topic}: {message}")

    def disconnect(self):
        self.mqtt_client.disconnect()