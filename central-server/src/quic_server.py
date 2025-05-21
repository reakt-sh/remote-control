import asyncio
import ssl

from aioquic.asyncio import serve
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.quic.events import StreamDataReceived
from aioquic.quic.configuration import QuicConfiguration

from utils.app_logger import logger
from globals import *


class QUICRelayProtocol(QuicConnectionProtocol):
    # Store connected web clients for relaying video
    web_clients = set()
    train_clients = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.train_id = None
        self.is_train = False

        self.file = open("video_dump.h264", "wb")
        self.current_frame = bytearray()
        self.current_frame_id = -1
        logger.debug("QUIC Relay Protocol initialized")

    def quic_event_received(self, event):
        if isinstance(event, StreamDataReceived):
            if event.data[0] == PACKET_TYPE["video"]:
                # Header = 1 byte for packet type, 4 byte for frame_id, 2 byte for number of packets, 2 byte for packet_id, 36 byte for train_id
                packet_type = event.data[0]
                frame_id = int.from_bytes(event.data[1:5], byteorder='big')
                number_of_packets = int.from_bytes(event.data[5:7], byteorder='big')
                packet_id = int.from_bytes(event.data[7:9], byteorder='big')
                train_id = event.data[9:45].decode('utf-8')
                payload = event.data[45:]
                logger.debug(f"QUIC: {train_id} - Video Packet ==> frame_id: {frame_id}, number_of_packets: {number_of_packets}, packet_id: {packet_id}, payload size: {len(payload)}")

                if self.current_frame_id != frame_id:
                    self.current_frame = bytearray()
                    self.current_frame_id = frame_id
                    self.current_frame.extend(payload)
                else:
                    self.current_frame.extend(payload)
                    if packet_id == number_of_packets:
                        # Send the complete frame to all web clients
                        # now write to a file to test
                        self.file.write(self.current_frame)
                        self.file.flush()
                        logger.debug(f"QUIC: Received complete video frame {frame_id} of size {len(self.current_frame)}")

            else:
                logger.debug(f"QUIC: Received unhandled data : {event.data}")

async def run_quic_server():
    # Use a real TLS certificate in production!
    logger.debug("QUIC: server starting...")
    configuration = QuicConfiguration(is_client=False)
    configuration.load_cert_chain(certfile="/etc/ssl/quic_conf/cert.pem", keyfile="/etc/ssl/quic_conf/key.pem")

    # for testing, verfy mode disable
    configuration.verify_mode = ssl.CERT_NONE

    await serve(
        QUIC_HOST,
        QUIC_PORT,
        configuration=configuration,
        create_protocol=QUICRelayProtocol,
    )
    # show which port and host the server is running on
    logger.debug(f"QUIC: server running on {QUIC_HOST}:{QUIC_PORT}")

    # Keep server running forever
    await asyncio.Future()