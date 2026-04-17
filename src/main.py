
import sys

from components.chatbot import ChatbotGUI
from components.user_eda import InteractiveEDA
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TukeyLab")
        self.setMinimumSize(1200, 800)

        self.eda = InteractiveEDA()

        self.setCentralWidget(self.eda)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    widget = MainWindow()
    widget.show()
    print("hello")
    app.exec()