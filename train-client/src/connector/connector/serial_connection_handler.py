import logging
import asyncio
from serial_asyncio import SerialTransport

logger = logging.getLogger("connector:internal:serial")

class SerialConnectionHandler(asyncio.Protocol):
    """Internal serial connection to the REAKTOR driver."""
    _transport: SerialTransport # Low-level serial transport handler
    _buffer: bytearray # Buffer queue for incoming data
    _consumer: asyncio.Future # Consumer waiting for data

    # Internal API

    def __init__(self):
        super().__init__()
        self._transport = None
        self._buffer = bytearray()
        self._consumer = None

    def connection_made(self, transport):
        self._transport = transport
        logger.info("Serial connection established")

    def connection_lost(self, exc):
        logger.error("Serial connection lost")

    def data_received(self, data):
        logger.debug("Serial data received: %s", data.hex())
        self._buffer.extend(data)
        if self._consumer and not self._consumer.done():
            self._consumer.set_result(True)

    # Pubic API

    async def consume(self, num_bytes: int) -> bytes:
        """Consume a number of bytes from the buffer."""
        # Wait for data if needed
        if len(self._buffer) < num_bytes:
            if self._consumer and not self._consumer.done():
                raise Exception("Unsupported Operation: Cannot have multiple consumers waiting for data on the same serial connection.")
            self._consumer = asyncio.get_event_loop().create_future()
            await self._consumer
        # Retrieve data from buffer
        data = self._buffer[:num_bytes]
        self._buffer = self._buffer[num_bytes:]
        return bytes(data)

    def send(self, data: bytes):
        """Send a data to the driver."""
        if not self._transport:
            logger.error("Cannot send data: serial connection not yet established")
            return
        logger.debug("Sending data: %s", data.hex())
        self._transport.write(data)

    def is_ready(self) -> bool:
        """Check if the serial connection is ready."""
        return self._transport

    def close(self):
        """Close the serial connection."""
        if self._transport:
            self._transport.close()
            logger.info("Serial connection closed")
