import asyncio
from typing import Optional
from src.utils.app_logger import logger

class VideoDatagramAssembler:
    def __init__(self, train_id: str):
        self.train_id = train_id
        self.current_frame = bytearray()
        self.current_frame_id = -1
        self.expected_packets = 0
        self.received_packets = 0
        self.frame_counter = 0
        self.start_time = None

    def process_packet(self, data: bytes) -> Optional[bytes]:
        try:
            # Ignoring first byte as packet_type = data[0]
            frame_id = int.from_bytes(data[1:5], byteorder='big')
            number_of_packets = int.from_bytes(data[5:7], byteorder='big')
            packet_id = int.from_bytes(data[7:9], byteorder='big')
            train_id = data[9:45].decode('utf-8').strip()
            payload = data[45:]

            if train_id != self.train_id:
                logger.warning(f"Packet train ID mismatch: expected {self.train_id}, got {train_id}")
                return None

            if frame_id != self.current_frame_id:
                # New frame
                self.current_frame = bytearray()
                self.current_frame_id = frame_id
                self.expected_packets = number_of_packets
                self.received_packets = 0

            self.current_frame.extend(payload)
            self.received_packets += 1

            if packet_id == number_of_packets and self.received_packets == self.expected_packets:
                # Complete frame received
                complete_frame = bytes(self.current_frame)
                self.current_frame = bytearray()

                if self.frame_counter == 0:
                    self.frame_counter += 1
                    self.start_time = asyncio.get_event_loop().time()
                else:
                    self.frame_counter += 1

                current_time = asyncio.get_event_loop().time()
                if current_time - self.start_time >= 1.0:
                    logger.info(f"Received {self.frame_counter} complete video frames in the last second for train {self.train_id}")
                    self.frame_counter = 0

                return complete_frame

            return None

        except Exception as e:
            logger.error(f"Error processing video packet: {e}")
            return None
