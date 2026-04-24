
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
                if pd.isna(value):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem("-"))
                else:
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

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