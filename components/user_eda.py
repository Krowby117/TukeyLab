import plotly.express as px
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
    QSizePolicy
)
from numpy.matlib import empty
from components.helper_classes import TableMaker


class InteractiveEDA(QMainWindow):
    def __init__(self):
        super().__init__()

        self.dataframes = {}
        self.current_dataframe = ""

        ## --- Actual table view of the selected file --- ##
        self.data_viewer = DataViewer()
        self.data_viewer.setMinimumWidth(600)

        ## --- File loader sidebar --- ##
        self.upload_button = QPushButton("Open File")
        self.upload_button.clicked.connect(self.open_file)

        pixmap = QStyle.StandardPixmap.SP_DialogOpenButton
        icon = self.style().standardIcon(pixmap)
        self.upload_button.setIcon(icon)

        self.file_scroller = QScrollArea()
        self.file_scroller.setWidgetResizable(True)
        self.file_scroller.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.file_container = QWidget()
        self.flayout = QVBoxLayout(self.file_container)
        self.file_scroller.setWidget(self.file_container)
        self.flayout.addStretch()

        self.left_layout = QVBoxLayout()
        self.left_layout.addWidget(self.upload_button)
        self.left_layout.addWidget(self.file_scroller)

        self.left_widget = QWidget()
        self.left_widget.setLayout(self.left_layout)
        self.left_widget.setMinimumWidth(175)
        self.left_widget.setMaximumWidth(250)

        # get the table's base color
        table_bg = self.data_viewer.table.palette().color(QPalette.ColorRole.Base)

        # apply it to the file container
        self.file_container.setAutoFillBackground(True)
        palette = self.file_container.palette()
        palette.setColor(QPalette.ColorRole.Window, table_bg)
        self.file_container.setPalette(palette)

        ## --- Plotly visualizer sidebar --- ##
        self.new_graph_button = QPushButton("New Table")
        self.new_graph_button.clicked.connect(self.generate_table)

        self.graph_scroller = QScrollArea()
        self.graph_scroller.setWidgetResizable(True)
        self.graph_scroller.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.graph_container = QWidget()
        self.glayout = QVBoxLayout(self.graph_container)
        self.graph_scroller.setWidget(self.graph_container)
        self.glayout.addStretch()

        self.right_layout = QVBoxLayout()
        self.right_layout.addWidget(self.new_graph_button)
        self.right_layout.addWidget(self.graph_scroller)

        self.right_widget = QWidget()
        self.right_widget.setLayout(self.right_layout)
        self.right_widget.setMinimumWidth(250)

        ## --- Some styling stuff --- ##
        # get the table's base color
        table_bg = self.data_viewer.table.palette().color(QPalette.ColorRole.Base)

        # apply it to the file container
        self.file_container.setAutoFillBackground(True)
        palette = self.file_container.palette()
        palette.setColor(QPalette.ColorRole.Window, table_bg)
        self.file_container.setPalette(palette)

        # and to the graph container
        self.graph_container.setAutoFillBackground(True)
        palette = self.graph_container.palette()
        palette.setColor(QPalette.ColorRole.Window, table_bg)
        self.graph_container.setPalette(palette)

        ## ---- Main widget / layout container ---- ##
        self.main_container = QSplitter(Qt.Orientation.Horizontal)
        self.main_container.addWidget(self.left_widget)
        self.main_container.addWidget(self.data_viewer)
        self.main_container.addWidget(self.right_widget)
        self.main_container.setSizes([175, 600, 175])

        self.setCentralWidget(self.main_container)

    def open_file(self):
        file_dialog = QFileDialog()
        filters = "Data Files (*.csv *.json *.xml *.xlsx);;CSV Files (*.csv);;JSON Files (*.json);;XML Files (*.xml);;Excel Files (*.xlsx)"
        filepath, _ = file_dialog.getOpenFileName(self, "Open CSV File", "", filters)

        # load the file path based on the type
        if filepath.endswith(".csv"):
            data = pd.read_csv(filepath)
        elif filepath.endswith(".json"):
            data = pd.read_json(filepath)
        elif filepath.endswith(".xml"):
            data = pd.read_xml(filepath)
        elif filepath.endswith(".xlsx"):
            data = pd.read_excel(filepath)
        else:
            raise ValueError("Unsupported file type")

        # if the data doesn't exist, or it is empty,
        # then don't bother loading it into the viewer
        if data is None or data.empty:
            return

        name = filepath.split("/")[-1]  # grab the filename
        self.dataframes[name] = data      # add dataset to dictionary
        self.add_dataset_button(name)   # add the button

        # set it as the currently open dataset
        self.current_dataframe = name
        self.data_viewer.set_data(data)

    def generate_table(self):
        # if the dataset list is not valid then stop
        if not self.dataframes:
            return

        table_maker = TableMaker(self.dataframes)
        table_maker.exec()

    def add_dataset_button(self, name):
        btn = QToolButton()
        btn.setText(name)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.clicked.connect(lambda: self.switch_dataset(name))

        # Insert before the stretch widget
        # self.flayout.addWidget(btn)
        self.flayout.insertWidget(self.flayout.count() - 1, btn)

    def switch_dataset(self, name):
        if name in self.dataframes and name != self.current_dataframe:
            self.current_dataframe = name
            self.data_viewer.set_data(self.dataframes[name])

class DataViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.table = QTableWidget()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.table)

        self.setLayout(self.layout)

    def set_data(self, data):
        if data is None or data.empty:
            return

        # clear the existing table data
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

        # grab the headers
        headers = list(data.columns)
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        rows = data.values
        self.table.setRowCount(len(rows))

        # add the data into the table
        for row_idx, row in enumerate(rows):
            for col_idx, value in enumerate(row):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))