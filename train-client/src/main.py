
import sys
import platform

def run_rpi5_client():
    from rpi5_client import RPi5Client

    # Create and start the client
    client = RPi5Client()

def run_train_client():
    from PyQt5.QtWidgets import QApplication
    from train_client import TrainClient

    app = QApplication(sys.argv)
    client = TrainClient()
    client.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    if "rpi" in platform.uname().release.lower():
        # run Raspberri Pi 5 client
        run_rpi5_client()
    else:
        # run Desktop Train client
        run_train_client()