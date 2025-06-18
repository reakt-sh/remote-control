import os
import time
import subprocess
from threading import Thread
from picamera2 import Picamera2

VIDEO_PATH_CAMERA1 = "/media/usb/videos/camera1"
VIDEO_PATH_CAMERA2 = "/media/usb/videos/camera2"

os.makedirs(VIDEO_PATH_CAMERA1, exist_ok=True)
os.makedirs(VIDEO_PATH_CAMERA2, exist_ok=True)

def record_video(camera_id, video_path, duration):
    camera = Picamera2(camera_num=camera_id)
    
    while True:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        raw_filename = os.path.join(video_path, f"camera{camera_id}_video_{timestamp}.mp4")
        
        print(f"Starte Aufnahme mit Kamera {camera_id}: {raw_filename}")
        
        video_config = camera.create_video_configuration(main={"size": (1280, 720)},controls={"FrameRate": 60})
        camera.configure(video_config)
        camera.start_and_record_video(raw_filename, duration=duration)
        
        print(f"Aufnahme abgeschlossen mit Kamera {camera_id}: {raw_filename}")
        
        camera.stop()
        
        converted_filename = os.path.join(video_path, f"camera{camera_id}_video_{timestamp}_converted.mp4")
        
        ffmpeg_command = [
            "ffmpeg",
            "-y",                 # Überschreibe Zieldatei ohne nachzufragen
            "-i", raw_filename,   # Eingabedatei
            "-c", "copy",         # Ohne erneute Kodierung -> nur Remux
            converted_filename
        ]
        
        print(f"Konvertiere Video mit ffmpeg: {converted_filename}")
        try:
            subprocess.run(ffmpeg_command, check=True)
            os.remove(raw_filename)
            print(f"Konvertierung erfolgreich. Original gelöscht: {raw_filename}")
        except subprocess.CalledProcessError as e:
            print(f"Fehler bei der Konvertierung des Videos: {e}")

def main():
    video_duration =  120
    
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
