from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QToolButton,
    QGridLayout
)
from components.custom_dialogs import NewProjectDialog

from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QIcon
from pathlib import Path

class HomePage(QWidget):
    open_file = Signal(str)
    new_file = Signal(str)

    create_dialog = None

    def __init__(self):
        super().__init__()

        self.total_btns = 0
        self.num_columns = 6

        self.new_proj_btn = QToolButton()
        self.new_proj_btn.setText("New Project")
        self.new_proj_btn.setFixedSize(100, 100)
        self.new_proj_btn.clicked.connect(self.create_new_project)
        self.new_proj_btn.setStyleSheet("""
            QToolButton {
                border-radius: 10px;
                background-color: #2d2d2d;
                border: 1px solid #404040;
            }
            QToolButton:hover {
                background-color: #3d3d3d;
            }
        """)
        icon = QIcon(str(Path(__file__).resolve().parent.parent / "assets" / "icons" / "square-plus.svg"))
        self.new_proj_btn.setIcon(icon)
        self.new_proj_btn.setIconSize(QSize(80, 80))

        self.layout = QGridLayout(self)
        self.layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.layout.addWidget(self.new_proj_btn)
        self.total_btns += 1

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
        proj_btn = QToolButton()
        proj_btn.setText(proj_name)
        proj_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        proj_btn.clicked.connect(lambda: self.open_project(proj_id))
        proj_btn.setFixedSize(100, 100)
        proj_btn.setStyleSheet("""
            QToolButton {
                border-radius: 10px;
                background-color: #2d2d2d;
                border: 1px solid #404040;
            }
            QToolButton:hover {
                background-color: #3d3d3d;
            }
        """)
        icon = QIcon(str(Path(__file__).resolve().parent.parent / "assets" / "icons" / "folder-open.svg"))
        proj_btn.setIcon(icon)
        proj_btn.setIconSize(QSize(80, 80))

        # Calculate position based on current list length
        current_index = self.total_btns
        row = current_index // self.num_columns
        col = current_index % self.num_columns

        self.layout.addWidget(proj_btn, row, col)
        self.total_btns += 1
