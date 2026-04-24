
from PySide6.QtCore import Qt, Signal
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
    QFormLayout
)

import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure()
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)

class DataWindow(QWidget):
    file_opened = Signal(str, object)
    dataframes = {}
    curr_file = ""

    def __init__(self):
        super().__init__()

        self.table = QTableWidget()

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
        table_bg = self.table.palette().color(QPalette.ColorRole.Base)

        # apply it to the file container
        self.file_container.setAutoFillBackground(True)
        palette = self.file_container.palette()
        palette.setColor(QPalette.ColorRole.Window, table_bg)
        self.file_container.setPalette(palette)

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.left_widget)
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
                if pd.isna(value):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem("-"))
                else:
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

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
        self.dataframes[name] = data
        self.add_dataset_button(name)   # add the button

        # set it as the currently open dataset
        self.set_data(data)
        self.curr_file = name

        # emit the opened file and dataframe
        self.file_opened.emit(name, data)

    def add_dataset_button(self, name):
        btn = QToolButton()
        btn.setText(name)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.clicked.connect(lambda: self.switch_dataset(name))

        # Insert before the stretch widget
        self.flayout.insertWidget(self.flayout.count() - 1, btn)

    def switch_dataset(self, name):
        if name in self.dataframes.keys() and name != self.curr_file:
            self.curr_file = name
            self.set_data(self.dataframes[name])

class GraphWindow(QWidget):
    def __init__(self):
        super().__init__()

    def add_graph(self, metadata: str):
        pass


class InfoWindow(QWidget):
    def __init__(self):
        super().__init__()

    def add_doc(self, metadata: str):
        pass