from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QVBoxLayout,
)
from components.custom_dialogs import NewProjectDialog
from components.custom_widgets import MplCanvas

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from pathlib import Path

class HomePage(QWidget):
    open_file = Signal(str)
    new_file = Signal(str)

    create_dialog = None

    def __init__(self):
        super().__init__()


        self.new_proj_btn = QPushButton("Create New Project")
        self.new_proj_btn.clicked.connect(self.create_new_project)
        icon = QIcon(str(Path(__file__).resolve().parent.parent / "assets" / "icons" / "square-plus.svg"))
        self.new_proj_btn.setIcon(icon)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.new_proj_btn)

        self.setLayout(self.layout)

    def open_project(self, proj_id: str):
        self.open_file.emit(proj_id)

    def create_new_project(self):
        self.create_dialog = NewProjectDialog()
        self.create_dialog.setModal(True)
        self.create_dialog.created.connect(self.create_project)
        self.create_dialog.open()

    def create_project(self, name: str):
        self.new_file.emit(name)

    def add_proj_button(self, proj_name: str, proj_id: str):
        proj_btn = QPushButton(proj_name)
        proj_btn.clicked.connect(lambda: self.open_project(proj_id))

        icon = QIcon(str(Path(__file__).resolve().parent.parent / "assets" / "icons" / "folder-open.svg"))
        proj_btn.setIcon(icon)

        self.layout.addWidget(proj_btn)
