#!/usr/bin/env python3
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GObject

# Initialisiere GStreamer
Gst.init(None)

def on_bus_message(bus, message):
    t = message.type
    if t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print("GStreamer ERROR: {}: {}".format(err, debug))
    elif t == Gst.MessageType.STATE_CHANGED:
        old_state, new_state, pending = message.parse_state_changed()
        # Hier geben wir alle State-Änderungen aus (optional: nur für die Pipeline)
        print("Pipeline state changed from {} to {}".format(
            old_state.value_nick, new_state.value_nick))

class PiCamRTSPServer:
    def __init__(self):
        # Erstelle einen RTSP-Server, der auf Port 8554 lauscht
        self.server = GstRtspServer.RTSPServer()
        self.server.set_service("8554")
        self.server.connect("client-connected", self.on_client_connected)
        
        # Erstelle eine MediaFactory für den Stream
        self.factory = GstRtspServer.RTSPMediaFactory()
        self.factory.set_shared(True)
        # Signal "media-configure" abfangen, um Debug-Ausgaben zu erzeugen
        self.factory.connect("media-configure", self.on_media_configure)
        
        # Definiere die GStreamer-Pipeline:
        # - rpicamsrc: liest den PiCam-Stream (ohne Vorschau)
        # - video/x-raw: legt Auflösung und Framerate fest (hier 640x480, 30fps)
        # - videoconvert: Formatkonvertierung
        # - x264enc: kodiert in H.264 (mit Low-Latency-Einstellungen)
        # - rtph264pay: verpackt den H.264-Stream in RTP-Pakete
        pipeline_str = (
            "( rpicamsrc preview=false ! "
            "video/x-raw,width=640,height=480,framerate=30/1 ! "
            "videoconvert ! "
            "x264enc tune=zerolatency bitrate=500 speed-preset=superfast ! "
            "rtph264pay config-interval=1 name=pay0 pt=96 )"
        )
        print("Starte Kamera mit Pipeline:")
        print(pipeline_str)
        self.factory.set_launch(pipeline_str)
        
        # Hänge die MediaFactory an den Mountpunkt /stream
        mount_points = self.server.get_mount_points()
        mount_points.add_factory("/stream", self.factory)
        
        # Starte den RTSP-Server
        self.server.attach(None)

    def on_client_connected(self, server, client):
        # Hier kannst du zusätzliche Informationen über den Client ausgeben
        print("Neuer Client verbunden: {}".format(client.get_connection()))
    
    def on_media_configure(self, factory, media):
        print("Media wird konfiguriert. Pipeline wird für den neuen Client erstellt.")
        element = media.get_element()
        # Füge einen Bus-Watch hinzu, um Nachrichten der Pipeline anzuzeigen
        bus = element.get_bus()
        bus.add_signal_watch()
        bus.connect("message", on_bus_message)

    def run(self):
        loop = GObject.MainLoop()
        try:
            print("RTSP-Server läuft. Verbinde dich unter: rtsp://192.168.1.28:8554/stream")
            loop.run()
        except KeyboardInterrupt:
            print("Server wird beendet...")
            loop.quit()

if __name__ == '__main__':
    server = PiCamRTSPServer()
    server.run()
