from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QVBoxLayout,
)
from PySide6.QtCore import Signal

class HomePage(QWidget):
    open_file = Signal(str)

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.new_proj_btn = QPushButton("Create New Project")
        layout.addWidget(self.new_proj_btn)

        self.new_proj_btn.clicked.connect(lambda: self.open_project("new"))

        self.setLayout(layout)

    def open_project(self, proj_id: str):
        self.open_file.emit(proj_id)