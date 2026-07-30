import av
import threading
import time
from app_logger import logger
from globals import CAMERA_TYPE


# RTSP_URL_FRONT = "rtsp://reaktorpi2.local:8554/cam"
# RTSP_URL_REAR = "rtsp://reaktorpi5.local:8554/cam"
# RTSP_URL_FRONT = "rtsp://localhost:8554/cam1"
# RTSP_URL_REAR = "rtsp://localhost:8554/cam2"
# RTSP_URL_FRONT = "rtsp://admin:rtsysrocks42@192.168.1.42:554/H264/ch1/main/av_stream"
# RTSP_URL_REAR = "rtsp://admin:rtsysrocks42@192.168.1.30:554/H264/ch1/main/av_stream"

RTSP_URL_FRONT = "rtsp://admin:rtsysrocks42@192.168.88.248:554/H264/ch1/main/av_stream"
RTSP_URL_REAR = "rtsp://admin:rtsysrocks42@192.168.88.249:554/H264/ch1/main/av_stream"
RECONNECT_DELAY = 2.0  # seconds between reconnect attempts


class _Signal:
    """Lightweight callback signal, drop-in for pyqtSignal in non-Qt threads."""

    def __init__(self):
        self._callbacks = []

    def connect(self, callback):
        self._callbacks.append(callback)

    def emit(self, *args):
        for cb in self._callbacks:
            cb(*args)


class RTSPStream:

    def __init__(self, url: str = RTSP_URL_FRONT):
        self.frame_ready = _Signal()
        self.url = url
        self._thread = None
        self._running = False
        self.frame_count = 0
        self.width = 0
        self.height = 0
        self.camera_type = CAMERA_TYPE["FRONT"] if url == RTSP_URL_FRONT else CAMERA_TYPE["REAR"]

    def init_capture(self):
        self._running = True
        self._thread = threading.Thread(target=self._stream_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None

    def set_speed(self, speed: int):
        """No-op: speed control is not applicable to an RTSP stream."""
        pass

    def set_direction(self, direction: str):
        """No-op: direction control is not applicable to an RTSP stream."""
        pass

    def _open_stream(self):
        """Open RTSP stream with TCP transport, return (container, video_stream)."""
        container = av.open(
            self.url,
            options={
                "rtsp_transport": "tcp",
                "stimeout": "5000000",        # socket timeout 5 s (µs)
                "max_delay": "500000",         # max mux delay 0.5 s (µs)
                "fflags": "nobuffer",
                "flags": "low_delay",
                "analyzeduration": "1000000",  # probe duration 1 s (µs)
            },
        )
        video_stream = container.streams.video[0]
        video_stream.thread_type = "AUTO"
        return container, video_stream

    def _stream_loop(self):
        while self._running:
            container = None
            try:
                logger.info(f"Connecting to RTSP stream: {self.url}")
                container, video_stream = self._open_stream()

                self.width = video_stream.width
                self.height = video_stream.height

                fps = float(video_stream.average_rate) if video_stream.average_rate else 0.0
                logger.info(
                    f"RTSP stream opened: {self.width}x{self.height}"
                    f" @ {fps:.1f} fps"
                )

                for packet in container.demux(video_stream):
                    if not self._running:
                        break
                    if packet.size == 0:
                        continue  # end-of-stream flush packet

                    self.frame_count += 1
                    self.frame_ready.emit(
                        self.frame_count,
                        bytes(packet),
                        self.width,
                        self.height,
                        True,
                        self.camera_type
                    )

            except Exception as e:
                if self._running:
                    logger.error(
                        f"RTSP stream error: {e}. Reconnecting in {RECONNECT_DELAY}s..."
                    )
                    time.sleep(RECONNECT_DELAY)
            finally:
                if container is not None:
                    try:
                        container.close()
                    except Exception:
                        pass

    def set_speed(self, speed: int):
        """No-op: speed control is not applicable to an RTSP stream."""
        pass
