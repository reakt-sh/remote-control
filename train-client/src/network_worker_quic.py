import asyncio
import queue
import ssl
import threading

from PyQt5.QtCore import QThread
from aioquic.asyncio import connect
from aioquic.quic.configuration import QuicConfiguration

from globals import *


class NetworkWorkerQUIC(threading.Thread):
    def __init__(self, train_client_id, parent=None):
        super().__init__(parent)
        self.train_client_id = train_client_id
        self.train_client_id_bytes = train_client_id.encode('utf-8')

        self.configuration = QuicConfiguration(is_client=True)
        self.configuration.verify_mode = ssl.CERT_NONE  # For testing, disable verification mode

        self.server_host = QUIC_HOST
        self.server_port = QUIC_PORT
        self.frame_queue = queue.Queue()
        self.running = False
        self.loop = None
        print(f"QUIC: server URL: {self.server_host}:{self.server_port}")


    def run(self):
        self.running = True
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.quic_sender())
        finally:
            self.loop.close()

    async def quic_sender(self):
        print("QUIC: Sender task started")
        try:
            async with connect(
                self.server_host,
                self.server_port,
                configuration=self.configuration,
            ) as client:
                if client is None:
                    print("QUIC: connection failed")
                    return
                else:
                    print(f"QUIC: connection established: {client._quic._peer_cid}")
                # Send train identification first
                stream_id = client._quic.get_next_available_stream_id()
                handshake = f"TRAIN:{self.train_client_id}".encode()
                client._quic.send_stream_data(stream_id, handshake)
                print(f"QUIC: handshake sent, stream ID: {stream_id}")
                result = client.transmit()
                if result is not None:
                    await result
                print(f"QUIC: the loop is starting with stream id: {stream_id}")

                while self.running:
                    try:
                        (frame_id, frame) = self.frame_queue.get_nowait()
                        packet_list = self.get_packets(frame_id, frame)
                        for packet in packet_list:
                            client._quic.send_stream_data(stream_id, packet)
                            result = client.transmit()
                            if result is not None:
                                await result
                    except queue.Empty:
                        await asyncio.sleep(0.01)
                    except Exception as e:
                        print(f"QUIC: sender error: {e}")
                        break
        except Exception as e:
            print(f"QUIC: connection failed: {type(e).__name__}: {e}")

    def stop(self):
        self.running = False

    def get_packets(self, frame_id, frame):
        # Header = 1 byte for packet type, 4 byte for frame_id, 2 byte for number of packets, 2 byte for packet_id, 36 byte for train_id
        number_of_packets = (len(frame) // MAX_PACKET_SIZE) + 1
        packet_id = 1
        packet_list = []
        while(len(frame) > MAX_PACKET_SIZE):
            header = bytearray()
            header.append(PACKET_TYPE["video"])
            header.extend(frame_id.to_bytes(4, byteorder='big'))
            header.extend(number_of_packets.to_bytes(2, byteorder='big'))
            header.extend(packet_id.to_bytes(2, byteorder='big'))
            header.extend(self.train_client_id_bytes)
            packet = header + frame[:MAX_PACKET_SIZE]
            packet_list.append(packet)

            # remove the first MAX_PACKET_SIZE bytes from the frame
            frame = frame[MAX_PACKET_SIZE:]
            packet_id += 1

        # send the last packet
        header = bytearray()
        header.append(PACKET_TYPE["video"])
        header.extend(frame_id.to_bytes(4, byteorder='big'))
        header.extend(number_of_packets.to_bytes(2, byteorder='big'))
        header.extend(packet_id.to_bytes(2, byteorder='big'))
        header.extend(self.train_client_id_bytes)
        packet = header + frame
        packet_list.append(packet)
        return packet_list


    def enqueue_frame(self, frame_id, frame):
        self.frame_queue.put((frame_id, frame))