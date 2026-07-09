import datetime
import os
import uuid
import json
import struct
import ntplib

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

    def create_storage_file(self, filename, extension):
        dump_dir = os.path.dirname(filename)
        if dump_dir and not os.path.exists(dump_dir):
            os.makedirs(dump_dir, exist_ok=True)

        time_suffix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{filename}_{time_suffix}.{extension}"
        if extension == "h264":
            file = open(output_filename, "wb")
            return file
        else:
            file = open(output_filename, "w")
            return file

    def get_ntp_offset(self, server="pool.ntp.org", timeout=5):
        client = ntplib.NTPClient()
        response = client.request(server, version=3, timeout=timeout)

        # offset = how far your system clock is from true time (seconds)
        # positive = your clock is ahead, negative = your clock is behind
        offset = response.offset * 1000  # Convert to milliseconds

        return offset