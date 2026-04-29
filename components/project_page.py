
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QIcon
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
    QLabel
)

from pathlib import Path
import filecmp
import shutil
import json

from components.custom_dialogs import SingleFileGraph, DataInformation, MissingValueAnalysis
from components.custom_widgets import DataWindow, GraphWindow, InfoWindow

class ProjectPage(QMainWindow):
    dataframes = {}
    current_dataframe = ""

    def __init__(self, project_dir: Path, full_id: str):
        super().__init__()

        self.PROJECT_DIR = project_dir
        self.FULL_ID = full_id

        self.table_dialog = None
        self.info_dialog = None

        ## --- Tab window of different view modes --- ##
        self.data_tab = DataWindow(self.PROJECT_DIR)
        self.data_tab.file_selected.connect(self.import_datafile)
        self.data_tab.new_dataframe.connect(self.add_dataframe)

        self.graph_tab = GraphWindow(self.PROJECT_DIR)

        self.info_tab = InfoWindow()

        self.tabs = QTabWidget()
        self.tabs.addTab(self.data_tab, "Data Tables")
        self.tabs.addTab(self.graph_tab, "Graphs")
        self.tabs.addTab(self.info_tab, "Info Docs")

        ## --- Creation Sidebar --- ##
        upload_file_button = QPushButton("+")
        upload_file_button.clicked.connect(self.open_file)
        icon = QIcon(str(Path(__file__).resolve().parent.parent / "assets" / "icons" / "file-plus-corner.svg"))
        upload_file_button.setIcon(icon)

        single_file_graph = QPushButton("+")
        single_file_graph.clicked.connect(self.generate_table)
        icon = QIcon(str(Path(__file__).resolve().parent.parent / "assets" / "icons" / "chart-area.svg"))
        single_file_graph.setIcon(icon)

        get_data_info = QPushButton("+")
        get_data_info.clicked.connect(lambda: self.generate_data_info(1))
        icon = QIcon(str(Path(__file__).resolve().parent.parent / "assets" / "icons" / "file-text.svg"))
        get_data_info.setIcon(icon)

        missing_data_info = QPushButton("+")
        missing_data_info.clicked.connect(lambda: self.generate_data_info(2))

        self.graph_scroller = QScrollArea()
        self.graph_scroller.setWidgetResizable(True)
        self.graph_scroller.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.graph_container = QWidget()
        self.glayout = QVBoxLayout(self.graph_container)
        self.graph_scroller.setWidget(self.graph_container)
        self.glayout.addStretch()

        self.right_layout = QVBoxLayout()
        generator_buttons = QFormLayout()
        generator_buttons.addRow("Upload Data Source: ", upload_file_button)
        generator_buttons.addRow("Create Single-File Graph: ", single_file_graph)
        generator_buttons.addRow("See Data Information: ", get_data_info)
        generator_buttons.addRow("Missing Data Analysis: ", missing_data_info)
        self.right_layout.addLayout(generator_buttons)
        self.right_layout.addWidget(self.graph_scroller)

        self.right_widget = QWidget()
        self.right_widget.setLayout(self.right_layout)
        self.right_widget.setMinimumWidth(250)

        ## --- Some styling stuff --- ##
        # get the table's base color
        table_bg = self.data_tab.table.palette().color(QPalette.ColorRole.Base)

        # and to the graph container
        self.graph_container.setAutoFillBackground(True)
        palette = self.graph_container.palette()
        palette.setColor(QPalette.ColorRole.Window, table_bg)
        self.graph_container.setPalette(palette)

        ## ---- Main widget / layout container ---- ##
        self.main_container = QSplitter(Qt.Orientation.Horizontal)
        self.main_container.addWidget(self.tabs)
        self.main_container.addWidget(self.right_widget)
        self.main_container.setSizes([775, 175])

        self.setCentralWidget(self.main_container)

        # load the project schema
        self.load_schema()

    def load_schema(self):
        # grab the schema
        schema = self.grab_schema()

        # grab the individual components of the schema
        datasets = schema["datasets"]
        graphs = schema["graphs"]
        docs = schema["info_docs"]

        # process each component as necessary
        for file in datasets:
            self.data_tab.load_file(file)

        for file in graphs:
            src_path = self.PROJECT_DIR / "graphs" / file
            with src_path.open("r", encoding="utf-8") as f:
                metadata = json.load(f)
            self.graph_tab.load_graph(metadata)

        print("Schema loaded!")

    def save_schema(self):
        # create a blank schema and load in basic information
        proj_name, proj_id = self.FULL_ID.rsplit("_", 1)
        datasets = []
        graphs = []
        docs = []

        # iterate through the projects subfolders and load in subfolder info
        for subfolder in self.PROJECT_DIR.iterdir():
            if subfolder.is_dir():
                print(f"\nFolder: {subfolder.name}")

                # iterate through the items in each subdirectory
                for item in subfolder.iterdir():
                    if item.is_file():
                        print(f"File: {item.name}")

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

    def grab_schema(self):
        # grab and unpack the schema
        schema_path = self.PROJECT_DIR / (self.FULL_ID + ".json")
        with schema_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    # copies the newly loaded data source into the project directory
    def import_datafile(self, filepath: str):
        src = Path(filepath)
        data_dir = self.PROJECT_DIR / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        path = data_dir / src.name
        if path.exists(): # if the file already exists
            if filecmp.cmp(src, path, shallow=False): # and it's the same as the new file, then ignore it
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

    # copies the newly created graph's metadata into the project directory
    def import_graph(self, metadata: dict):
        graphs_dir = self.PROJECT_DIR / "graphs"
        graphs_dir.mkdir(parents=True, exist_ok=True)

        file_path = graphs_dir / (metadata["name"] + ".json")

        with open(file_path, "w", encoding="utf-8") as f:
            # indent=4 makes the nested structure visually clear
            json.dump(metadata, f, indent=2)

    def import_infofile(self):
        pass

    def add_dataframe(self, name, df):
        self.dataframes[name] = df

    def open_file(self):
        file_dialog = QFileDialog()
        filters = "Data Files (*.csv *.json *.xml *.xlsx);;CSV Files (*.csv);;JSON Files (*.json);;XML Files (*.xml);;Excel Files (*.xlsx)"
        filepath, _ = file_dialog.getOpenFileName(self, "Open CSV File", "", filters)

        self.import_datafile(filepath)
        self.data_tab.load_file(filepath)

    def generate_table(self):
        if len(self.dataframes) < 1:    # make sure there is at least one file loaded
            QMessageBox.information(self, "No Data Loaded","At least one dataset is required before a table can be created.")
            return

        # then open the popup for creating a table
        self.table_dialog = SingleFileGraph(self.dataframes, self)
        self.table_dialog.setModal(True)
        self.table_dialog.created_graph.connect(self._on_table_dialog_closed)
        self.table_dialog.open()

    def _on_table_dialog_closed(self, metadata):
        self.import_graph(metadata)
        self.graph_tab.load_graph(metadata)
        self.table_dialog = None

    def generate_data_info(self, num: int):
        if len(self.dataframes) < 1:  # make sure there is at least one file loaded
            QMessageBox.information(self, "No Data Loaded",
                                    "At least one dataset is required before data information be viewed.")
            return

        if num == 1:
            self.info_dialog = DataInformation(self.dataframes, self)
            self.info_dialog.setModal(True)
            self.info_dialog.created_doc.connect(self._on_info_dialog_closed)
            self.info_dialog.open()

        elif num == 2:
            self.info_dialog = MissingValueAnalysis(self.dataframes, self)
            self.info_dialog.setModal(True)
            self.info_dialog.finished.connect(self._on_info_dialog_closed_temp)
            self.info_dialog.open()

    def _on_info_dialog_closed(self, doc_name, doc_type, item):
        self.info_tab.add_info_doc(doc_name, doc_type, item)
        self.info_dialog = None

    def _on_info_dialog_closed_temp(self):
        self.info_dialog = None
