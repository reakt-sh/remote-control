# some configuration for components

START_X = 100
START_Y = 100
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FRAME_RATE = 30
H264_DUMP = "../dump_collection/dump"
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
    "notification": 21
}
SERVER_WEBSOCKET_PORT = 8000
SERVER_URL = f"ws://localhost:{SERVER_WEBSOCKET_PORT}/ws"

TEXT_FIELD_HEIGHT = 23
BG_COLOR = "#9CAFB4"
ID_BG_COLOR = "light green"
TAG_FONT = ("cabin", 18, "bold")
TEXT_FONT = ("Open Sans", 18)
OUTPUT_TEXT_FONT = ("Times New roman", 14)
CONSOLE_TEXT_FONT = ("Courier New", 14)
ID_FONT = ("Open Sans", 20, "bold")
BUTTON_FONT = ("Archivo Black", 16, "bold")
BUTTON_WIDTH = 10
BUTTON_BG_COLOR = "#acc3e3"
BUTTON_FG_COLOR = "black"
BUTTON_ACTIVE_BG_COLOR = "#7792b8"
BUTTON_ACTIVE_FG_COLOR = "#65e7ff"
BUTTON_HIGHLIGHT_COLOR = "white"
BUTTON_HIGHLIGHT_ACTIVE_COLOR = "red"
BUTTON_CURSOR = 'hand2'
TEXT_WIDGET_BG_COLOR = '#cfd5d6'
TAG_BG_COLOR = TEXT_WIDGET_BG_COLOR

