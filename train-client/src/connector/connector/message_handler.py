"""
INTERNAL message handler for decoding and encoding messages to/from the vehicle.
"""

import asyncio
from datetime import datetime
from typing import Callable
from math import floor
from .data import ConnectionProblem, Control, InternalState, Status
from .serial_connection_handler import SerialConnectionHandler
from .generated.communication_bp import StatusMessage, ControlAnnouncementMessage, ConnectionControlMessage, MotorControlMessage, ErrorAppendixMessage, ErrorState, ControlPayloadType
from .generated.config_communication import COMM_STATUS_MESSAGE_TIME_BITSIZE, COMM_MESSAGE_ACKNOWLEDGEMENT_CODE_BITSIZE, COMM_CONTROL_MESSAGE_ACKNOWLEDGEMENT_TIME, COMM_PROTOCOL_VERSION
from .generated.config_vehicle import MOTOR_SPEED_TRANSMISSION_FACTOR
from .generated.errors import ERROR_MAP
from . import CONNECTOR_ROOT_LOGGER

logger = CONNECTOR_ROOT_LOGGER.getChild("internal.messages")

class MessageHandler:
    """Handler for encoding and decoding messages to/from the vehicle."""

    _serial: SerialConnectionHandler # Internal serial connection handler
    _status_callback: Callable[[Status], None] # Callback for new status
    _error_callback: Callable[[ConnectionProblem], None] # Callback for errors
    _worker: asyncio.Task # Background worker task for processing messages
    _next_acknowledgement_code: int # Counter for acknowledgement code
    _unacknowledged_codes: dict[int, datetime] # Set of currently outstanding acknowledgement codes

    def __init__(self, serial: SerialConnectionHandler, status_callback: Callable[[Status], None], error_callback: Callable[[ConnectionProblem], None]):
        self._serial = serial
        self._status_callback = status_callback
        self._error_callback = error_callback
        self._worker = None
        self._next_acknowledgement_code = 1
        self._unacknowledged_codes = {}

    async def _decoder_loop(self, notifier: asyncio.Future[bool]) -> None:
        """Background task to decode incoming status messages."""
        try:
            last_status_msg: StatusMessage = None
            time_overflow_offset = 0
            connect_pending_ack = 0
            notified = False
            while True:
                # Read status message bytes form serial
                status_data = await self._serial.consume(StatusMessage.BYTES_LENGTH)
                logger.debug("Received status message data: %s", status_data.hex())
                # Decode status message
                status_msg = StatusMessage()
                try:
                    status_msg.decode(status_data)
                    logger.debug("Decoded status message: %s", status_msg.to_dict())
                except Exception as e:
                    logger.error("Failed to decode status message: %s", e)
                    self._error_callback(ConnectionProblem("Failed to decode status message", cause=e))
                    if not notified:
                        notifier.set_result(False)
                        return
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
                        self._error_callback(ConnectionProblem("Failed to decode error appendix message", cause=e))
                        if not notified:
                            notifier.set_result(False)
                            return
                        continue
                # Handle acknowledgement code
                if status_msg.control_acknowledgement > 0:
                    self._handle_received_acknowledgement_code(status_msg.control_acknowledgement)
                # Establish connection handshake
                if connect_pending_ack > 0:
                    if status_msg.connection_established:
                        logger.info("Connection handshake with driver successful.")
                        connect_pending_ack = 0
                        if not notified:
                            notifier.set_result(True)
                            notified = True
                    elif status_msg.control_acknowledgement == connect_pending_ack:
                        logger.error("Connection handshake with driver failed. Check protocol compatibility.")
                        self._error_callback(ConnectionProblem("Connection handshake with driver failed. Check protocol compatibility."))
                        if not notified:
                            notifier.set_result(False)
                            return
                        connect_pending_ack = -1
                elif not status_msg.connection_established:
                    if notified:
                        logger.warning("Driver indicated lost connection, attempting to re-establish.")
                        connect_pending_ack = self._send_connection_request()
                    elif connect_pending_ack == 0:
                        logger.info("Starting connection handshake with driver.")
                        connect_pending_ack = self._send_connection_request()
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
                        connection_established=status_msg.connection_established,
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

    def _get_next_acknowledgement_code(self) -> int:
        """Get the next acknowledgement code for connection requests."""
        code = self._next_acknowledgement_code
        # Register code as unacknowledged
        self._unacknowledged_codes[code] = datetime.now()
        # Find next unused code
        self._next_acknowledgement_code += 1
        if self._next_acknowledgement_code > (1 << COMM_MESSAGE_ACKNOWLEDGEMENT_CODE_BITSIZE) - 1:
            self._next_acknowledgement_code = 1
        if self._next_acknowledgement_code in self._unacknowledged_codes.keys():
            raise Exception(f"Too many unacknowledged messages pending ({len(self._unacknowledged_codes)}). Cannot send new message, no free consecutive acknowledgement code available.")
        return code

    def _handle_received_acknowledgement_code(self, code: int):
        """Process and free the received acknowledgement code."""
        if code in self._unacknowledged_codes:
            if (datetime.now() - self._unacknowledged_codes[code]).total_seconds() * 1000 > COMM_CONTROL_MESSAGE_ACKNOWLEDGEMENT_TIME:
                logger.error("Acknowledgement timeout. Code: %d. Sent: %s. Received: %s", code, self._unacknowledged_codes[code], datetime.now())
                self._error_callback(ConnectionProblem("Acknowledgement timeout"))
            else:
                logger.debug("Received acknowledgement for code: %d", code)
            del self._unacknowledged_codes[code]
        else:
            logger.warning("Received unknown acknowledgement code: %d", code)

    def _send_connection_request(self) -> int:
        """Send a connection request to the driver. Returns the acknowledgement code used."""
        if not self._serial.is_ready():
            logger.error("Cannot send connection request: serial connection not yet ready")
            return 0
        # Announcement message
        pre_msg = ControlAnnouncementMessage(
            acknowledge=0, # No acknowledgement needed for announcement
            type=ControlPayloadType.CONNECT
        )
        logger.info("Sending control announcement message: %s", pre_msg.to_dict())
        self._serial.send(pre_msg.encode())

        # Get acknowledgement code for connection message
        ack_code = self._get_next_acknowledgement_code()
        # Connection control message
        msg = ConnectionControlMessage(
            acknowledge=ack_code,
            protocol_version=COMM_PROTOCOL_VERSION
        )
        logger.info("Sending connection control message: %s", msg.to_dict())
        self._serial.send(msg.encode())
        return ack_code

    def send_control(self, control: Control) -> bool:
        """Send a control command to the driver."""
        if not self._serial.is_ready():
            logger.error("Cannot send control message: serial connection not yet ready")
            return False
        # Announcement message
        pre_msg = ControlAnnouncementMessage(
            acknowledge=0, # No acknowledgement needed for announcement
            type=ControlPayloadType.MOTOR
        )
        logger.info("Sending control announcement message: %s", pre_msg.to_dict())
        self._serial.send(pre_msg.encode())

        # Actual control message
        rpm = floor(control.target_speed / MOTOR_SPEED_TRANSMISSION_FACTOR)
        msg = MotorControlMessage(
            acknowledge=self._get_next_acknowledgement_code(),
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
        msg = ControlAnnouncementMessage(
            acknowledge=self._get_next_acknowledgement_code(),
            type=ControlPayloadType.HEARTBEAT
        )
        logger.info("Sending heartbeat control message: %s", msg.to_dict())
        self._serial.send(msg.encode())
        return True

    async def start_processing(self) -> bool:
        """Start decoding incoming messages. Will return once the initial message is received but will continue afterwards. Returns True if the connection was successfully established, False otherwise."""
        if not self._worker:
            notifier = asyncio.get_running_loop().create_future()
            self._worker = asyncio.create_task(self._decoder_loop(notifier))
            try:
                await notifier
                if notifier.result():
                    logger.info("Decoder loop started successfully")
                    return True
                else:
                    logger.error("Decoder loop failed to start")
                    self._worker.cancel()
                    self._worker = None
            except asyncio.CancelledError:
                logger.info("Decoder loop stopped before connection was established")
        else:
            logger.warning("Decoder loop already running")
        return False

    def shutdown(self):
        """Stop decoding incoming messages."""
        if self._worker:
            self._worker.cancel()
            self._worker = None
