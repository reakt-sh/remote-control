import threading

from connection_info import get_network_connection
from models import NtpSyncResult
from sntp_client import SntpClient

SYNC_PERIOD_SECONDS = 2.0


class _Signal:
    def __init__(self):
        self._callbacks = []

    def connect(self, callback):
        self._callbacks.append(callback)

    def emit(self, *args):
        for cb in self._callbacks:
            cb(*args)


class NtpSyncThread:

    def __init__(self, client: SntpClient, host: str, period_seconds: float = SYNC_PERIOD_SECONDS):
        self.finished = _Signal()  # Emits NtpSyncResult
        self._client = client
        self._host = host
        self._period_seconds = period_seconds
        self._thread = None
        self._stop_event = threading.Event()

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def join(self, timeout=None):
        if self._thread:
            self._thread.join(timeout=timeout)

    def _run(self):
        while not self._stop_event.is_set():
            network_connection = get_network_connection(self._host)
            result: NtpSyncResult = self._client.query_server(self._host)
            result.network_connection = network_connection
            self.finished.emit(result)
            self._stop_event.wait(self._period_seconds)
