# Auto-generated from config_communication.yaml
# DO NOT MODIFY!

# Configuration parameters for the communication between driver and connector

COMM_PROTOCOL_VERSION = 1 # Version number of the communication protocol.
COMM_SERIAL_BAUDRATE = 115200 # Serial communication speed.
COMM_MESSAGE_ACKNOWLEDGEMENT_CODE_BITSIZE = 8 # Number of bits used to encode the acknowledgement code in status and control messages.
COMM_STATUS_MESSAGE_TIME_BITSIZE = 32 # Number of bits used to encode the internal time in status messages.
COMM_STATUS_MESSAGE_SPACING_TIME = 1000 # Time between two status messages in ms (unless issued otherwise, e.g. forced response or acknowledgement of a heartbeat).
COMM_CONTROL_MESSAGE_HEARTBEAT_TIME = 200 # When in remote control mode, the maximum time in ms between two control messages before the driver assumes the connection lost and stops the vehicle for safety reasons.
COMM_CONTROL_MESSAGE_ACKNOWLEDGEMENT_TIME = 1000 # Maximum time in ms between a sent control message and its acknowledgement by a status message (w.r.t. acknowledgement code). Checked by the connector.
