# Auto-generated from errors.yaml
# DO NOT MODIFY!

# List of error codes and messages used by the driver
# Error codes will encoded in a one-hot bit-vector and should be continuous.

ERROR_CONTROL_MODE_SWITCH_UNSAFE = 0
ERROR_CONTROL_MODE_SWITCH_UNSAFE_MESSAGE = "Control mode switch attempted while in unsafe driving mode."
ERROR_REMOTE_CONTROL_TIMEOUT = 1
ERROR_REMOTE_CONTROL_TIMEOUT_MESSAGE = "While in active remote control mode, no control (or heartbeat) message was received in the expected interval."
ERROR_HARDWARE_NO_THROTTLE_DAC = 2
ERROR_HARDWARE_NO_THROTTLE_DAC_MESSAGE = "No connection to motor throttle control component (DAC via I2C)."

# Mapping of error codes to human-readable messages.
ERROR_MAP = {
    0: "Control mode switch attempted while in unsafe driving mode.",
    1: "While in active remote control mode, no control (or heartbeat) message was received in the expected interval.",
    2: "No connection to motor throttle control component (DAC via I2C).",
}
