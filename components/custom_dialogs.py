
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
    QLineEdit
)

import seaborn as sns
import pandas as pd
import hashlib
import time

from components.custom_widgets import MplCanvas

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
        #"Bar Chart",
        #"Pie Chart",
    ]

    created_graph = Signal(dict)
    def __init__(self, dfs, parent=None):
        super().__init__(parent)
        self.resize(900, 700)

        self.dataframes = dfs

        self.setWindowTitle("Create New Table:")

        self.tableCombo = QComboBox()
        self.tableCombo.addItem(self.default_text)
        self.tableCombo.addItems(list(self.table_options))
        self.tableCombo.currentTextChanged.connect(self.update_inputs)

        self.fileCombo = QComboBox()
        self.fileCombo.addItem(self.default_text)
        self.fileCombo.addItems(list(self.dataframes.keys()))
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

        self.graphView = MplCanvas(self)

        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttonBox.addButton(QDialogButtonBox.StandardButton.Cancel)
        buttonBox.accepted.connect(self.create_graph)
        buttonBox.rejected.connect(self.reject)

        layout = QFormLayout()
        layout.addRow(self.tableCombo)
        layout.addRow(self.fileCombo)
        layout.addRow(self.inputStack)
        layout.addRow(self.graphView)
        layout.addRow(buttonBox)

        self.setLayout(layout)

    def create_graph(self):
        if not self._combo_has_valid_selection(self.fileCombo):
            return

        # grab the dataset
        dataset = self.fileCombo.currentText()
        df = self.dataframes[dataset]

        # define the graph name and parameters based on the selected graph type
        if self.graphType == "Histogram" and self._combo_has_valid_selection(self.hist_feature):
            feat = self.hist_feature.currentText()
            bins = self.bins.value()
            param = {"feature": feat, "bins": bins}
            name = f"{feat} Histogram"

        elif self.graphType == "Scatter Plot" and self._combo_has_valid_selection(self.scat_feature_x) and self._combo_has_valid_selection(self.scat_feature_y):
            x = self.scat_feature_x.currentText()
            y = self.scat_feature_y.currentText()
            param = {"x": x, "y": y}
            name = f"{x} v {y} Scatter Plot"

        elif self.graphType == "Box Plot" and self._combo_has_valid_selection(self.box_feature):
            param = self.box_feature.currentText()
            name = f"{param} Box Plot"

        elif self.graphType == "Heatmap" and self._combo_has_valid_selection(self.heatmap_feature_x) and self._combo_has_valid_selection(self.heatmap_feature_y):
            x = self.heatmap_feature_x.currentText()
            y = self.heatmap_feature_y.currentText()
            param = {"x": x, "y": y}
            name = f"{x} v {y} Heatmap"

        elif self.graphType == "KDE Plot" and self._combo_has_valid_selection(self.kde_feature):
            param = self.kde_feature.currentText()
            name = f"{param} KDE Plot"

        elif self.graphType == "Correlation Matrix":
            param = {}
            name = f"{dataset} Correlation Matrix"

        else: return

        # define the graph metadata to emit
        metadata = {
            "name": name,
            "type": self.graphType,
            "data": df,
            "params": param,
        }

        # emit the metadata
        self.created_graph.emit(metadata)
        self.accept()

    def update_inputs(self, graph_type: str):
        if graph_type == self.default_text:
            self.graphType = self.default_text
            self.inputStack.setCurrentIndex(0)
            return

        mapping = {
            self.default_text: 0,
            "Histogram": 1,
            "Scatter Plot": 2,
            "Box Plot": 3,
            "Heatmap": 4,
            "KDE Plot": 5,
            "Correlation Matrix": 6
        }

        self.graphType = graph_type
        self.inputStack.setCurrentIndex(mapping[graph_type])
        self.update_feature_selections()

    def _combo_has_valid_selection(self, combo: QComboBox) -> bool:
        text = combo.currentText().strip()
        return bool(text) and text != self.default_text.strip()

    def _reset_plot_area(self):
        # Recreate the main axis so heatmap colorbar/layout changes never persist.
        fig = self.graphView.figure
        fig.clear()
        self.graphView.ax = fig.add_subplot(111)
        self.graphView.draw()

    def generate_graph(self):
        self._reset_plot_area()

        if not self._combo_has_valid_selection(self.fileCombo):
            return

        df = self.dataframes[self.fileCombo.currentText()]

        if self.graphType == "Histogram":
            if not self._combo_has_valid_selection(self.hist_feature):
                return

            feature = self.hist_feature.currentText()

            self.graphView.ax.hist(df[feature].dropna(), bins=self.bins.value())
            self.graphView.ax.set_title(f"{feature} Distribution")
            self.graphView.ax.set_xlabel(feature)
            self.graphView.ax.set_ylabel("Frequency")
            self.graphView.draw()

        if self.graphType == "Scatter Plot":
            if ( not self._combo_has_valid_selection(self.scat_feature_x)
                or not self._combo_has_valid_selection(self.scat_feature_y)):
                return

            scat_x = self.scat_feature_x.currentText()
            scat_y = self.scat_feature_y.currentText()

            self.graphView.ax.scatter(df[scat_x], df[scat_y])
            self.graphView.ax.set_title(f"{scat_x} vs. {scat_y}")
            self.graphView.ax.set_xlabel(scat_x)
            self.graphView.ax.set_ylabel(scat_y)
            self.graphView.draw()

        if self.graphType == "Box Plot":
            if not self._combo_has_valid_selection(self.box_feature):
                return

            feature = self.box_feature.currentText()

            self.graphView.ax.boxplot(df[feature].dropna(), vert=False)
            self.graphView.ax.set_title(f"{feature} Box Plot")
            self.graphView.draw()

        if self.graphType == "Heatmap":
            if ( not self._combo_has_valid_selection(self.heatmap_feature_x)
                or not self._combo_has_valid_selection(self.heatmap_feature_y)):
                return

            hm_x = self.heatmap_feature_x.currentText()
            hm_y = self.heatmap_feature_y.currentText()
            data = df[[hm_x, hm_y]].apply(pd.to_numeric, errors='coerce').dropna()
            if data.empty:
                QMessageBox.warning(self, "Heatmap", "No numeric rows available for the selected columns.")
                return

            sns.heatmap(data, annot=True, cmap='coolwarm', ax=self.graphView.ax)
            self.graphView.ax.set_title(f"{hm_x} vs. {hm_y}")
            self.graphView.draw()

        if self.graphType == "KDE Plot":
            if not self._combo_has_valid_selection(self.kde_feature):
                return

            x = self.kde_feature.currentText()

            self.graphView.ax.clear()
            df[x].dropna().plot(kind='kde', ax=self.graphView.ax)
            self.graphView.ax.set_title(f"{x} Distribution (KDE)")
            self.graphView.draw()

        if self.graphType == "Correlation Matrix":
            data = df.select_dtypes(include=["number"])
            if data.shape[1] < 2:
                self.corr_label.setText("At least two numerical columns must be present in selected datafile.")
                return

            self.corr_label.setText("")
            corr = data.corr(numeric_only=True)

            sns.heatmap(corr, annot=True, cmap="coolwarm", ax=self.graphView.ax, vmin=-1, vmax=1)
            self.graphView.ax.set_title("Correlation Matrix")
            self.graphView.draw()

    def update_feature_selections(self):
        file = self.fileCombo.currentText()

        if file == self.default_text:
            self.generate_graph()
            return

        df = self.dataframes[file]
        numeric_data = df.select_dtypes(include=['number']).columns.tolist()

        # previous selections for all graph types, lets it save selections while looking at options
        prev_hist = self.hist_feature.currentText()
        prev_x = self.scat_feature_x.currentText()
        prev_y = self.scat_feature_y.currentText()
        prev_b = self.box_feature.currentText()
        prev_hx = self.heatmap_feature_x.currentText()
        prev_hy = self.heatmap_feature_y.currentText()
        prev_kde = self.kde_feature.currentText()

        if self.graphType == "Histogram":
            self.restore_selection(self.hist_feature, numeric_data, prev_hist)
        if self.graphType == "Scatter Plot":
            self.restore_selection(self.scat_feature_x, numeric_data, prev_x)
            self.restore_selection(self.scat_feature_y, numeric_data, prev_y)
        if self.graphType == "Box Plot":
            self.restore_selection(self.box_feature, numeric_data, prev_b)
        if self.graphType == "Heatmap":
            self.restore_selection(self.heatmap_feature_x, numeric_data, prev_hx)
            self.restore_selection(self.heatmap_feature_y, numeric_data, prev_hy)
        if self.graphType == "KDE Plot":
            self.restore_selection(self.kde_feature, numeric_data, prev_kde)

        self.generate_graph()

    def restore_selection(self, combo: QComboBox, data: list[str], prev: str):
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(data)

        if prev in data: combo.setCurrentText(prev)
        elif data: combo.setCurrentText(data[0])

        combo.blockSignals(False)

    def histo_inputs(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.hist_feature = QComboBox()
        self.hist_feature.currentTextChanged.connect(self.generate_graph)

        self.bins = QSlider()
        self.bins.setOrientation(Qt.Orientation.Horizontal)
        self.bins.setRange(1, 50)
        self.bins.valueChanged.connect(self.generate_graph)

        layout.addWidget(self.hist_feature)
        layout.addWidget(self.bins)

        widget.setLayout(layout)
        return widget

    def scatter_inputs(self):
        widget = QWidget()
        layout = QHBoxLayout()

        self.scat_feature_x = QComboBox()
        self.scat_feature_x.currentTextChanged.connect(self.generate_graph)

        self.scat_feature_y = QComboBox()
        self.scat_feature_y.currentTextChanged.connect(self.generate_graph)

        layout.addWidget(self.scat_feature_x)
        layout.addWidget(self.scat_feature_y)

        widget.setLayout(layout)
        return widget

    def box_inputs(self):
        widget = QWidget()
        layout = QHBoxLayout()

        self.box_feature = QComboBox()
        self.box_feature.addItem(self.default_text)
        self.box_feature.currentTextChanged.connect(self.generate_graph)

        layout.addWidget(self.box_feature)

        widget.setLayout(layout)
        return widget

    def heatmap_inputs(self):
        widget = QWidget()
        layout = QHBoxLayout()

        self.heatmap_feature_x = QComboBox()
        self.heatmap_feature_x.currentTextChanged.connect(self.generate_graph)

        self.heatmap_feature_y = QComboBox()
        self.heatmap_feature_y.currentTextChanged.connect(self.generate_graph)

        layout.addWidget(self.heatmap_feature_x)
        layout.addWidget(self.heatmap_feature_y)

        widget.setLayout(layout)
        return widget

    def kde_inputs(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.kde_feature = QComboBox()
        self.kde_feature.currentTextChanged.connect(self.generate_graph)

        layout.addWidget(self.kde_feature)

        widget.setLayout(layout)
        return widget

    def correlation_inputs(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.corr_label = QLabel("")

        layout.addWidget(self.corr_label)

        widget.setLayout(layout)
        return widget

class DataInformation(QDialog):
    default_text = "---"
    activeFile = ""
    info = None

    created_doc = Signal(str, str, object)
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
            return

        doc_name = self.activeFile + " General Info"
        self.created_doc.emit(doc_name, "table", self.info)
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

class MissingValueAnalysis(QDialog):
    def __init__(self, dfs, parent=None):
        super().__init__(parent)
        self.resize(900, 700)
        self.dataframes = dfs
        self.setWindowTitle("Missing Value Analysis")

        self.fileCombo = QComboBox()
        self.fileCombo.addItems(list(dfs.keys()))
        self.fileCombo.currentTextChanged.connect(self.update_plot)

        self.canvas = MplCanvas(self)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout()
        layout.addWidget(self.fileCombo)
        layout.addWidget(self.canvas)
        layout.addWidget(buttons)
        self.setLayout(layout)

        self.update_plot(self.fileCombo.currentText())

    def update_plot(self, file):
        df = self.dataframes[file]
        missing = df.isna().sum()
        missing = missing[missing > 0]  # only show columns that have nulls

        self.canvas.ax.clear()
        if missing.empty:
            self.canvas.ax.text(0.5, 0.5, "No missing values!",
                                ha='center', va='center', transform=self.canvas.ax.transAxes)
        else:
            missing.plot(kind='bar', ax=self.canvas.ax, color='salmon')
            self.canvas.ax.set_title("Missing Values Per Column")
            self.canvas.ax.set_ylabel("Count")

        self.canvas.draw()

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
