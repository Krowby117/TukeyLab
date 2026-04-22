
import sys

from PySide6.QtGui import QVector2DList

from components.user_eda import ProjectPage
from components.basic_pages import HomePage
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QStackedWidget,
    QPushButton,
    QHBoxLayout
)

class MainWindow(QMainWindow):
    curr_proj = None
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TukeyLab")
        self.setMinimumSize(1200, 800)

        self.home_btn = QPushButton("Home")
        self.home_btn.clicked.connect(self.open_homepage)

        self.label = QLabel("")

        self.menu_bar = QHBoxLayout()
        self.menu_bar.addWidget(self.home_btn)
        self.menu_bar.addWidget(self.label)

        self.home = HomePage()
        self.home.open_file.connect(self.open_project)

        self.pages = QStackedWidget()
        self.pages.addWidget(self.home)

        layout = QVBoxLayout()
        layout.addLayout(self.menu_bar)
        layout.addWidget(self.pages)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

        self.update_label()

    def open_project(self, proj_id: str):
        proj = ProjectPage()

        self.curr_proj = proj
        self.pages.addWidget(proj)
        self.pages.setCurrentWidget(proj)
        self.update_label()

    def open_homepage(self):
        if self.curr_proj:
            self.pages.removeWidget(self.curr_proj)
            self.curr_proj = None

        self.pages.setCurrentWidget(self.home)
        self.update_label()

    def update_label(self):
        self.label.setText(str(self.pages.count()))

if __name__ == "__main__":
    app = QApplication(sys.argv)

    widget = MainWindow()
    widget.show()
    print("hello")
    app.exec()