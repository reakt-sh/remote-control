# Auto-generated from config_driver.yaml
# DO NOT MODIFY!

# Configuration parameters for the driver behavior

DRIVER_REVOLUTION_SIGNAL_BLIND_TIME = 2 # Time in millis where interrupts are ignored because the signal might be fuzzy and result in multiple signal edges.
DRIVER_BRAKING_DECELERATION_OFFSET_RPM = 15 # Offset in RPM for the deceleration braking behavior. If the negative difference between current and target speed (as absolute value) exceeds this offset, braking behavior will start.
DRIVER_BRAKING_OVERSHOOT_LIMIT_RPM = 361 # Limit in RPM for the overshoot braking behavior. As soon as the actual speed is above this value over the target speed, braking behavior will start.
