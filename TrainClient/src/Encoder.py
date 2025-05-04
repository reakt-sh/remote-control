import av
from fractions import Fraction
from PyQt5.QtCore import QObject, pyqtSignal
from globals import *
class Encoder(QObject):
    encode_ready = pyqtSignal(object)  # Emits the encoded bytes
    def __init__(self, parent=None):
        super().__init__(parent)
        self.width = FRAME_WIDTH
        self.height = FRAME_HEIGHT
        self.frame_rate = FRAME_RATE
        self.pixel_format = PIXEL_FORMAT
        self.h264_dump_path = H264_DUMP
        self.init_encoder()

    def init_encoder(self):
        # Create in-memory output container
        self.output_container = av.open('pipe:', mode='w', format='mp4')

        # Convert FPS to a fraction
        fps_fraction = Fraction(self.frame_rate).limit_denominator(1000)

        # Add H.264 video stream
        self.stream = self.output_container.add_stream('h264', rate=fps_fraction)
        self.stream.width = self.width
        self.stream.height = self.height
        self.stream.pix_fmt = self.pixel_format

        # Set some encoding options
        self.stream.options = {
            'g': '30',
            'gop_size': '30',
            'idr_interval': '30',
            'keyint_min': '30',
            'forced-idr': '1',
            'preset': 'fast',
            'level': '3.1',
            'crf': '23',
            'tune': 'zerolatency',
            'sc_threshold': '0',
            'x264-params': (
                'keyint=30:min-keyint=30:scenecut=0:'
                'force-idr=1:repeat_headers=1'
            ),
        }

    def encode_frame(self, frame_id, frame, log_callback=None):
        av_frame = av.VideoFrame.from_ndarray(frame, format='bgr24')
        for packet in self.stream.encode(av_frame):
            current_sps_pps = self.stream.codec_context.extradata
            packet_bytes = bytes(packet)
            if len(packet_bytes) > 0:
                nal_type = packet_bytes[4] & 0x1F
                if log_callback:
                    if nal_type == 7:
                        log_callback(f"SPS NAL unit detected for Frame ID: {frame_id}")
                    elif nal_type == 8:
                        log_callback(f"PPS NAL unit detected for Frame ID: {frame_id}")
                    elif nal_type == 5:
                        log_callback(f"IDR NAL unit detected for Frame ID: {frame_id}")
                    elif nal_type == 1:
                        print(f"P-frame NAL unit detected for Frame ID: {frame_id}")
                    elif nal_type == 0:
                        log_callback(f"B-frame NAL unit detected for Frame ID: {frame_id}")

                if nal_type == 5:  # IDR frame
                    self.encode_ready.emit(current_sps_pps)

                self.encode_ready.emit(packet_bytes)

    def close(self):
        self.output_container.close()