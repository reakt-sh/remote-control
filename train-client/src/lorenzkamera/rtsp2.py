#!/usr/bin/env python3
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GObject, GLib

# Initialisiere GStreamer
Gst.init(None)

def on_bus_message(bus, message):
    t = message.type
    if t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print("GStreamer ERROR: {}: {}".format(err, debug))
    elif t == Gst.MessageType.STATE_CHANGED:
        # Gib nur die State-Änderungen der Pipeline aus
        old_state, new_state, _ = message.parse_state_changed()
        print("Pipeline state changed from {} to {}".format(
            old_state.value_nick, new_state.value_nick))

def probe_callback(pad, info):
    # Diese Funktion wird aufgerufen, wenn ein Buffer die Probe passiert
    print("Frame received: Buffer passed through probe.")
    return Gst.PadProbeReturn.OK

class PiCamRTSPServer:
    def __init__(self):
        # Erstelle den RTSP-Server, der auf Port 8554 lauscht
        self.server = GstRtspServer.RTSPServer()
        self.server.set_service("8554")
        self.server.connect("client-connected", self.on_client_connected)

        # Erstelle eine MediaFactory
        self.factory = GstRtspServer.RTSPMediaFactory()
        self.factory.set_shared(True)
        self.factory.connect("media-configure", self.on_media_configure)

        # Erstelle die GStreamer-Pipeline.
        # Hinweis: Wir haben hier ein "identity" mit dem Namen "probe" eingefügt,
        # um über einen Pad-Probe zu prüfen, ob Frames fließen.
        pipeline_str = (
            "( rpicamsrc preview=false ! "
            "video/x-raw,width=640,height=480,framerate=30/1 ! "
            "videoconvert ! identity name=probe ! "
            "x264enc tune=zerolatency bitrate=500 speed-preset=superfast ! "
            "rtph264pay config-interval=1 name=pay0 pt=96 )"
        )
        print("Starte Kamera mit Pipeline:")
        print(pipeline_str)
        self.factory.set_launch(pipeline_str)

        # Binde die MediaFactory an den Mountpunkt /stream
        mount_points = self.server.get_mount_points()
        mount_points.add_factory("/stream", self.factory)

        # Starte den RTSP-Server
        self.server.attach(None)

    def on_client_connected(self, server, client):
        print("Neuer Client verbunden: {}".format(client.get_connection()))

    def on_media_configure(self, factory, media):
        print("Media wird konfiguriert. Pipeline wird für den neuen Client erstellt.")
        element = media.get_element()
        # Bus-Watch hinzufügen, um Nachrichten der Pipeline anzuzeigen
        bus = element.get_bus()
        bus.add_signal_watch()
        bus.connect("message", on_bus_message)

        # Hole das "identity"-Element und füge einen Pad-Probe hinzu,
        # der anzeigt, ob Frames durchkommen.
        probe_element = element.get_by_name("probe")
        if probe_element:
            pad = probe_element.get_static_pad("src")
            if pad:
                pad.add_probe(Gst.PadProbeType.BUFFER, probe_callback)
            else:
                print("Fehler: 'probe' Element besitzt keinen src-Pad.")
        else:
            print("Fehler: 'probe' Element nicht gefunden in der Pipeline.")

    def run(self):
        loop = GLib.MainLoop()  # Verwende GLib.MainLoop (statt GObject.MainLoop)
        try:
            print("RTSP-Server läuft. Verbinde dich unter: rtsp://192.168.1.28:8554/stream")
            loop.run()
        except KeyboardInterrupt:
            print("Server wird beendet...")
            loop.quit()

if __name__ == '__main__':
    server = PiCamRTSPServer()
    server.run()
