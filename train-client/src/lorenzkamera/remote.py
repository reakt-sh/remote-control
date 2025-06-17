#!/usr/bin/env python3
import io
import socketserver
from http import server
from threading import Thread, Condition
import time
import cv2
from picamera2 import Picamera2

# HTML-Seite, die den Stream einbettet
PAGE = """\
<html>
  <head>
    <title>Raspberry Pi 5 Kamera-Stream</title>
  </head>
  <body>
    <center><h1>Raspberry Pi 5 Kamera-Stream</h1></center>
    <center><img src="stream.mjpg" width="1280" height="720"></center>
  </body>
</html>
"""

# Klasse, die den aktuell kodierten JPEG-Frame hält und Clients benachrichtigt
class StreamingOutput:
    def __init__(self):
        self.frame = None
        self.condition = Condition()

# HTTP-Request-Handler, der den MJPEG-Stream liefert
class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # Umleiten auf Index
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', '0')
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', str(len(frame)))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                print("Streaming-Client {} entfernt: {}".format(self.client_address, e))
        else:
            self.send_error(404)
            self.end_headers()

# Multithreaded HTTP-Server
class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

# In einem separaten Thread werden kontinuierlich Frames erfasst, zu JPEG kodiert
def capture_frames():
    # Ziel-FPS (hier ca. 24fps)
    delay = 1 / 24.0
    while True:
        # Erhalte ein aktuelles Frame als NumPy-Array (RGB888)
        frame = picam2.capture_array()
        # Optional: Falls erforderlich, in BGR umwandeln (JPEG-Encoding funktioniert meist ohne Umwandlung)
        # frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        with output.condition:
            output.frame = jpeg.tobytes()
            output.condition.notify_all()
        time.sleep(delay)

if __name__ == '__main__':
    # Erstelle Picamera2-Objekt
    picam2 = Picamera2()
    # Konfiguriere die Kamera im RGB-Modus (da MJPEG vom Sensor nicht unterstützt wird)
    config = picam2.create_video_configuration(main={"format": "RGB888", "size": (1280, 720)})
    picam2.configure(config)

    # Output-Puffer erstellen
    output = StreamingOutput()

    # Starte die Kamera (im Vorschaumodus)
    picam2.start()

    # Starte einen separaten Thread zur kontinuierlichen Frame-Erfassung und JPEG-Kodierung
    capture_thread = Thread(target=capture_frames)
    capture_thread.daemon = True
    capture_thread.start()

    # Starte den HTTP-Server auf Port 8332
    address = ('', 8332)
    try:
        streaming_server = StreamingServer(address, StreamingHandler)
        print("Server gestartet. Im Browser aufrufen unter: http://<RPi-IP>:8332")
        streaming_server.serve_forever()
    except KeyboardInterrupt:
        print("Stream wird beendet...")
    finally:
        picam2.stop()
