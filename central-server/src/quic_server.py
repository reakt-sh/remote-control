import asyncio
from aioquic.asyncio import serve
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.quic.events import StreamDataReceived

QUIC_PORT = 4433
QUIC_HOST = "0.0.0.0"

class QuicRelayProtocol(QuicConnectionProtocol):
    # Store connected web clients for relaying video
    web_clients = set()
    train_clients = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.train_id = None
        self.is_train = False

    def quic_event_received(self, event):
        if isinstance(event, StreamDataReceived):
            # First message from train: b"TRAIN:<train_id>"
            if not self.is_train and event.data.startswith(b"TRAIN:"):
                self.is_train = True
                self.train_id = event.data.decode().split(":")[1]
                QuicRelayProtocol.train_clients[self.train_id] = self
                print(f"Train {self.train_id} connected via QUIC")
                return
            if self.is_train:
                # Relay to all web clients for this train
                for client in list(QuicRelayProtocol.web_clients):
                    if getattr(client, "train_id", None) == self.train_id:
                        client._quic.send_stream_data(event.stream_id, event.data)
                        asyncio.create_task(client.transmit())
            else:
                # Assume web client sends: b"CLIENT:<train_id>"
                if event.data.startswith(b"CLIENT:"):
                    self.train_id = event.data.decode().split(":")[1]
                    QuicRelayProtocol.web_clients.add(self)
                    print(f"Web client for train {self.train_id} connected via QUIC")

async def run_quic_server():
    # Use a real TLS certificate in production!
    await serve(
        QUIC_HOST,
        QUIC_PORT,
        configuration=None,
        create_protocol=QuicRelayProtocol,
    )