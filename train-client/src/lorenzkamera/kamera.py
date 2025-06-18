import os
import time
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
        filename = os.path.join(video_path, f"camera{camera_id}_video_{timestamp}.mp4")
        print(f"Starte Aufnahme mit Kamera {camera_id}: {filename}")
        camera.start_and_record_video(filename, duration=duration)
        print(f"Aufnahme abgeschlossen mit Kamera {camera_id}: {filename}")
        camera.stop()

def main():
    video_duration = 120

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
