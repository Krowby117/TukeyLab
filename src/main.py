
import sys

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
        self.home.new_file.connect(self.create_new_proj)

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
        # check if the proj_id exists, if so then open that project
        
        # extract the project name and input it into the constructor
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

    def create_new_proj(self, project_name: str):
        # check if the project name already exists, if it does then update it
            # add a number or something to it

        # create the main project folder

        # create the project .json file

        # create the project folders (data, graphs, info)

        self.open_project(project_name)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    widget = MainWindow()
    widget.show()
    print("hello")
    app.exec()