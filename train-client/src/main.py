
import sys
from PyQt5.QtWidgets import QApplication
from train_client import TrainClient

if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = TrainClient()
    client.show()
    sys.exit(app.exec_())