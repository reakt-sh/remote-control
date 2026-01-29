import av
import datetime
from fractions import Fraction
from PyQt5.QtCore import QObject, pyqtSignal
from utils.app_logger import logger

from globals import *
class Encoder(QObject):
    encode_ready = pyqtSignal(int, object, object)  # Emits frame_id, timestamp (as object to handle 64-bit), encoded_bytes
    def __init__(self, parent=None):
        super().__init__(parent)
        self.frame_rate = FRAME_RATE
        self.pixel_format = PIXEL_FORMAT
        self.h264_dump_path = H264_DUMP
        self.current_bitrate = MEDIUM_BITRATE
        self.min_bitrate = LOW_BITRATE
        self.max_bitrate = HIGH_BITRATE
        self.output_container = None
        self.stream = None
        self.enc_width = None
        self.enc_height = None
        self._pending_reinit = False  # Flag when bitrate change requires reinit

    def init_encoder(self, width: int, height: int):
        """(Re)initialize encoder for given resolution."""
        # Close any existing resources first
        self.close()
        self.enc_width = width
        self.enc_height = height
        self.output_container = av.open('pipe:', mode='w', format='mp4')
        fps_fraction = Fraction(self.frame_rate).limit_denominator(1000)
        self.stream = self.output_container.add_stream('h264', rate=fps_fraction)
        self.stream.pix_fmt = self.pixel_format
        self.stream.width = width
        self.stream.height = height
        # Base options
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
        self.update_encoder_parameters()
        logger.info(f"Encoder initialized ({width}x{height}) bitrate={self.current_bitrate}")

    def update_encoder_parameters(self):
        if not self.stream:
            return
        # Merge bitrate-related options
        self.stream.options = {
            **self.stream.options,
            'bitrate': str(self.current_bitrate),
            'bufsize': str(self.current_bitrate * 2),
            'maxrate': str(self.current_bitrate),
            'minrate': str(self.current_bitrate // 2),
        }
        if hasattr(self.stream, 'codec_context') and self.stream.codec_context:
            try:
                self.stream.codec_context.bit_rate = self.current_bitrate
            except Exception:
                pass

    def set_bitrate(self, new_bitrate: int, immediate: bool = True):
        # Clamp to allowed range
        old_bitrate = self.current_bitrate
        self.current_bitrate = max(self.min_bitrate, min(self.max_bitrate, new_bitrate))
        if old_bitrate != self.current_bitrate:
            if immediate and self.enc_width and self.enc_height:
                # Recreate encoder with same resolution
                self.init_encoder(self.enc_width, self.enc_height)
            else:
                self._pending_reinit = True
            logger.info(f"Encoder bitrate set to {self.current_bitrate} bps (old={old_bitrate})")
        else:
            logger.info(f"Encoder bitrate unchanged at {self.current_bitrate} bps")


    def encode_frame(self, frame_id, frame, width, height, log_callback=None):
        # Lazy init or reinit if resolution changed or pending bitrate reinit
        if (self.stream is None or
            self.enc_width != width or
            self.enc_height != height or
            self._pending_reinit):
            self.init_encoder(width, height)
            self._pending_reinit = False
        av_frame = av.VideoFrame.from_ndarray(frame, format='bgr24')
        try:
            packets = self.stream.encode(av_frame)
        except Exception as e:
            logger.error(f"Encoder error on frame {frame_id}: {e}. Attempting reinitialization.")
            # Try one reinit and retry once
            self.init_encoder(width, height)
            av_frame_retry = av.VideoFrame.from_ndarray(frame, format='bgr24')
            packets = self.stream.encode(av_frame_retry)
        for packet in packets:
            current_sps_pps = self.stream.codec_context.extradata
            encoded_frame = bytes(packet)
            timestamp = int(datetime.datetime.now().timestamp() * 1000)  # Current timestamp in milliseconds
            if len(encoded_frame) > 0:
                nal_type = encoded_frame[4] & 0x1F
                if log_callback:
                    if nal_type == 7:
                        log_callback(f"SPS NAL unit detected for Frame ID: {frame_id}")
                    elif nal_type == 8:
                        log_callback(f"PPS NAL unit detected for Frame ID: {frame_id}")
                    elif nal_type == 5:
                        log_callback(f"IDR NAL unit detected for Frame ID: {frame_id}")
                    elif nal_type == 1:
                        # print(f"P-frame NAL unit detected for Frame ID: {frame_id}")
                        pass
                    elif nal_type == 0:
                        log_callback(f"B-frame NAL unit detected for Frame ID: {frame_id}")

                if nal_type == 5:  # IDR frame
                    # Prepend SPS and PPS to the IDR frame
                    encoded_frame = current_sps_pps + encoded_frame
                self.encode_ready.emit(frame_id, timestamp, encoded_frame)


    def close(self):
        try:
            # Drain encoder if possible
            if self.stream:
                try:
                    for _ in self.stream.encode():
                        pass
                except Exception:
                    pass
            if self.output_container:
                try:
                    self.output_container.close()
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Error closing encoder container: {e}")
        finally:
            self.output_container = None
            self.stream = None