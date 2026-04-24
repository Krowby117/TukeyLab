
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
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
from components.custom_dialogs import SingleFileGraph, DataInformation, MissingValueAnalysis
from components.custom_widgets import DataWindow, GraphWindow, InfoWindow

class ProjectPage(QMainWindow):
    dataframes = {}
    def __init__(self):
        super().__init__()

        self.dataframes = {}
        self.current_dataframe = ""
        self.table_dialog = None
        self.info_dialog = None

        ## --- Actual table view of the selected file --- ##
        self.data_tab = DataWindow()
        self.data_tab.file_opened.connect(self.add_dataframe)

        self.graph_tab = GraphWindow()
        self.info_tab = InfoWindow()

        self.tabs = QTabWidget()
        self.tabs.addTab(self.data_tab, "Data Tables")
        self.tabs.addTab(self.graph_tab, "Graphs")
        self.tabs.addTab(self.info_tab, "Info Docs")

        ## --- Plotly visualizer sidebar --- ##
        single_file_graph = QPushButton("+")
        single_file_graph.clicked.connect(lambda: self.generate_table(1))

        multi_file_graph = QPushButton("+")
        multi_file_graph.clicked.connect(lambda: self.generate_table(2))

        get_data_info = QPushButton("+")
        get_data_info.clicked.connect(lambda: self.generate_data_info(1))

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
        generator_buttons.addRow("Create Single-File Graph: ", single_file_graph)
        generator_buttons.addRow("Create Multi-File Graph: ", multi_file_graph)
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

    def add_dataframe(self, name, df):
        self.dataframes[name] = df

    def generate_table(self, num: int):
        if num == 1:    # if making a single-file graph
            if len(self.dataframes) < 1:    # make sure there is at least one file loaded
                QMessageBox.information(self, "No Data Loaded","At least one dataset is required before a table can be created.")
                return

            # then open the popup for creating a table
            self.table_dialog = SingleFileGraph(self.dataframes, self)
            self.table_dialog.setModal(True)
            self.table_dialog.created_graph.connect(self._on_table_dialog_closed)
            self.table_dialog.open()

        if num == 2:  # if making a multi-file graph
            if len(self.dataframes) < 2:  # make sure there are at least two files loaded
                QMessageBox.information(self, "Not Enough Data Loaded","At least two datasets are required before a table can be created.")
                return

            QMessageBox.information(self, "Work In Progress","No functionality yet.")

    def _on_table_dialog_closed(self, metadata):
        self.graph_tab.add_graph(metadata)
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
