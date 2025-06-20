import sys
from dataclasses import dataclass

# Packet Types
PACKET_TYPE = {
    "video": 13,
    "audio": 14,
    "control": 15,
    "command": 16,
    "telemetry": 17,
    "imu": 18,
    "lidar": 19,
    "keepalive": 20,
    "notification": 21
}

HOST = "0.0.0.0"
FAST_API_PORT = 8000
QUIC_PORT = 4437

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
