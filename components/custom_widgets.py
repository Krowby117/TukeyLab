
from PySide6.QtCore import Qt, Signal
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
    QLabel,
    QStackedWidget
)

import pandas as pd
import seaborn as sns
from pathlib import Path
import filecmp
import shutil
import json

from components.custom_dialogs import SingleFileGraph, DataInformation, MissingValueAnalysis
from components.helper_classes import MplCanvas

class ButtonList(QWidget):
    item_selected = Signal(str)

    def __init__(self):
        super().__init__()

        self._buttons = {}

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        scroll_area.setWidget(self.container)
        self.layout.addStretch()

        outer_layout = QVBoxLayout()
        outer_layout.addWidget(scroll_area)
        self.setLayout(outer_layout)

    def add_button(self, name: str):
        if name in self._buttons:
            return

        btn = QToolButton()
        btn.setText(name)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.clicked.connect(lambda: self._make_selection(name))
        self.layout.insertWidget(self.layout.count() - 1, btn)
        self._buttons[name] = btn

    def _make_selection(self, text: str):
        self.item_selected.emit(text)

class ItemCreationMenu(QWidget):
    item_created = Signal(list)

    def __init__(self):
        super().__init__()

        self.dataframes = {}
        self.popup = None

        # icon directory path
        icon_dir = Path(__file__).resolve().parent.parent / "assets" / "icons"

        # -- Setup each of the creation buttons -- #
        graph_creation = QPushButton("+")
        graph_creation.clicked.connect(self._open_graph_dialog)
        icon = QIcon(str(icon_dir / "chart-area.svg"))
        graph_creation.setIcon(icon)

        info_creation = QPushButton("+")
        info_creation.clicked.connect(self._open_info_dialog)
        icon = QIcon(str(icon_dir / "file-text.svg"))
        info_creation.setIcon(icon)

        layout = QFormLayout()
        layout.addRow("New Graph: ", graph_creation)
        layout.addRow("New Info Doc: ", info_creation)

        self.setLayout(layout)

    def update_dataframes(self, dfs):
        self.dataframes = dict(dfs)

    def _open_graph_dialog(self):
        if len(self.dataframes) < 1: # make sure there is at least one file loaded
            QMessageBox.information(self, "No Data Loaded",
                "At least one datasource is required before a table can be created.")
            return

        # then open the popup for creating a table
        self.popup = SingleFileGraph(self.dataframes)
        self.popup.setModal(True)
        self.popup.created_graph.connect(self._close_graph_dialog)
        self.popup.open()

    def _close_graph_dialog(self, metadata):
        # add the type of item created to the metadata and emit
        self.item_created.emit(["graph", metadata])

        # set popup to none
        self.popup = None

    def _open_info_dialog(self):
        if len(self.dataframes) < 1: # make sure there is at least one file loaded
            QMessageBox.information(self, "No Data Loaded",
                "At least one datasource is required before data information be viewed.")
            return

        # then open pop up for generating data info
        self.popup = DataInformation(self.dataframes, self)
        self.popup.setModal(True)
        self.popup.created_doc.connect(self._close_info_dialog)
        self.popup.open()

    def _close_info_dialog(self, doc_name, doc_type, item):
        # create the item metadata
        metadata = {
            "doc_name": doc_name,
            "doc_type": doc_type,
            "doc":     item
        }

        # emit the metadata and item type
        self.item_created.emit(["doc", metadata])

        # set popup to none
        self.popup = None

class ItemViewer(QWidget):
    single_file_graphs = [
        "Histogram",
        "Scatter Plot",
        "Box Plot",
        "Heatmap",
        "KDE Plot",
        "Correlation Matrix",
        #"Bar Chart",
        #"Pie Chart",
    ]

    curr_graph = ""

    def __init__(self):
        super().__init__()

        self.dataframes = {}

        # -- define the different item view types -- #
        self.table = QTableWidget()     # for viewing dataframes
        self.graph = MplCanvas()       # for viewing graphs
        self.doc = QWidget()           # for viewing docs

        self.view_stack = QStackedWidget()
        self.view_stack.addWidget(self.table)
        self.view_stack.addWidget(self.graph)
        self.view_stack.addWidget(self.doc)

        layout = QVBoxLayout()
        layout.addWidget(self.view_stack)
        self.setLayout(layout)

    def update_dataframes(self, dfs):
        self.dataframes = dict(dfs)

    def show_item(self, item_type: str, item_data):
        if item_type == "data":
            self._show_data(item_data)
        elif item_type == "graph":
            self._show_graph(item_data)
        elif item_type == "doc":
            self._show_doc(item_data)

    def _show_data(self, name: str):
        data = self.dataframes[name]
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

        # set the table as the active view
        self.view_stack.setCurrentWidget(self.table)

    def _show_graph(self, metadata):
        if metadata is None or not metadata:
            return

        # resets the plot area so a fresh graph gets updated
        fig = self.graph.figure
        fig.clear()
        self.graph.ax = fig.add_subplot(111)
        self.graph.draw()

        name = metadata["name"]
        graph_type = metadata["type"]
        data = metadata["data"]
        params = metadata["params"]

        if graph_type in self.single_file_graphs:
            df = self.dataframes[data[0]]
        else:
            raise ValueError("Unsupported graph type")

        if graph_type == "Histogram":
            feature = params["feature"]
            bins = params["bins"]

            self.graph.ax.hist(df[feature].dropna(), bins=bins)
            self.graph.ax.set_title(name)
            self.graph.ax.set_xlabel(feature)
            self.graph.ax.set_ylabel("Frequency")
            self.graph.draw()

        if graph_type == "Scatter Plot":
            scat_x = params["x"]
            scat_y = params["y"]

            self.graph.ax.scatter(df[scat_x], df[scat_y])
            self.graph.ax.set_title(f"{scat_x} vs. {scat_y}")
            self.graph.ax.set_xlabel(scat_x)
            self.graph.ax.set_ylabel(scat_y)
            self.graph.draw()

        if graph_type == "Box Plot":
            feature = params

            self.graph.ax.boxplot(df[feature].dropna(), vert=False)
            self.graph.ax.set_title(f"{feature} Box Plot")
            self.graph.draw()

        if graph_type == "Heatmap":
            hm_x = params["x"]
            hm_y = params["y"]

            data = df[[hm_x, hm_y]].apply(pd.to_numeric, errors='coerce').dropna()

            sns.heatmap(data, annot=True, cmap='coolwarm', ax=self.graph.ax)
            self.graph.ax.set_title(f"{hm_x} vs. {hm_y}")
            self.graph.draw()

        if graph_type == "KDE Plot":
            feature = params

            self.graph.ax.clear()
            df[feature].dropna().plot(kind='kde', ax=self.graph.ax)
            self.graph.ax.set_title(f"{feature} Distribution (KDE)")
            self.graph.draw()

        if graph_type == "Correlation Matrix":
            data = df.select_dtypes(include=["number"])
            corr = data.corr(numeric_only=True)

            sns.heatmap(corr, annot=True, cmap="coolwarm", ax=self.graph.ax, vmin=-1, vmax=1)
            self.graph.ax.set_title("Correlation Matrix")
            self.graph.draw()

        # set the graph as the active view
        self.view_stack.setCurrentWidget(self.graph)

    def _show_doc(self, metadata):
        pass
