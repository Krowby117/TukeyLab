
import sys
import os
import json
from pathlib import Path
import hashlib
from datetime import datetime

from components.project_page import ProjectPage
from components.basic_pages import HomePage

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QStackedWidget,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
    QToolBar,
    QStyle
)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt

from qt_material import apply_stylesheet
import qdarktheme

class MainWindow(QMainWindow):
    BASE_DIR = Path(__file__).resolve().parent.parent
    ICONS_PATH = BASE_DIR / "assets" / "icons"
    PROJECTS_DIR = BASE_DIR / "projects"

    # dictionary mapping project id to project name
    proj_id_name: dict[str, str] = {}
    curr_proj = None

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TukeyLab")
        self.setMinimumSize(1200, 800)

        self.home = HomePage()
        self.home.open_file.connect(self.open_project)
        self.home.new_file.connect(self.create_new_proj)

        self.pages = QStackedWidget()
        self.pages.addWidget(self.home)

        self.setCentralWidget(self.pages)

        self.create_toolbar()
        self.load_init_projects()

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        #toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)

        # Home button
        home_icon = QIcon(str(self.ICONS_PATH / "flask-conical.svg"))
        home_btn = QAction(home_icon, "TukeyLab", self)
        home_btn.triggered.connect(self.open_homepage)
        toolbar.addAction(home_btn)

        # # New File Action
        # new_act = QAction("New", self)
        # new_act.triggered.connect(lambda: self.editor.clear())
        # toolbar.addAction(new_act)
        #
        # # Open File Action
        # open_act = QAction("Open", self)
        # open_act.triggered.connect(self.open_file)
        # toolbar.addAction(open_act)
        #
        # # Save File Action
        # save_act = QAction("Save", self)
        # save_act.triggered.connect(self.save_file)
        # toolbar.addAction(save_act)

    def open_homepage(self):
        if self.curr_proj:
            self.curr_proj.save_schema()
            self.pages.removeWidget(self.curr_proj)
            self.curr_proj = None

        self.pages.setCurrentWidget(self.home)

    def load_init_projects(self):
        self.proj_id_name.clear()

        # iterate through the projects folder
        for folder in self.PROJECTS_DIR.iterdir():
            if folder.is_dir():
                # Split the folder name into two parts
                name, proj_id = folder.name.rsplit("_", 1)

                self.proj_id_name[proj_id] = name
                self.home.add_proj_button(name, proj_id)

    def open_project(self, proj_id: str):
        # if the proj_id does not exist then give an error message
        if not proj_id in self.proj_id_name.keys():
            QMessageBox.warning(
                self,
                "Project Error",
                "Selected project does not exist. Ensure project folder is in your projects directory."
            )
            return

        # extract the project schema and input it into the constructor
        full_id = self.proj_id_name[proj_id] + "_" + proj_id
        proj_dir = self.PROJECTS_DIR / full_id
        proj = ProjectPage(proj_dir, full_id)

        self.curr_proj = proj
        self.pages.addWidget(proj)
        self.pages.setCurrentWidget(proj)

    def create_new_proj(self, name: str):
        # this ensures that no project shares a name
        # it adds a _num to the end of the name based on how many files it shares a name with
        proj_name: str = ""
        index: int = 0
        valid: bool = False
        while not valid:
            if index == 0: check = name
            else: check = name + str(index)

            if check in self.proj_id_name.values():
                index += 1
            else:
                proj_name = check
                valid = True

        # create general information for the project
        proj_id = self.generate_id(proj_name)
        proj_dir = proj_name + "_" + proj_id

        # create the main project folder
        project_path = self.PROJECTS_DIR / proj_dir
        project_path.mkdir(parents=True, exist_ok=True)

        # add the project .json file into the main project folder
        path_to_schema = project_path / f"{proj_dir}.json"
        proj_schema = {
            "project_id": proj_id,
            "project_name": proj_name,
            "datasets": [],
            "graphs": [],
            "info_docs": []
        }
        with path_to_schema.open("w", encoding="utf-8") as f:
            json.dump(proj_schema, f, indent=2)

        # create the project folders (data, graphs, info) into the main project folder
        (project_path / "data").mkdir(exist_ok=True)
        #(project_path / "data" / "raw").mkdir(exist_ok=True)
        #(project_path / "data" / "clean").mkdir(exist_ok=True)
        (project_path / "graphs").mkdir(exist_ok=True)
        (project_path / "info").mkdir(exist_ok=True)

        # update open project names and ids
        self.proj_id_name[proj_id] = proj_name

        self.home.add_proj_button(proj_name, proj_id)
        self.open_project(proj_id)

    def generate_id(self, name: str):
        code = name + datetime.now().isoformat()
        hash_id = hashlib.sha256(code.encode()).hexdigest()
        return hash_id[:9] # grab the first 9 digits as a 9-digit id

if __name__ == "__main__":
    app = QApplication(sys.argv)

    theme_path = Path(__file__).resolve().parent.parent / "assets" / "themes" / "ElegantDark.qss"
    with open(theme_path, "r") as f:
        _style = f.read()
        app.setStyleSheet(_style)

    widget = MainWindow()
    widget.show()

    app.exec()