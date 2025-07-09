
import sys
import platform

def run_rpi5_client():
    from PyQt5.QtCore import QCoreApplication
    from rpi5_client import RPi5Client

    # Create and start the client
    app = QCoreApplication(sys.argv)
    client = RPi5Client()
    client.start()
    sys.exit(app.exec_())

def run_train_client():
    from PyQt5.QtWidgets import QApplication
    from train_client import TrainClient

    app = QApplication(sys.argv)
    client = TrainClient()
    client.show()
    sys.exit(app.exec_())

def run_cli_client():
    from PyQt5.QtCore import QCoreApplication
    from cli_client import CLIClient

    # Create and start the CLI client
    app = QCoreApplication(sys.argv)
    client = CLIClient()
    client.start()
    sys.exit(app.exec_())

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        # run CLI client
        run_cli_client()
    elif "rpi" in platform.uname().release.lower():
        # run Raspberri Pi 5 client
        run_rpi5_client()
    else:
        # run Desktop Train client
        run_train_client()