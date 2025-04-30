import queue
import zmq
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, pyqtSlot


class NetworkWorker(QThread):
    packet_sent = pyqtSignal(int)  # Signal to emit when packet is sent

    def __init__(self, parent=None):
        super().__init__(parent)
        self.packet_queue = queue.Queue()
        self.running = True

    def run(self):
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        socket.bind("tcp://*:5555")

        while self.running:
            try:
                packet = self.packet_queue.get(timeout=0.1)
                if packet:
                    # For H.264 packets, we might want to send NAL units separately
                    # Here we'll just send the whole packet
                    socket.send(packet)
                    self.packet_sent.emit(len(packet))
            except queue.Empty:
                continue

        socket.close()
        context.term()

    def stop(self):
        self.running = False
        self.wait()

    def enqueue_packet(self, packet):
        self.packet_queue.put(packet)