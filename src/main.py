
import sys
from pathlib import Path
import hashlib
from datetime import datetime

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
    QHBoxLayout,
    QMessageBox
)

class MainWindow(QMainWindow):
    projects_dir = Path(__file__).resolve().parent.parent / "projects"

    # dictionary mapping project id to project .json filepath
    proj_idschema: dict[str, Path] = {}
    proj_names: list[str] = []
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
        self.load_init_projects()

    def open_homepage(self):
        if self.curr_proj:
            self.pages.removeWidget(self.curr_proj)
            self.curr_proj = None

        self.pages.setCurrentWidget(self.home)
        self.update_label()

    def update_label(self):
        self.label.setText(str(self.pages.count()))

    def load_init_projects(self):
        self.proj_idschema.clear()
        self.proj_names.clear()

        # iterate through the projects folder
        for folder in self.projects_dir.iterdir():
            if folder.is_dir():
                # Split the folder name into two parts
                name, proj_id = folder.name.rsplit("_", 1)
                path_to_schema = self.projects_dir / folder.name / f"{folder.name}.json"

                self.proj_idschema[proj_id] = path_to_schema
                self.proj_names.append(name)

                # self.home.add_button(proj_id)

    def open_project(self, proj_id: str):
        # if the proj_id does not exist then give an error message
        if not proj_id in self.proj_idschema.keys():
            QMessageBox.warning(
                self,
                "Project Error",
                "Selected project does not exist. Ensure project folder is in your projects directory."
            )
            return

        # extract the project schema and input it into the constructor
        schema = self.proj_idschema[proj_id]
        proj = ProjectPage()

        self.curr_proj = proj
        self.pages.addWidget(proj)
        self.pages.setCurrentWidget(proj)
        self.update_label()

    def create_new_proj(self, name: str):
        # this ensures that no project shares a name
        # it adds a _num to the end of the name based on how many files it shares a name with
        proj_name: str = ""
        index: int = 0
        valid: bool = False
        while not valid:
            if index == 0: check = name
            else: check = name + "_" + str(index)

            if check in self.proj_names:
                index += 1
            else:
                proj_name = check
                valid = True

        # create general information for the project
        proj_id = self.generate_id(proj_name)
        proj_dir = proj_name + "_" + proj_id

        # create the main project folder
        project_path = self.projects_dir / proj_dir
        project_path.mkdir(parents=True, exist_ok=True)

        # add the project .json file into the main project folder

        # create the project folders (data, graphs, info) into the main project folder
        (project_path / "data").mkdir(exist_ok=True)
        (project_path / "graphs").mkdir(exist_ok=True)
        (project_path / "info").mkdir(exist_ok=True)

        # update open project names and ids
        self.proj_idschema[proj_id] = project_path
        self.proj_names.append(proj_name)
        # self.home.add_button(proj_id)

        self.open_project(proj_id)

    def generate_id(self, name: str):
        code = name + datetime.now().isoformat()
        hash_id = hashlib.sha256(code.encode()).hexdigest()
        return hash_id[9] # grab the first 9 digits as a 9-digit id

if __name__ == "__main__":
    app = QApplication(sys.argv)

    widget = MainWindow()
    widget.show()
    print("hello")
    app.exec()