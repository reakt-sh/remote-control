"""
A simple test script for the motor driver connection.
Tests with a fixed speed.
"""

import asyncio
import logging
from context import Connection, Status, Control, Mode

TARGET_SPEED = 1000  # Target speed in RPM

# Status handling
status = None
def set_status(s: Status):
    """Callback for new status messages."""
    global status
    status = s
    print("New status: ", s)

async def main():
    # Uncomment for debugging output
    # logging.basicConfig(level=logging.DEBUG)

    # Open connection
    connection = Connection()
    connection.add_status_listener(set_status)
    await connection.open("/dev/ttyUSB0")

    # Test if connection is ready
    if not connection.is_ready():
        print("Warning: Connection not yet ready. Check connection.")
    while not status:
        print("Waiting for initial status...")
        await asyncio.sleep(.1)

    # Test state
    if not status.remote_control:
        print("Warning: Driver not in remote control mode.")

    # Testing
    try:
        # Set speed
        control = Control(
            mode = Mode.FORWARD,
            target_rpm = TARGET_SPEED
        )
        print("Sending new RPM:", control.target_rpm)
        connection.send_control(control)

        # Wait until speed reached
        while status.motor_rpm < TARGET_SPEED * 0.95:
            print("Waiting for motor to reach target speed. Current RPM:", status.motor_rpm)
            await asyncio.sleep(.5)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        print("Stopping motor...")
        control = Control(
            mode = Mode.NEUTRAL,
            target_rpm = 0
        )
        connection.send_control(control)
        await asyncio.sleep(1)

        connection.close()
        print("Connection closed.")

if __name__ == "__main__":
    asyncio.run(main())
