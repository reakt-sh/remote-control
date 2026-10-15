# Auto-generated from config_hardware.yaml
# DO NOT MODIFY!

# Configuration parameters for the driver board and connected hardware


# Driver board pin specifications
BOARD_PIN_IN_MOTOR_METER = 2 # Pin for reading motor speed.
BOARD_PIN_IN_MANUAL_THROTTLE = "A0" # Pin for reading throttle lever position.
BOARD_PIN_IN_DAC = "A1" # Pin for reading output of DAC.
BOARD_PIN_IN_ONBOARD = 7 # Pin for reading onboard switch (currently not used).
BOARD_PIN_IN_ENABLE_REMOTE_CONTROL = 22 # Pin for reading switch for enabling remote control.
BOARD_PIN_IN_MANUAL_FORWARD = 24 # Pin for reading manual forward switch.
BOARD_PIN_IN_MANUAL_REVERSE = 26 # Pin for reading manual reverse switch.
BOARD_PIN_IN_PANEL_KNOB_ENC_A = 0 # Pin for reading panel knob movement encoded part A.
BOARD_PIN_IN_PANEL_KNOB_ENC_B = 0 # Pin for reading panel knob movement encoded part B.
BOARD_PIN_IN_PANEL_KNOB_PRESSED = 29 # Pin for reading panel knob pressed state.
BOARD_PIN_OUT_MOTOR_FORWARD = 6 # Pin for engaging forward drive of the motor.
BOARD_PIN_OUT_MOTOR_REVERSE = 5 # Pin for engaging reverse drive in the motor.
BOARD_PIN_OUT_MOTOR_BRAKE = 4 # Pin for engaging brake of the motor.
BOARD_PIN_OUT_MOTOR_REGENERATIVE = 3 # Pin for engaging regenerative braking of the motor.
BOARD_PIN_OUT_PANEL_LED_RED = 27 # Pin for red channel of the LED on the control panel.
BOARD_PIN_OUT_PANEL_LED_GREEN = 25 # Pin for green channel of the LED on the control panel.
BOARD_PIN_OUT_PANEL_LED_BLUE = 23 # Pin for blue channel of the LED on the control panel.
BOARD_PIN_OUT_PANEL_DISPLAY_SDO = 33 # Pin for SDO channel of the display on the control panel.
BOARD_PIN_OUT_PANEL_DISPLAY_SDI = 35 # Pin for SDI channel of the display on the control panel.
BOARD_PIN_OUT_PANEL_DISPLAY_SCL = 31 # Pin for SCL channel of the display on the control panel.
BOARD_PIN_OUT_PANEL_DISPLAY_CS = 34 # Pin for CS channel of the display on the control panel.

# Analog conversion specifications
V_REF = 5.0 # Analog reference voltage.
DAC_STEPS = 4095 # Number of steps in MCP 4725 (12 bit).
ADC_STEPS = 1023 # Number of steps in Arduino ADC (10 bit).

# Motor specifications
MOTOR_MAX_RPM = 1125 # Maximum motor speed in RPM.
MOTOR_MIN_RPM = 45 # Motor will not move at speed lower than this. This will also influences the waiting time until the motor is considered stopped.
MOTOR_SIGNAL_EDGES_PER_REVOLUTION = 3 # Number of signal edges (rising edges) per motor revolution. E.g. for a hall sensor with 3 magnets this is 3. Note that only every third edge is a full revolution.

# Throttle lever specifications
THROTTLE_LEVER_LOWER_DEADZONE = 0.01 # Lower deadzone for throttle lever (0.0 - 1.0).
THROTTLE_LEVER_UPPER_DEADZONE = 0.09 # Upper deadzone for throttle lever (0.0 - 1.0).
