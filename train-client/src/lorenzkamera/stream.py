from flask import Flask, Response, stream_with_context
from picamera2 import Picamera2
from threading import Thread, Lock
import time
import io

app = Flask(__name__)

# Globaler Frame-Buffer und Lock für thread-sicheren Zugriff
frame_buffer = io.BytesIO()
buffer_lock = Lock()
clients = []  # Liste der verbundenen Clients

# Kamera-Setup
picam2 = Picamera2()
config = picam2.create_video_configuration(main={"size": (1280, 720), "format": "RGB888"})
picam2.configure(config)
picam2.start()

def update_frame():
    """Kontinuierliche Frame-Aufnahme und Verteilung an verbundene Clients."""
    global frame_buffer, buffer_lock, clients
    while True:
        # Erstelle einen neuen Buffer für jeden neuen Frame
        temp_buffer = io.BytesIO()
        
        # Bild in den temporären Buffer aufnehmen
        picam2.capture_file(temp_buffer, format="jpeg")
        
        # Frame in den globalen Buffer kopieren
        with buffer_lock:
            frame_buffer.seek(0)
            frame_buffer.write(temp_buffer.getvalue())
            frame_buffer.truncate()
            frame_data = frame_buffer.getvalue()

        # Broadcast: Sende den aktuellen Frame an alle verbundenen Clients
        disconnected_clients = []
        for client in clients:
            try:
                client.send(frame_data)
            except Exception:
                # Client konnte nicht erreicht werden, daher trennen
                disconnected_clients.append(client)

        # Entferne nicht erreichbare Clients
        for client in disconnected_clients:
            clients.remove(client)

        time.sleep(0.03)  # Bildrate stabilisieren (ca. 30 FPS)

class ClientConnection:
    """Verwaltung einer Client-Verbindung."""
    def __init__(self):
        self.queue = io.BytesIO()

    def send(self, data):
        """Sendet den Frame an den Client."""
        self.queue.seek(0)
        self.queue.write(data)
        self.queue.truncate()

    def get_frame(self):
        """Holt das aktuelle Frame."""
        self.queue.seek(0)
        return self.queue.read()

def generate(client):
    """Generator, der Frames für einen Client streamt."""
    while True:
        frame = client.get_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.03)  # Stabilisierung der Übertragung

@app.route('/video_feed')
def video_feed():
    client = ClientConnection()
    clients.append(client)
    return Response(stream_with_context(generate(client)), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return "<html><body><h1>Livestream</h1><img src='/video_feed'></body></html>"

if __name__ == '__main__':
    # Starte den Frame-Update-Thread
    frame_thread = Thread(target=update_frame)
    frame_thread.daemon = True
    frame_thread.start()

    # Flask-Server starten
    app.run(host='0.0.0.0', port=8080)
