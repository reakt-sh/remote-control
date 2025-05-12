
import json
import struct
from globals import PACKET_TYPE

class PacketBuilder:
    def __init__(self):
        self.packet = {}

    def add_header(self, header):
        """
        Add a header to the packet.
        """
        self.packet['header'] = header

    def add_payload(self, payload):
        """
        Add a payload to the packet.
        """
        self.packet['payload'] = payload

    def build(self):
        """
        Build the packet and return it.
        """
        return self.packet

    def make_train_notification(self, train_id: str, event: str):
        notify_message = {
            "type": "notification",
            "train_id": train_id,
            "event": event
        }
        packet_data = json.dumps(notify_message).encode('utf-8')
        return struct.pack("B", PACKET_TYPE["notification"]) + packet_data