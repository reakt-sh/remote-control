"""
User-facing connectoion for managing communication with the vehicle.
"""

import logging
import asyncio
from typing import Callable
from inspect import iscoroutinefunction
from serial_asyncio import create_serial_connection
from .generated.config_communication import COMM_SERIAL_BAUDRATE, COMM_CONTROL_MESSAGE_HEARTBEAT_TIME
from .serial_connection_handler import SerialConnectionHandler
from .message_handler import MessageHandler
from .data import ConnectionProblem, Control, Status
from . import CONNECTOR_ROOT_LOGGER

logger = CONNECTOR_ROOT_LOGGER.getChild("connection")

class Connection:
    """Connection to the REAKTOR."""

    _serial: SerialConnectionHandler # Internal serial connection handler
    _decoder: MessageHandler # Message handler for en/decoding messages
    _heartbeat_task: asyncio.Task # Background task for automatic heartbeat
    _listeners: list[Callable[[Status], None]] # Listeners for status updates
    _listener_futures: list[asyncio.Future] # Futures for one-time status listeners
    _listener_tasks: set # Background tasks for async listeners
    _opened: bool # Connection established
    _problems: list[ConnectionProblem] # List of connection problems
    current_status: Status # Latest received status

    def __init__(self):
        self._serial = None
        self._decoder = None
        self._heartbeat_task = None
        self._opened = False
        self._listeners = []
        self._listener_futures = []
        self._listener_tasks = set()
        self._problems = []
        self.current_status = None

    # Internal API

    def _handle_error(self, problem: ConnectionProblem):
        """Register a connection problem."""
        self._problems.append(problem)
        self._notify_listeners(problem)

    def _handle_status(self, status: Status):
        """Store status and notify all registered listeners about a new status."""
        self.current_status = status
        self._notify_listeners(status)

    def _notify_listeners(self, event: Status | ConnectionProblem):
        """Notify all registered listeners about a new status or problem."""
        # One-time listeners
        for listener in self._listener_futures:
            if asyncio.isfuture(listener) and not listener.done():
                listener.set_result(event)
        self._listener_futures = []
        # Persistent listeners
        for listener in self._listeners:
            try:
                if iscoroutinefunction(listener):
                    task = asyncio.create_task(listener(event))
                    self._listener_tasks.add(task)
                    task.add_done_callback(self._listener_tasks.discard)
                else:
                    listener(event)
            except Exception as e:
                logger.error("Failed to notify status listener: %s", e)

    async def _heartbeat_loop(self):
        """Background task to send periodic heartbeat messages."""
        try:
            while True:
                if self._serial and self._serial.is_ready():
                    self._decoder.send_heartbeat()
                await asyncio.sleep((COMM_CONTROL_MESSAGE_HEARTBEAT_TIME / 1000) / 2 ) # Half heartbeat interval
        except asyncio.CancelledError:
            logger.info("Heartbeat loop cancelled")

    # Public API

    async def open(self, port: str, manual_heartbeat: bool = False):
        """Open the connection. ASYNC!"""
        if self._serial:
            logger.warning("Connection already opened")
            return
        # Create serial connection
        _, protocol = await create_serial_connection(asyncio.get_event_loop(), SerialConnectionHandler, port, baudrate=COMM_SERIAL_BAUDRATE)
        self._serial = protocol
        self._decoder = MessageHandler(protocol, self._handle_status, self._handle_error)
        # Wait until the connection is fully established (driver indicates connected)
        if await self._decoder.start_processing():
            self._opened = True
            logger.info("Communication established on port %s", port)
            # Start automatic heartbeat to detect connection loss
            if not manual_heartbeat:
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        else:
            logger.error("Failed to establish communication on port %s", port)
            raise ConnectionProblem("Failed to establish communication")

    async def get_next_status(self) -> Status | ConnectionProblem:
        """Get the next status when received. ASYNC! If you do not want to miss status messages, add a listener."""
        collector = asyncio.get_running_loop().create_future()
        self._listener_futures.append(collector)
        return await collector

    def get_current_status(self) -> Status:
        """Get the latest received status. If you do not want to miss status messages, add a listener."""
        return self.current_status

    def add_status_listener(self, listener: Callable[[Status | ConnectionProblem], None]):
        """Add a listener for status updates. Callback can be sync or async function. The pace of status updates is determined by control command responses and heartbeats. If you want to increase status updates send additional controls/heartbeats or switch to manual heartbeat mode."""
        self._listeners.append(listener)

    def get_problems(self) -> list[ConnectionProblem]:
        """Get the (mutable) list of connection problems."""
        return self._problems

    def send_control(self, control: Control) -> bool:
        """Send a control command."""
        return self._decoder.send_control(control)

    def send_heartbeat(self) -> bool:
        """Send a manual heartbeat signal. Only required if automatic heartbeat is disabled."""
        return self._decoder.send_heartbeat()

    def is_ready(self) -> bool:
        """Check if the connection is ready."""
        if open and self._serial:
            return self._serial.is_ready()
        return False

    def close(self):
        """Close the connection."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._serial:
            self._serial.close()

    def activate_file_logging(self, file_path: str, level: int = logging.WARNING):
        """Activate logging to a file."""
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        CONNECTOR_ROOT_LOGGER.addHandler(file_handler)
        CONNECTOR_ROOT_LOGGER.setLevel(level)
