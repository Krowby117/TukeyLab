import sys
import tempfile
import os
import pandas as pd
import plotly.express as px

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPlainTextEdit


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("text editor test")
        self.resize(900, 600)

        self.text_editor = QPlainTextEdit()

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.text_editor)
        self.load_text()
        self.setCentralWidget(container)

    def load_text(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
