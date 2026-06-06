import datetime
import os
import uuid
import json
import struct


class Helper:
    def __init__(self):
        print("Helper initialized")

    def get_uuid(self):
        return str(uuid.uuid4())

    def get_timestamp(self):
        return int(datetime.datetime.now().timestamp() * 1000)

    def get_length_prefixed_packet(self, packet):
        data_size = len(packet)
        length_prefixed_packet = bytearray(2 + len(packet))
        length_prefixed_packet[0] = (data_size >> 8) & 0xFF  # High byte
        length_prefixed_packet[1] = data_size & 0xFF         # Low byte
        length_prefixed_packet[2:] = packet
        return length_prefixed_packet