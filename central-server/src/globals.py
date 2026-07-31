import sys
from dataclasses import dataclass
from enum import Enum, IntEnum, StrEnum

# Packet Types
class PACKET_TYPE(IntEnum):
    VIDEO_FRONT = 11
    VIDEO_REAR = 12
    VIDEO = 13
    AUDIO = 14
    CONTROL = 15
    COMMAND = 16
    TELEMETRY = 17
    IMU = 18
    LIDAR = 19
    KEEPALIVE = 20
    NOTIFICATION = 21
    DOWNLOAD_START = 22
    DOWNLOADING = 23
    DOWNLOAD_END = 24
    UPLOAD_START = 25
    UPLOADING = 26
    UPLOAD_END = 27
    RTT = 28
    MAP_CONNECT = 29
    RTT_TRAIN = 30
    MAP_DISCONNECT = 31
    CONNECT = 32
    CONNECT_RESPONSE = 33
    ERROR_MSG = 34

HOST = "0.0.0.0"
FAST_API_PORT = 8000
QUIC_PORT = 4437

CLIENT_TYPE_TRAIN = "TRAIN"
CLIENT_TYPE_REMOTE_CONTROL = "REMOTE_CONTROL"

STREAM_MESSAGE_SIZE_LIMIT = 300  # bytes, will adjust if needed after testing


@dataclass
class ServerConfig:
    cert_file: str = ""
    key_file: str = ""

def get_client_config() -> ServerConfig:
    """Get platform-specific client configuration"""
    if sys.platform.startswith("win"):
        return ServerConfig(
            cert_file="C:\\quic_conf\\certificate.pem",
            key_file="C:\\quic_conf\\certificate.key"
        )
    elif sys.platform.startswith("linux"):
        return ServerConfig(
            cert_file="/etc/letsencrypt/live/wt.rtsys-lab.de/fullchain.pem",
            key_file="/etc/letsencrypt/live/wt.rtsys-lab.de/privkey.pem"
        )
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")
