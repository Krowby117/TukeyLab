
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QComboBox,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QWidget,
    QFormLayout,
    QSlider,
    QStackedWidget,
    QMessageBox,
    QDialogButtonBox,
    QTextBrowser,
    QTableWidget,
    QTableWidgetItem,
    QCheckBox,
    QLineEdit,
)

from PySide6.QtWebEngineWidgets import QWebEngineView

import seaborn as sns
import pandas as pd
import hashlib
import time
from pathlib import Path
import plotly.express as px

from components.helper_widgets import PlotlyWebEngine

class SingleFileGraph(QDialog):
    default_text: str = " --- "
    graphType: str = default_text
    table_options = [
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

    created_graph = Signal(dict)
    def __init__(self, dfs, parent=None):
        super().__init__(parent)
        self.resize(900, 700)

        self._dataframes = dfs
        self._metadata = {}

        self.setWindowTitle("Create New Table:")

        self.tableCombo = QComboBox()
        self.tableCombo.addItem(self.default_text)
        self.tableCombo.addItems(list(self.table_options))
        self.tableCombo.currentTextChanged.connect(self.update_inputs)

        self.fileCombo = QComboBox()
        self.fileCombo.addItem(self.default_text)
        self.fileCombo.addItems(list(self._dataframes.keys()))
        self.fileCombo.currentTextChanged.connect(self.update_feature_selections)

        self.defaultLabel = QLabel("Select a graph type to continue")

        self.inputStack = QStackedWidget()
        self.inputStack.addWidget(self.defaultLabel)
        self.inputStack.addWidget(self.histo_inputs())
        self.inputStack.addWidget(self.scatter_inputs())
        self.inputStack.addWidget(self.box_inputs())
        self.inputStack.addWidget(self.heatmap_inputs())
        self.inputStack.addWidget(self.kde_inputs())
        self.inputStack.addWidget(self.correlation_inputs())
        self.inputStack.addWidget(self.line_inputs())
        self.inputStack.addWidget(self.bar_inputs())
        self.inputStack.addWidget(self.violin_inputs())
        self.inputStack.addWidget(self.pie_inputs())

        #self.graphView = MplCanvas(self)
        self.graphView = PlotlyWebEngine()
        self.graphView.set_dataframes(self._dataframes)
        self.graphView.setMinimumHeight(400)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self._create_graph)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.tableCombo)
        layout.addWidget(self.fileCombo)
        layout.addWidget(self.inputStack)
        layout.addWidget(self.graphView)
        layout.addWidget(button_box)
        layout.setStretch(2, 0)
        layout.setStretch(3, 1)

        self.setLayout(layout)

    def _generate_graph(self):
        if not self._combo_has_valid_selection(self.fileCombo):
            return

        # grab the dataset
        dataset = self.fileCombo.currentText()

        # define the graph name and parameters based on the selected graph type
        if self.graphType == "Histogram" and self._combo_has_valid_selection(self.hist_feature):
            feat = self.hist_feature.currentText()
            bins = self.bins.value()
            param = {"feature": feat, "bins": bins}
            name = f"{feat}_Histogram"

        elif self.graphType == "Scatter Plot" and self._combo_has_valid_selection(self.scat_feature_x) and self._combo_has_valid_selection(self.scat_feature_y):
            x = self.scat_feature_x.currentText()
            y = self.scat_feature_y.currentText()
            param = {"x": x, "y": y}
            name = f"{x}_v_{y}_ScatterPlot"

        elif self.graphType == "Box Plot" and self._combo_has_valid_selection(self.box_feature):
            param = self.box_feature.currentText()
            name = f"{param}_BoxPlot"

        elif self.graphType == "Heatmap" and self._combo_has_valid_selection(self.heatmap_feature_x) and self._combo_has_valid_selection(self.heatmap_feature_y):
            x = self.heatmap_feature_x.currentText()
            y = self.heatmap_feature_y.currentText()
            param = {"x": x, "y": y}
            name = f"{x}_v_{y}_Heatmap"

        elif self.graphType == "KDE Plot" and self._combo_has_valid_selection(self.kde_feature):
            param = self.kde_feature.currentText()
            name = f"{param}_KDEPlot"

        elif self.graphType == "Correlation Matrix":
            param = {}
            name = f"{dataset}_Correlation_Matrix"

        elif self.graphType == "Line Plot" and self._combo_has_valid_selection(self.line_feature_x) and self._combo_has_valid_selection(self.line_feature_y):
            x = self.line_feature_x.currentText()
            y = self.line_feature_y.currentText()
            param = {"x": x, "y": y}
            name = f"{x}_v_{y}_LinePlot"

        elif self.graphType == "Bar Chart" and self._combo_has_valid_selection(self.bar_feature_x) and self._combo_has_valid_selection(self.bar_feature_y):
            x = self.bar_feature_x.currentText()
            y = self.bar_feature_y.currentText()
            param = {"x": x, "y": y}
            name = f"{x}_v_{y}_BarChart"

        elif self.graphType == "Violin Plot" and self._combo_has_valid_selection(self.violin_feature):
            feature = self.violin_feature.currentText()
            param = feature
            name = f"{feature}_ViolinPlot"

        elif self.graphType == "Pie Chart" and self._combo_has_valid_selection(self.pie_names_feature) and self._combo_has_valid_selection(self.pie_values_feature):
            names = self.pie_names_feature.currentText()
            values = self.pie_values_feature.currentText()
            param = {"names": names, "values": values}
            name = f"{names}_v_{values}_PieChart"

        else: return

        # define the graph metadata to emit
        self._metadata = {
            "name": name,
            "type": self.graphType,
            "data": [dataset],
            "params": param,
        }

        self.graphView.update_view(self._metadata)

    def _create_graph(self):
        if not self._metadata:
            QMessageBox.information(self, "No Graph", "Pick a graph type and valid inputs first.")
            return

        # emit the metadata
        self.created_graph.emit(self._metadata)
        self.accept()

    def update_inputs(self, graph_type: str):
        if graph_type == self.default_text:
            self.graphType = self.default_text
            self.inputStack.setVisible(True)
            self.inputStack.setCurrentIndex(0)
            return

        mapping = {
            self.default_text: 0,
            "Histogram": 1,
            "Scatter Plot": 2,
            "Box Plot": 3,
            "Heatmap": 4,
            "KDE Plot": 5,
            "Correlation Matrix": 6,
            "Line Plot": 7,
            "Bar Chart": 8,
            "Violin Plot": 9,
            "Pie Chart": 10,
        }

        self.graphType = graph_type
        # Correlation Matrix has no configurable inputs, so let the graph use the space.
        self.inputStack.setVisible(graph_type != "Correlation Matrix")
        self.inputStack.setCurrentIndex(mapping[graph_type])
        self.update_feature_selections()

    def _combo_has_valid_selection(self, combo: QComboBox) -> bool:
        text = combo.currentText().strip()
        return bool(text) and text != self.default_text.strip()

    def update_feature_selections(self):
        file = self.fileCombo.currentText()

        if file == self.default_text:
            self._generate_graph()
            return

        df = self._dataframes[file]
        numeric_data = df.select_dtypes(include=['number']).columns.tolist()
        all_data = df.columns.tolist()

        # previous selections for all graph types, lets it save selections while looking at options
        prev_hist = self.hist_feature.currentText()
        prev_x = self.scat_feature_x.currentText()
        prev_y = self.scat_feature_y.currentText()
        prev_b = self.box_feature.currentText()
        prev_hx = self.heatmap_feature_x.currentText()
        prev_hy = self.heatmap_feature_y.currentText()
        prev_kde = self.kde_feature.currentText()
        prev_lx = self.line_feature_x.currentText()
        prev_ly = self.line_feature_y.currentText()
        prev_bx = self.bar_feature_x.currentText()
        prev_by = self.bar_feature_y.currentText()
        prev_violin = self.violin_feature.currentText()
        prev_pie_names = self.pie_names_feature.currentText()
        prev_pie_values = self.pie_values_feature.currentText()

        if self.graphType == "Histogram":
            self._restore_selection(self.hist_feature, numeric_data, prev_hist)
        if self.graphType == "Scatter Plot":
            self._restore_selection(self.scat_feature_x, numeric_data, prev_x)
            self._restore_selection(self.scat_feature_y, numeric_data, prev_y)
        if self.graphType == "Box Plot":
            self._restore_selection(self.box_feature, numeric_data, prev_b)
        if self.graphType == "Heatmap":
            self._restore_selection(self.heatmap_feature_x, numeric_data, prev_hx)
            self._restore_selection(self.heatmap_feature_y, numeric_data, prev_hy)
        if self.graphType == "KDE Plot":
            self._restore_selection(self.kde_feature, numeric_data, prev_kde)
        if self.graphType == "Line Plot":
            self._restore_selection(self.line_feature_x, all_data, prev_lx)
            self._restore_selection(self.line_feature_y, numeric_data, prev_ly)
        if self.graphType == "Bar Chart":
            self._restore_selection(self.bar_feature_x, all_data, prev_bx)
            self._restore_selection(self.bar_feature_y, numeric_data, prev_by)
        if self.graphType == "Violin Plot":
            self._restore_selection(self.violin_feature, numeric_data, prev_violin)
        if self.graphType == "Pie Chart":
            self._restore_selection(self.pie_names_feature, all_data, prev_pie_names)
            self._restore_selection(self.pie_values_feature, numeric_data, prev_pie_values)

        self._generate_graph()

    def _restore_selection(self, combo: QComboBox, data: list[str], prev: str):
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(data)

        if prev in data: combo.setCurrentText(prev)
        elif data: combo.setCurrentText(data[0])

        combo.blockSignals(False)

    def histo_inputs(self):
        widget = QWidget()
        layout = QFormLayout()

        self.hist_feature = QComboBox()
        self.hist_feature.currentTextChanged.connect(self._generate_graph)

        self.bins = QSlider()
        self.bins.setOrientation(Qt.Orientation.Horizontal)
        self.bins.setRange(1, 50)
        self.bins.setValue(10)
        self.bins.sliderReleased.connect(lambda: self._generate_graph())

        layout.addRow("Feature Column:", self.hist_feature)
        layout.addRow("Number of Bins:", self.bins)

        widget.setLayout(layout)
        return widget

    def scatter_inputs(self):
        widget = QWidget()
        layout = QFormLayout()

        self.scat_feature_x = QComboBox()
        self.scat_feature_x.currentTextChanged.connect(self._generate_graph)

        self.scat_feature_y = QComboBox()
        self.scat_feature_y.currentTextChanged.connect(self._generate_graph)

        layout.addRow("X Axis Column:", self.scat_feature_x)
        layout.addRow("Y Axis Column:", self.scat_feature_y)

        widget.setLayout(layout)
        return widget

    def box_inputs(self):
        widget = QWidget()
        layout = QFormLayout()

        self.box_feature = QComboBox()
        self.box_feature.addItem(self.default_text)
        self.box_feature.currentTextChanged.connect(self._generate_graph)

        layout.addRow("Feature Column:", self.box_feature)

        widget.setLayout(layout)
        return widget

    def heatmap_inputs(self):
        widget = QWidget()
        layout = QFormLayout()

        self.heatmap_feature_x = QComboBox()
        self.heatmap_feature_x.currentTextChanged.connect(self._generate_graph)

        self.heatmap_feature_y = QComboBox()
        self.heatmap_feature_y.currentTextChanged.connect(self._generate_graph)

        layout.addRow("X Axis Column:", self.heatmap_feature_x)
        layout.addRow("Y Axis Column:", self.heatmap_feature_y)

        widget.setLayout(layout)
        return widget

    def kde_inputs(self):
        widget = QWidget()
        layout = QFormLayout()

        self.kde_feature = QComboBox()
        self.kde_feature.currentTextChanged.connect(self._generate_graph)

        layout.addRow("Feature Column:", self.kde_feature)

        widget.setLayout(layout)
        return widget

    def correlation_inputs(self):
        widget = QWidget()
        layout = QFormLayout()

        self.corr_label = QLabel("No additional inputs are needed.")

        layout.addRow("Info:", self.corr_label)

        widget.setLayout(layout)
        return widget

    def line_inputs(self):
        widget = QWidget()
        layout = QFormLayout()

        self.line_feature_x = QComboBox()
        self.line_feature_x.currentTextChanged.connect(self._generate_graph)

        self.line_feature_y = QComboBox()
        self.line_feature_y.currentTextChanged.connect(self._generate_graph)

        layout.addRow("X Axis Column:", self.line_feature_x)
        layout.addRow("Y Axis Column:", self.line_feature_y)

        widget.setLayout(layout)
        return widget

    def bar_inputs(self):
        widget = QWidget()
        layout = QFormLayout()

        self.bar_feature_x = QComboBox()
        self.bar_feature_x.currentTextChanged.connect(self._generate_graph)

        self.bar_feature_y = QComboBox()
        self.bar_feature_y.currentTextChanged.connect(self._generate_graph)

        layout.addRow("Category Column:", self.bar_feature_x)
        layout.addRow("Value Column:", self.bar_feature_y)

        widget.setLayout(layout)
        return widget

    def violin_inputs(self):
        widget = QWidget()
        layout = QFormLayout()

        self.violin_feature = QComboBox()
        self.violin_feature.currentTextChanged.connect(self._generate_graph)

        layout.addRow("Distribution Column:", self.violin_feature)

        widget.setLayout(layout)
        return widget

    def pie_inputs(self):
        widget = QWidget()
        layout = QFormLayout()

        self.pie_names_feature = QComboBox()
        self.pie_names_feature.currentTextChanged.connect(self._generate_graph)

        self.pie_values_feature = QComboBox()
        self.pie_values_feature.currentTextChanged.connect(self._generate_graph)

        layout.addRow("Slice Labels Column:", self.pie_names_feature)
        layout.addRow("Slice Values Column:", self.pie_values_feature)

        widget.setLayout(layout)
        return widget

class DataInformation(QDialog):
    default_text = "---"
    activeFile = ""
    info = None

    generated_info = Signal(str, object)
    def __init__(self, dfs, parent=None):
        super().__init__(parent)
        self.resize(900, 700)

        self.dataframes = dfs

        self.setWindowTitle("Data General Information:")

        self.fileCombo = QComboBox()
        self.fileCombo.addItem(self.default_text)
        self.fileCombo.addItems(list(self.dataframes.keys()))
        self.fileCombo.currentTextChanged.connect(self.update_table)

        self.table = QTableWidget()

        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttonBox.addButton(QDialogButtonBox.StandardButton.Cancel)
        buttonBox.accepted.connect(self.create_document)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.fileCombo)
        layout.addWidget(self.table)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def create_document(self):
        if self.info is None or self.info.empty:
            self.reject()

        doc_name = Path(self.activeFile).stem + "_General_Info"
        self.generated_info.emit(doc_name, self.info)
        self.accept()

    def update_table(self, file: str):
        if file == self.activeFile: return

        self.activeFile = file
        self.table.clear()

        if file == self.default_text: return

        df = self.dataframes[file]

        summary = pd.DataFrame({
            "dtype": df.dtypes,
            "missing_values": df.isna().sum(),
            "missing_%": (df.isna().sum() / len(df)) * 100
        })

        # Add describe() stats
        desc = df.describe(include='all').transpose()

        # Combine everything
        self.info = summary.join(desc)

        # Reset index to make feature names a column
        self.info = self.info.reset_index()
        self.info = self.info.rename(columns={"index": "Feature"})

        self.table.setRowCount(self.info.shape[0])
        self.table.setColumnCount(self.info.shape[1])

        # Set column headers
        self.table.setHorizontalHeaderLabels(self.info.columns.astype(str))

        for row in range(self.info.shape[0]):
            for col in range(self.info.shape[1]):
                value = self.info.iat[row, col]

                # Handle NaN / None cleanly
                if pd.isna(value):
                    display = "-"
                else:
                    display = str(value)

                self.table.setItem(row, col, QTableWidgetItem(display))

class NewProjectDialog(QDialog):
    created = Signal(str)

    def __init__(self):
        super().__init__()
        self.resize(500, 300)
        self.setWindowTitle("Create New Project")

        self.proj_name = QLineEdit()
        self.proj_name.setPlaceholderText("Project name")
        self.proj_name.returnPressed.connect(self.emit_name)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.emit_name)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.proj_name)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _is_valid_name(self, name: str) -> bool:
        # allow only letters, digits, and underscores
        import re
        return bool(name) and bool(re.fullmatch(r'[A-Za-z0-9]+', name))

    def emit_name(self):
        name = self.proj_name.text().strip()
        if not self._is_valid_name(name):
            QMessageBox.warning(
                self,
                "Invalid Project Name",
                "Project name must be non-empty and may only contain letters, and digits. "
                "No spaces or special characters are allowed."
            )
            self.proj_name.clear()
            return

        _id = self.generate_id(name)
        proj_id = [name, _id]

        self.created.emit(name)
        self.accept()

    def generate_id(self, name: str):
        timestamp = str(time.time_ns())
        check = (timestamp + name).encode()
        return hashlib.sha256(check).hexdigest()[:6]