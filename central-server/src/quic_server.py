import asyncio
import ssl

from aioquic.asyncio import serve
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.quic.events import DatagramFrameReceived, StreamDataReceived, ConnectionIdIssued
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
        self.is_web_client = False
        self.file = open("video_dump.h264", "wb")
        self.current_frame = bytearray()
        self.current_frame_id = -1
        logger.debug("QUIC Relay Protocol initialized")

    def quic_event_received(self, event):
        if isinstance(event, StreamDataReceived):
            # Identify client type
            if not self.is_train and not self.is_web_client:
                try:
                    message = event.data.decode()
                    if message.startswith("TRAIN:"):
                        self.is_train = True
                        self.train_id = message[6:]  # Extract train ID
                        QUICRelayProtocol.train_clients[self.train_id] = self
                        logger.debug(f"Train {self.train_id} connected via QUIC")
                        return
                    elif message.startswith("CLIENT:"):
                        self.is_web_client = True
                        self.train_id = message[7:]  # Extract train ID
                        QUICRelayProtocol.web_clients.add(self)
                        logger.debug(f"Web client for train {self.train_id} connected via QUIC")
                        return
                    else:
                        logger.warning(f"Unknown client identification message: {message}")
                        return
                except UnicodeDecodeError:
                    logger.warning("Could not decode client identification message")
                    return

            if self.is_train and event.data[0] == PACKET_TYPE["video"]:
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
                        for client in list(QUICRelayProtocol.web_clients):
                            if client != self and client.train_id == self.train_id:
                                client._quic.send_stream_data(event.stream_id, self.current_frame)
                                asyncio.create_task(client.transmit())
                        # now write to a file to test
                        self.file.write(self.current_frame)
                        self.file.flush()
                        logger.debug(f"QUIC: Received complete video frame {frame_id} of size {len(self.current_frame)}")

            else:
                logger.debug(f"QUIC: Received unhandled data : {event.data}")
        if isinstance(event, DatagramFrameReceived):
            logger.debug(f"QUIC: Received datagram frame: {event.data}")
        if isinstance(event, ConnectionIdIssued):
            logger.debug(f"QUIC: Received ConnectionIDIssued: {event.connection_id}")

async def run_quic_server():
    # Use a real TLS certificate in production!
    logger.debug("QUIC: server starting...")
    configuration = QuicConfiguration(
        is_client=False,
        alpn_protocols=["h3", "webtransport"]
    )
    configuration.load_cert_chain(certfile="/etc/ssl/quic_conf/cert.pem", keyfile="/etc/ssl/quic_conf/key.pem")

    # for testing, verfy mode disable
    configuration.verify_mode = ssl.CERT_NONE

    await serve(
        HOST,
        QUIC_PORT,
        configuration=configuration,
        create_protocol=QUICRelayProtocol,
    )
    # show which port and host the server is running on
    logger.debug(f"QUIC: server running on {HOST}:{QUIC_PORT}")

    # Keep server running forever
    await asyncio.Future()