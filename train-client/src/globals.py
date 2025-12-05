import sys
import platform
import os
# some configuration for components

START_X = 100
START_Y = 100
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FRAME_RATE = 60
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # This file's directory
H264_DUMP = os.path.join(BASE_DIR, '..', 'dump_collection', 'dump')
ASSET_DIR = os.path.join(BASE_DIR, '..', 'asset')
LATENCY_DUMP = os.path.join(BASE_DIR, '..', 'dump_collection', 'latency')

PIXEL_FORMAT = "yuv420p"

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
    "notification": 21,
    "download_start": 22,
    "downloading": 23,
    "download_end": 24,
    "upload_start": 25,
    "uploading": 26,
    "upload_end": 27,
    "rtt": 28,
    "map_ack": 29,
    "rtt_train": 30,
}

TRAIN_STATUS = {
    "POWER_ON": "running",
    "POWER_OFF": "stopped",
    "UNKNOWN": "unknown"
}

DIRECTION = {
    "FORWARD": 1,
    "BACKWARD": -1,
    "STOPPED": 0
}

# overwrite for remote server
SERVER = 'wt.rtsys-lab.de'

WS_PORT = 8000
QUIC_PORT = 4437
MQTT_PORT = 1883
WEBSOCKET_URL = f"wss://{SERVER}:{WS_PORT}/ws"
MAX_PACKET_SIZE = 1000

# Protocol options for video transmission
PROTOCOL_OPTIONS = {
    "WEBSOCKET": "WebSocket",
    "QUIC": "QUIC",
    "WEBRTC": "WebRTC"
}

# WebRTC Configuration
WEBRTC_STUN_SERVERS = [
    "stun:stun.l.google.com:19302",
    "stun:stun1.l.google.com:19302",
    "stun:stun2.l.google.com:19302",
    "stun:stun3.l.google.com:19302"
]

# Optional TURN servers for NAT traversal (configure if needed)
WEBRTC_TURN_SERVERS = [
    # Example: {"urls": "turn:your-turn-server.com:3478", "username": "user", "credential": "pass"}
]

STATION_LIST = [
    {"name": "Malente",                     "latitude": 54.1722,        "longitude": 10.5597},
    {"name": "Gremsmühlen",                 "latitude": 53.9036,        "longitude": 10.3111},
    {"name": "Plön",                        "latitude": 54.1624,        "longitude": 10.4234},
    {"name": "Ascheberg",                   "latitude": 54.1500,        "longitude": 10.3450},
    {"name": "Preetz",                      "latitude": 54.2353,        "longitude": 10.2775},
    {"name": "Raisdorf Rosenthal",          "latitude": 54.2500,        "longitude": 10.2333},
    {"name": "Raisdorf Schwentinebrücke",   "latitude": 54.2480,        "longitude": 10.2300},
    {"name": "Rastorfer Kreuz",             "latitude": 54.2700,        "longitude": 10.3000},
    {"name": "Wildenhorst",                 "latitude": 54.2800,        "longitude": 10.3500},
    {"name": "Rastorfer Passau",            "latitude": 54.2750,        "longitude": 10.3200},
    {"name": "Fuhlenbrügge",                "latitude": 54.2850,        "longitude": 10.4000},
    {"name": "Wittenberger Passau",         "latitude": 54.2900,        "longitude": 10.4500},
    {"name": "Martensrade Hohenklampen",    "latitude": 54.2800,        "longitude": 10.5000},
    {"name": "Wehdenweg",                   "latitude": 54.2900,        "longitude": 10.5200},
    {"name": "Dorfplatz",                   "latitude": 54.2930,        "longitude": 10.5500},
    {"name": "Bellin-Lammershagen",         "latitude": 54.2950,        "longitude": 10.5600},
    {"name": "Abzw. Jettkrog-Giekau",       "latitude": 54.2960,        "longitude": 10.5700},
    {"name": "Seekrug",                     "latitude": 54.2940,        "longitude": 10.5800},
    {"name": "Giekau-Fresendorf Klamp/B",   "latitude": 54.2930,        "longitude": 10.5850},
    {"name": "Klamp Winterfeld-Klamp",      "latitude": 54.2940,        "longitude": 10.5860},
    {"name": "Schulzentrum-Lütjenburg",     "latitude": 54.2945,        "longitude": 10.5864},
    {"name": "Lütjenburg",                  "latitude": 54.2941,        "longitude": 10.5868}
]

LOW_BITRATE = 1000000  # 1 Mbps
MEDIUM_BITRATE = 2000000  # 2 Mbps
HIGH_BITRATE = 5000000  # 5 Mbps
MAX_SPEED = 20 # KM/H
SCALE_FACTOR_PWM = 1.25  # Scale factor to convert speed to PWM duty cycle


TEXT_FIELD_HEIGHT = 23
BG_COLOR = "#9CAFB4"
ID_BG_COLOR = "light green"
TAG_FONT = ("cabin", 18, "bold")
TEXT_FONT = ("Open Sans", 18)
OUTPUT_TEXT_FONT = ("Times New roman", 14)
CONSOLE_TEXT_FONT = ("Courier New", 14)
ID_FONT = ("Open Sans", 20, "bold")
BUTTON_FONT = ("Archivo Black", 16, "bold")
BUTTON_WIDTH = 50
BUTTON_BG_COLOR = "#acc3e3"
BUTTON_FG_COLOR = "black"
BUTTON_ACTIVE_BG_COLOR = "#7792b8"
BUTTON_ACTIVE_FG_COLOR = "#65e7ff"
BUTTON_HIGHLIGHT_COLOR = "white"
BUTTON_HIGHLIGHT_ACTIVE_COLOR = "red"
BUTTON_CURSOR = 'hand2'
TEXT_WIDGET_BG_COLOR = '#cfd5d6'
TAG_BG_COLOR = TEXT_WIDGET_BG_COLOR

