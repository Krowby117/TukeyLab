
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPalette, QIcon, QAction
from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QStyle,
    QScrollArea,
    QSplitter,
    QSizePolicy,
    QMessageBox,
    QFormLayout,
    QTabWidget,
    QLabel,
    QStackedWidget,
    QToolBar
)

import pandas as pd
import seaborn as sns
from pathlib import Path
import filecmp
import shutil
import json

from components.custom_widgets import ButtonList, ItemCreationMenu, ItemViewer

def make_dataframe(filepath: str):
    # load the file path based on the type
    if filepath.endswith(".csv"):
        return pd.read_csv(filepath)
    elif filepath.endswith(".json"):
        return pd.read_json(filepath)
    elif filepath.endswith(".xml"):
        return pd.read_xml(filepath)
    elif filepath.endswith(".xlsx"):
        return pd.read_excel(filepath)
    else:
        raise ValueError("Unsupported file type")


class ProjectPage(QMainWindow):
    def __init__(self, project_dir: Path, full_id: str):
        super().__init__()

        self.PROJECT_DIR = project_dir
        self.FULL_ID = full_id
        self.project_dataframes = {}
        self.project_graphs = {}
        self.current_dataframe = ""

        # -- Set up the left bar -- #
        self.source_menu = ButtonList("Data Sources")
        self.source_menu.item_selected.connect(self._view_dataframe)

        self.created_items_menu = ButtonList("Created Items")
        self.created_items_menu.item_selected.connect(self._view_graph)

        top_padding = 10

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(10, top_padding, 10, 10)
        left_layout.setSpacing(5)
        left_layout.addWidget(self.source_menu, 1)
        left_layout.addWidget(self.created_items_menu, 2)
        left_layout.addStretch()

        left_container = QWidget()
        left_container.setLayout(left_layout)
        left_container.setFixedWidth(200)

        # -- Set up the middle widget -- #
        self.item_view = ItemViewer()

        # -- Set up the right bar -- #
        self.item_creation_menu = ItemCreationMenu()
        self.item_creation_menu.item_created.connect(self._handle_new_item)

        self.chat_window = QWidget()

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(10, top_padding, 10, 0)
        right_layout.setSpacing(15)
        right_layout.addWidget(self.item_creation_menu)
        right_layout.addWidget(self.chat_window, 1)

        right_container = QWidget()
        right_container.setLayout(right_layout)
        right_container.setFixedWidth(300)

        # ---- Set up main widget layout ---- #
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(left_container, 0)
        main_layout.addWidget(self.item_view, 3)
        main_layout.addWidget(right_container, 0)

        main_container = QWidget()
        main_container.setLayout(main_layout)

        self.setCentralWidget(main_container)
        self._load_schema()

    def _load_schema(self):
        # grab the schema
        schema_path = self.PROJECT_DIR / (self.FULL_ID + ".json")
        with schema_path.open("r", encoding="utf-8") as f:
            schema = json.load(f)

        # grab the individual components of the schema
        datasets = schema["datasets"]
        graphs = schema["graphs"]
        docs = schema["info_docs"]

        # process each component as necessary
        for file in datasets:
            self._load_file(file)

        for file in graphs:
            src_path = self.PROJECT_DIR / "graphs" / file
            with src_path.open("r", encoding="utf-8") as f:
                metadata = json.load(f)
            self._load_graph(metadata)

        for file in docs:
            self._load_doc(file)

    def save_schema(self):
        # create a blank schema and load in basic information
        proj_name, proj_id = self.FULL_ID.rsplit("_", 1)
        datasets = []
        graphs = []
        docs = []

        # iterate through the projects subfolders and load in subfolder info
        for subfolder in self.PROJECT_DIR.iterdir():
            if subfolder.is_dir():
                # iterate through the items in each subdirectory
                for item in subfolder.iterdir():
                    if item.is_file():
                        if subfolder.name == "data": datasets.append(item.name)
                        if subfolder.name == "graphs": graphs.append(item.name)
                        if subfolder.name == "info": docs.append(item.name)

        # load all information into a fresh schema
        proj_schema = {
            "project_id": proj_id,
            "project_name": proj_name,
            "datasets": datasets,
            "graphs": graphs,
            "info_docs": docs
        }

        # write the JSON file to the project folder
        schema_path = self.PROJECT_DIR / (self.FULL_ID + ".json")
        with schema_path.open("w", encoding="utf-8") as f:
            json.dump(proj_schema, f, indent=2)

    def _load_file(self, filepath):
        # create dataframe from source
        src_path = str(self.PROJECT_DIR / "data" / filepath)
        data = make_dataframe(src_path)

        # add dataframe to project's dataframes
        filename = filepath.split("/")[-1]  # grab the filename
        self.project_dataframes[filename] = data

        # update widget dataframes
        self.item_creation_menu.update_dataframes(self.project_dataframes)
        self.item_view.update_dataframes(self.project_dataframes)

        # update source buttons menu
        self.source_menu.add_button(filename)

    def _load_graph(self, metadata):
        name = metadata["name"]

        if name in self.project_graphs.keys():
            return

        # add it to the project's graphs
        self.project_graphs[name] = metadata

        # update created items menu
        self.created_items_menu.add_button(name)

    def _load_doc(self, metadata):
        pass

    # copies the newly loaded data source into the project directory
    def _import_datafile(self, filepath: str):
        src = Path(filepath)
        data_dir = self.PROJECT_DIR / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        path = data_dir / src.name
        if path.exists():  # if the file already exists
            if filecmp.cmp(src, path, shallow=False):  # and it's the same as the new file, then ignore it
                return
        else:
            shutil.copy2(src, path)  # preserves timestamps/metadata
            return

        stem, suffix = src.stem, src.suffix
        i = 1
        while path.exists():
            path = data_dir / f"{stem}_{i}{suffix}"
            if path.exists():
                if filecmp.cmp(src, path, shallow=False):
                    return
                i += 1
                continue

        shutil.copy2(src, path)  # preserves timestamps/metadata

    def _handle_new_item(self, item_data: list):
        item_type = item_data[0]
        metadata = item_data[1]

        if item_type == "data":
            self._import_datafile(metadata)
            self._load_file(metadata)
        elif item_type == "graph":
            self._import_graph(metadata)
            self._load_graph(metadata)

    # copies the newly created graph's metadata into the project directory
    def _import_graph(self, metadata: dict):
        graphs_dir = self.PROJECT_DIR / "graphs"
        graphs_dir.mkdir(parents=True, exist_ok=True)

        file_path = graphs_dir / (metadata["name"] + ".json")

        with open(file_path, "w", encoding="utf-8") as f:
            # indent=4 makes the nested structure visually clear
            json.dump(metadata, f, indent=2)

    def _view_dataframe(self, name: str):
        self.item_view.show_item("data", name)

    def _view_graph(self, name: str):
        metadata = self.project_graphs[name]
        self.item_view.show_item("graph", metadata)