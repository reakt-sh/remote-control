
import sys
from CameraClient import CameraClient
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = CameraClient()
    client.show()
    sys.exit(app.exec_())