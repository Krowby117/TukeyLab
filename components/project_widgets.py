from importlib.metadata import metadata

from PySide6.QtCore import Qt, Signal, QUrl, QSize
from PySide6.QtGui import QPalette, QIcon, QColor
from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QToolButton,
    QToolBar,
    QVBoxLayout,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QStyle,
    QScrollArea,
    QSizePolicy,
    QMessageBox,
    QFormLayout,
    QLabel,
    QStackedWidget,
    QHBoxLayout,
    QPlainTextEdit,
    QTextEdit
)

import pandas as pd
import seaborn as sns
from pathlib import Path
import tempfile
import filecmp
import shutil
import json

from components.custom_dialogs import SingleFileGraph, DataInformation
from components.helper_widgets import PlotlyWebEngine, NotesWidget


class WrappingButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setText("")

        self._label = QLabel(text, self)
        self._label.setWordWrap(True)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._label.setStyleSheet("border: none; background: transparent; font-size: 10px;")

        inner_layout = QVBoxLayout(self)
        inner_layout.setContentsMargins(6, 6, 6, 6)
        inner_layout.addWidget(self._label)

    def setDisplayText(self, text: str):
        self._label.setText(text)


class ButtonList(QWidget):
    item_selected = Signal(str)

    def __init__(self, title: str = ""):
        super().__init__()

        self._buttons = {}

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        self.container = QWidget()
        self.container.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(10, 10, 10, 10)
        scroll_area.setWidget(self.container)
        self.layout.addStretch()

        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(2)

        if title:
            title_label = QLabel(title)
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    font-size: 12px;
                    margin-bottom: 0px;
                }
            """)
            outer_layout.addWidget(title_label)

        # Create a rounded container for the scroll area
        self.rounded_container = QWidget()
        self.rounded_container.setStyleSheet("""
            QWidget {
                border: 1px solid #404040;
                border-radius: 8px;
                background-color: #2d2d2d;
            }
        """)
        rounded_layout = QVBoxLayout(self.rounded_container)
        rounded_layout.setContentsMargins(0, 0, 0, 0)
        rounded_layout.addWidget(scroll_area)

        outer_layout.addWidget(self.rounded_container)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(outer_layout)

    def add_button(self, name: str):
        if name in self._buttons:
            return

        # Remove file extension and replace underscores with spaces
        display_name = Path(name).stem.replace("_", " ")

        btn = WrappingButton()
        btn.setDisplayText(display_name)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
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
        upload_file = QToolButton()
        upload_file.setText("New\nSource")
        upload_file.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        upload_file.clicked.connect(self._upload_new_file)
        icon = QIcon(str(icon_dir / "file-up.svg"))
        upload_file.setIcon(icon)
        upload_file.setIconSize(QSize(48, 48))
        upload_file.setMinimumHeight(90)

        graph_creation = QToolButton()
        graph_creation.setText("New\nGraph")
        graph_creation.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        graph_creation.clicked.connect(self._open_graph_dialog)
        icon = QIcon(str(icon_dir / "image-plus.svg"))
        graph_creation.setIcon(icon)
        graph_creation.setIconSize(QSize(48, 48))
        graph_creation.setMinimumHeight(90)

        info_creation = QToolButton()
        info_creation.setText("Source\nInfo")
        info_creation.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        info_creation.clicked.connect(self._open_info_dialog)
        icon = QIcon(str(icon_dir / "file-plus-corner.svg"))
        info_creation.setIcon(icon)
        info_creation.setIconSize(QSize(48, 48))
        info_creation.setMinimumHeight(90)

        doc_opener = QToolButton()
        doc_opener.setText("Open\nNotes")
        doc_opener.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        doc_opener.clicked.connect(lambda: self.item_created.emit(["notes"]))
        icon = QIcon(str(icon_dir / "file-text.svg"))
        doc_opener.setIcon(icon)
        doc_opener.setIconSize(QSize(48, 48))
        doc_opener.setMinimumHeight(90)

        # Create content layout
        form_layout = QHBoxLayout()
        form_layout.addWidget(upload_file)
        form_layout.addWidget(graph_creation)
        form_layout.addWidget(info_creation)
        form_layout.addWidget(doc_opener)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(10)

        # Create rounded container
        content_widget = QWidget()
        content_widget.setLayout(form_layout)
        content_widget.setStyleSheet("""
            QWidget {
                border: 1px solid #404040;
                border-radius: 8px;
                background-color: #2d2d2d;
                font-size: 10px;
                padding: 1px;
            }
        """)

        # Create outer layout with title
        outer_layout = QVBoxLayout()
        outer_layout.addWidget(content_widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addStretch()

        self.setLayout(outer_layout)

    def update_dataframes(self, dfs):
        self.dataframes = dict(dfs)

    def _upload_new_file(self):
        file_dialog = QFileDialog()
        filters = "Data Files (*.csv *.json *.xml *.xlsx);;CSV Files (*.csv);;JSON Files (*.json);;XML Files (*.xml);;Excel Files (*.xlsx)"

        filepath, _ = file_dialog.getOpenFileName(self, "Open CSV File", "", filters)

        self.item_created.emit(["data", filepath])

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

        # then open pop up for generating data docs
        self.popup = DataInformation(self.dataframes, self)
        self.popup.setModal(True)
        self.popup.generated_info.connect(self._close_info_dialog)
        self.popup.open()

    def _close_info_dialog(self, doc_name, item):
        # create the item metadata
        metadata = {
            "name": doc_name,
            "doc":     item
        }

        # emit the metadata and item type
        self.item_created.emit(["doc", metadata])

        # set popup to none
        self.popup = None

class ItemViewer(QWidget):
    save_note = Signal(str)

    single_file_graphs = [
        "Histogram",
        "Scatter Plot",
        "Box Plot",
        "Heatmap",
        "KDE Plot",
        "Correlation Matrix",
        "Line Plot",
        "Bar Chart",
        "Violin Plot",
        "Pie Chart",
    ]
    curr_item = ""

    def __init__(self):
        super().__init__()

        self._dataframes = {}

        # -- define the different item view types -- #
        self.table = QTableWidget()     # for viewing dataframes
        self.graph = PlotlyWebEngine()       # for viewing graphs
        self.doc = NotesWidget()         # for viewing docs
        self.doc.save_note.connect(self.save_note.emit)

        self.view_stack = QStackedWidget()
        self.view_stack.addWidget(self.table)
        self.view_stack.addWidget(self.graph)
        self.view_stack.addWidget(self.doc)

        self.view_container = QWidget()
        self.view_container.setObjectName("itemViewContainer")
        self.view_container.setStyleSheet("""
            #itemViewContainer {
                border: 1px solid #404040;
                border-radius: 8px;
                background-color: #2d2d2d;
            }
        """)
        container_layout = QVBoxLayout(self.view_container)
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.addWidget(self.view_stack)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view_container)
        self.setLayout(layout)

    def add_dataframe(self, name: str, data: pd.DataFrame):
        self._dataframes[name] = data
        self.graph.add_dataframe(name, data)

    def show_item(self, item_type: str, item_data):
        if item_type == "data":
            self._show_data(item_data)
        elif item_type == "graph":
            self._show_graph(item_data)
        elif item_type == "data_doc":
            self._show_data_doc(item_data)
        elif item_type == "notes":
            self._show_notes(item_data)

    def _show_data(self, name: str):
        if name == self.curr_item:
            return

        self.curr_item = name

        data = self._dataframes[name]
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
                is_missing = pd.isna(value) if pd.api.types.is_scalar(value) else False
                display_value = "-" if is_missing else str(value)
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(display_value))

        # set the table as the active view
        self.view_stack.setCurrentWidget(self.table)

    def _show_graph(self, metadata):
        if metadata is None or not metadata:
            return

        name = metadata.get("name", "")
        if name and name == self.curr_item:
            self.view_stack.setCurrentWidget(self.graph)
            return

        self.curr_item = name
        self.graph.update_view(metadata)

        # set the graph as the active view
        self.view_stack.setCurrentWidget(self.graph)

    def _show_data_doc(self, metadata):
        if metadata is None or not metadata:
            return

        doc = metadata.get("doc")
        if not isinstance(doc, pd.DataFrame) or doc.empty:
            return

        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

        headers = [str(col) for col in doc.columns]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        rows = doc.values
        self.table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            for col_idx, value in enumerate(row):
                is_missing = pd.isna(value) if pd.api.types.is_scalar(value) else False
                display_value = "-" if is_missing else str(value)
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(display_value))

        self.view_stack.setCurrentWidget(self.table)

    def _show_notes(self, note: str):
        self.view_stack.setCurrentWidget(self.doc)

        if note != "":
            self.doc.open_note(note)
