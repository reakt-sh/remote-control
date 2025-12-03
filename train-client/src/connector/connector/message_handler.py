import logging
import asyncio
from datetime import datetime
from typing import Callable
from math import floor
from .data import Control, InternalState, Status
from .serial_connection_handler import SerialConnectionHandler
from .generated.communication_bp import StatusMessage, ControlMessage, ErrorAppendixMessage, ErrorState, Mode
from .generated.config_communication import COMM_STATUS_MESSAGE_TIME_BITSIZE
from .generated.config_vehicle import MOTOR_SPEED_TRANSMISSION_FACTOR
from .generated.errors import ERROR_MAP

logger = logging.getLogger("connector:internal:messages")

class MessageHandler:
    _serial: SerialConnectionHandler # Internal serial connection handler
    _status_callback: Callable[[Status], None] # Callback for new status
    _worker: asyncio.Task # Background worker task for processing messages

    def __init__(self, serial: SerialConnectionHandler, callback: Callable[[Status], None]):
        self._serial = serial
        self._status_callback = callback
        self._worker = None

    async def _decoder_loop(self, notifier: asyncio.Future) -> None:
        """Background task to decode incoming status messages."""
        try:
            last_status_msg: StatusMessage = None
            time_overflow_offset = 0
            received_message = False
            while True:
                # Read status message bytes form serial
                status_data = await self._serial.consume(StatusMessage.BYTES_LENGTH)
                logger.debug("Received status message data: %s", status_data.hex())
                # Notify that the first message has been received
                if not received_message:
                    received_message = True
                    notifier.set_result(True)
                # Decode status message
                status_msg = StatusMessage()
                try:
                    status_msg.decode(status_data)
                    logger.debug("Decoded status message: %s", status_msg.to_dict())
                except Exception as e:
                    logger.error("Failed to decode status message: %s", e)
                    continue
                # Read error appendix if needed
                status_errors = []
                if status_msg.error != ErrorState.NO_ERROR:
                    logger.debug("Reading error appendix message.")
                    error_data = await self._serial.consume(ErrorAppendixMessage.BYTES_LENGTH)
                    logger.debug("Received error appendix message data: %s", error_data.hex())
                    error_msg = ErrorAppendixMessage()
                    try:
                        error_msg.decode(error_data)
                        # Extract error code from bits
                        error_code_mask = 1
                        while error_msg.errors >= error_code_mask: # While there are still bits to check
                            if error_msg.errors & error_code_mask:
                                error_code = error_code_mask.bit_length() - 1
                                status_errors.append(ERROR_MAP[error_code])
                            error_code_mask <<= 1
                    except Exception as e:
                        logger.error("Failed to decode error appendix message: %s", e)
                        continue
                # Handle timestamp overflow in status messages
                if last_status_msg:
                    if status_msg.time < last_status_msg.time:
                        time_overflow_offset += 1 << COMM_STATUS_MESSAGE_TIME_BITSIZE
                last_status_msg = status_msg
                # Create Status from status data fields and validate via pydantic
                new_status = Status(
                    received_at=datetime.now(),
                    remote_control=status_msg.remote_control,
                    error=status_msg.error,
                    errors=status_errors,
                    mode=status_msg.mode,
                    target_speed=(status_msg.target_rpm * MOTOR_SPEED_TRANSMISSION_FACTOR),
                    motor_speed=(status_msg.motor_rpm * MOTOR_SPEED_TRANSMISSION_FACTOR),
                    internal_state=InternalState(
                        time_ms=status_msg.time + time_overflow_offset,
                        target_rpm=status_msg.target_rpm,
                        motor_rpm=status_msg.motor_rpm,
                        control_rpm=status_msg.control_rpm
                    )
                )
                logger.info("Status received: %s", new_status)
                # Notify listener about new status
                self._status_callback(new_status)
        except asyncio.CancelledError:
            logger.info("Decoder loop stopped")
        except asyncio.QueueShutDown:
            logger.info("SerialConnectionHandler shutdown detected, stopping decoder loop")

    def send_control(self, control: Control) -> bool:
        """Send a control command to the driver."""
        if not self._serial.is_ready():
            logger.error("Cannot send control message: serial connection not yet ready")
            return False
        rpm = floor(control.target_speed / MOTOR_SPEED_TRANSMISSION_FACTOR)
        msg = ControlMessage(
            mode=control.mode,
            target_rpm=rpm
        )
        logger.info("Sending control message: %s", msg.to_dict())
        self._serial.send(msg.encode())
        return True

    def send_heartbeat(self) -> bool:
        """Send a heartbeat control message to the driver."""
        if not self._serial.is_ready():
            logger.error("Cannot send heartbeat message: serial connection not yet ready")
            return False
        msg = ControlMessage(
            mode=Mode.HEARTBEAT,
            target_rpm=0
        )
        logger.info("Sending heartbeat control message: %s", msg.to_dict())
        self._serial.send(msg.encode())
        return True

    async def start_processing(self):
        """Start decoding incoming messages. Will return once the initial message is received but will continue afterwards."""
        if not self._worker:
            notifier = asyncio.get_running_loop().create_future()
            self._worker = asyncio.create_task(self._decoder_loop(notifier))
            try:
                await notifier
            except asyncio.CancelledError:
                logger.info("Decoder loop stopped before initial message received")

    def shutdown(self):
        """Stop decoding incoming messages."""
        self._worker.cancel()

