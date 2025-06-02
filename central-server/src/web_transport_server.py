# # web_transport_server.py
# import asyncio
# from aioquic.asyncio import serve
# from aioquic.quic.configuration import QuicConfiguration
# from aioquic.asyncio.protocol import QuicConnectionProtocol
# from aioquic.quic.events import DatagramFrameReceived, StreamDataReceived

# from utils.app_logger import logger
# from src.globals import *

# class WebTransportHandler(QuicConnectionProtocol):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self._http = None
#         self._session = None

#     def quic_event_received(self, event):
#         if isinstance(event, DatagramFrameReceived):
#             # Handle WebTransport datagrams
#             self._handle_datagram(event.data)
#         elif isinstance(event, StreamDataReceived):
#             # Handle WebTransport streams
#             self._handle_stream(event.stream_id, event.data)

#     def _handle_datagram(self, data):
#         # Process incoming video frames or other datagrams
#         pass

#     def _handle_stream(self, stream_id, data):
#         # Process control messages or other stream data
#         pass

# async def run_web_transport_server():
#     configuration = QuicConfiguration(
#         is_client=False,
#         alpn_protocols=["h3", "webtransport"],
#         max_datagram_frame_size=65536
#     )
#     configuration.load_cert_chain(
#         certfile="/etc/ssl/quic_conf/cert.pem",
#         keyfile="/etc/ssl/quic_conf/key.pem"
#     )

#     await serve(
#         host=HOST,
#         port=WEB_TRANSPORT_PORT,
#         configuration=configuration,
#         create_protocol=WebTransportHandler
#     )
#     print(f"WebTransport server running on {HOST}:{WEB_TRANSPORT_PORT}")
#     await asyncio.Future()  # Run forever