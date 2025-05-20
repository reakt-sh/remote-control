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
        logger.debug("QUIC Relay Protocol initialized")

    def quic_event_received(self, event):
        if isinstance(event, StreamDataReceived):
            if event.data[0] == PACKET_TYPE["video"]:
                logger.debug(f"QUIC: Received video packet on stream {event.data}")
            else:
                logger.debug(f"QUIC: Received unhandled data : {event.data}")

async def run_quic_server():
    # Use a real TLS certificate in production!
    logger.debug("QUIC server starting...")
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
    logger.debug(f"QUIC server running on {QUIC_HOST}:{QUIC_PORT}")

    # Keep server running forever
    await asyncio.Future()