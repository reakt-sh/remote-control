
import sys
import signal
import platform

def install_sigint_handler(app):
    """Quit the Qt event loop cleanly on Ctrl+C.

    Without this, KeyboardInterrupt is raised inside a Qt slot, and PyQt5
    aborts the process (SIGABRT/core dump) on unhandled slot exceptions.
    """
    from PyQt5.QtCore import QTimer

    signal.signal(signal.SIGINT, lambda *_: app.quit())
    # Periodically run Python code so the signal handler gets a chance to execute
    heartbeat = QTimer(app)
    heartbeat.start(1000) # 1 second
    heartbeat.timeout.connect(lambda: None)
    app._sigint_heartbeat = heartbeat

def run_rpi5_reaktor_client():
    from PyQt5.QtCore import QCoreApplication
    from rpi5_reaktor_client import RPi5ReaktorClient

    # Create and start the client
    app = QCoreApplication(sys.argv)
    install_sigint_handler(app)
    client = RPi5ReaktorClient()
    client.start()
    sys.exit(app.exec_())

def run_rpi5_client():
    from PyQt5.QtCore import QCoreApplication
    from rpi5_client import RPi5Client

    # Create and start the client
    app = QCoreApplication(sys.argv)
    install_sigint_handler(app)
    client = RPi5Client()
    client.start()
    sys.exit(app.exec_())

def run_train_client():
    from PyQt5.QtWidgets import QApplication
    from train_client import TrainClient

    app = QApplication(sys.argv)
    install_sigint_handler(app)
    client = TrainClient()
    client.show()
    sys.exit(app.exec_())

def run_reaktor_client():
    import asyncio
    from PyQt5.QtWidgets import QApplication
    from reaktor_client import ReaktorClient
    try:
        import qasync
        app = QApplication(sys.argv)
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        install_sigint_handler(app)

        client = ReaktorClient()
        client.show()

        with loop:
            loop.run_forever()
    except ImportError:
        # Fallback without qasync
        print("qasync not installed. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "qasync"])
        print("Please run the script again.")
        sys.exit(1)

def run_cli_client():
    from PyQt5.QtCore import QCoreApplication
    from cli_client import CLIClient

    # Create and start the CLI client
    app = QCoreApplication(sys.argv)
    install_sigint_handler(app)
    client = CLIClient()
    client.start()
    sys.exit(app.exec_())

"""
# ROS2: Import ROS2 libraries and message types
import rclpy
if __name__ == "__main__":
    rclpy.init()
"""

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        run_cli_client()
    elif (len(sys.argv) > 1 and sys.argv[1] == "reaktor"):
        run_reaktor_client()
    elif len(sys.argv) > 1 and sys.argv[1] == "rpi5_reaktor":
        run_rpi5_reaktor_client()
    elif "rpi" in platform.uname().release.lower():
        run_rpi5_client()
    else:
        run_train_client()