# Auto-generated from errors.yaml
# DO NOT MODIFY!

# List of error codes and messages used by the driver
# Error codes will encoded in a one-hot bit-vector and should be continuous.

ERROR_COMM_CONNECTION_VERSION_MISMATCH = 0
ERROR_COMM_CONNECTION_VERSION_MISMATCH_MESSAGE = "Connection refused due to protocol version mismatch between driver and remote control."
ERROR_COMM_CONNECTION_NOT_ESTABLISHED = 1
ERROR_COMM_CONNECTION_NOT_ESTABLISHED_MESSAGE = "A control message was received without a successful connection handshake beforehand."
ERROR_REMOTE_CONTROL_TIMEOUT = 2
ERROR_REMOTE_CONTROL_TIMEOUT_MESSAGE = "While in active remote control mode, no control (or heartbeat) message was received in the expected interval."
ERROR_HARDWARE_NO_THROTTLE_DAC = 3
ERROR_HARDWARE_NO_THROTTLE_DAC_MESSAGE = "No connection to motor throttle control component (DAC via I2C)."
ERROR_CONTROL_MODE_SWITCH_UNSAFE = 4
ERROR_CONTROL_MODE_SWITCH_UNSAFE_MESSAGE = "Control mode switch attempted while in unsafe driving mode."

# Mapping of error codes to human-readable messages.
ERROR_MAP = {
    0: "Connection refused due to protocol version mismatch between driver and remote control.",
    1: "A control message was received without a successful connection handshake beforehand.",
    2: "While in active remote control mode, no control (or heartbeat) message was received in the expected interval.",
    3: "No connection to motor throttle control component (DAC via I2C).",
    4: "Control mode switch attempted while in unsafe driving mode.",
}
