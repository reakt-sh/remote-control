import os
import time
import subprocess
from threading import Thread

VIDEO_PATH_CAMERA1 = "/media/usb/videos/camera1"
VIDEO_PATH_CAMERA2 = "/media/usb/videos/camera2"

os.makedirs(VIDEO_PATH_CAMERA1, exist_ok=True)
os.makedirs(VIDEO_PATH_CAMERA2, exist_ok=True)

def record_video(camera_id, video_path, duration):
    """
    Nimmt ein Video von /dev/videoX (X = camera_id) auf und schreibt es
    im fragmentierten MP4-Format (fMP4), sodass keine nachträgliche
    Konvertierung nötig ist.
    """
    while True:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(video_path, f"camera{camera_id}_video_{timestamp}.mp4")
        
        print(f"[Kamera {camera_id}] Starte Aufnahme: {filename}")
        
        command = [
            "ffmpeg",
            "-y",                    # Überschreibe bestehende Dateien ohne Nachfrage
            "-f", "v4l2",            # Eingang: V4L2-Gerät
            "-framerate", "30",      # Beispiel: 30 FPS
            "-video_size", "640x480",# Beispiel-Auflösung
            "-t", str(duration),     # Aufnahme-Dauer in Sekunden
            "-i", f"/dev/video{camera_id}",  # Kamera-Gerät
            "-c:v", "copy",          # Videostream unverändert kopieren (keine Neukodierung)
            "-f", "mp4",             # Ausgabecontainer MP4
            "-movflags", "frag_keyframe+empty_moov",
            filename
        ]
        
        try:
            subprocess.run(command, check=True)
            print(f"[Kamera {camera_id}] Aufnahme beendet: {filename}")
        except subprocess.CalledProcessError as e:
            print(f"[Kamera {camera_id}] Fehler bei ffmpeg: {e}")

def main():
    video_duration = 20
    
    try:
        thread1 = Thread(target=record_video, args=(0, VIDEO_PATH_CAMERA1, video_duration))
        thread2 = Thread(target=record_video, args=(1, VIDEO_PATH_CAMERA2, video_duration))

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

    except KeyboardInterrupt:
        print("Beende Programm...")

if __name__ == "__main__":
    main()
