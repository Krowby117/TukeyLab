
from PySide6.QtCore import Qt
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
    QTableWidgetItem
)

import seaborn as sns
import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure()
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)

class TableMaker(QDialog):
    default_text: str = " --- "
    table_options = {
    #   graph type          data type   inputs
        "Histogram":        ["numerical", 1],
        "Scatter Plot":     ["numerical", 2],
        "Box Plot":         ["numerical", 1],
        "Heatmap":          ["numerical", 2],
        #"Bar Chart":        ["categorical", 0],
        #"Pie Chart":        ["categorical", 0]
    }

    graphType: str   = default_text

    def __init__(self, dfs, parent=None):
        super().__init__(parent)
        self.resize(900, 700)

        self.dataframes = dfs

        self.setWindowTitle("Create New Table:")

        self.tableCombo = QComboBox()
        self.tableCombo.addItem(self.default_text)
        self.tableCombo.addItems(list(self.table_options.keys()))
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

        self.graphView = MplCanvas(self)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QFormLayout()
        layout.addRow(self.tableCombo)
        layout.addRow(self.fileCombo)
        layout.addRow(self.inputStack)
        layout.addRow(self.graphView)
        layout.addRow(buttonBox)

        self.setLayout(layout)

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
        }

        self.graphType = graph_type
        self.inputStack.setCurrentIndex(mapping[graph_type])
        self.update_feature_selections()

    def _combo_has_valid_selection(self, combo: QComboBox) -> bool:
        text = combo.currentText().strip()
        valid = bool(text) and text != self.default_text.strip()

        #if not valid: QMessageBox.information(self, "Cannot Generate Graph", "Please select required components.")

        return valid

    def generate_graph(self):
        if not self._combo_has_valid_selection(self.fileCombo):
            return

        df = self.dataframes[self.fileCombo.currentText()]

        if self.graphType == "Histogram":
            if not self._combo_has_valid_selection(self.hist_feature):
                return

            feature = self.hist_feature.currentText()

            self.graphView.ax.clear()

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

            self.graphView.ax.clear()

            self.graphView.ax.scatter(df[scat_x], df[scat_y])

            self.graphView.ax.set_title(f"{scat_x} vs. {scat_y}")
            self.graphView.ax.set_xlabel(scat_x)
            self.graphView.ax.set_ylabel(scat_y)

            self.graphView.draw()

        if self.graphType == "Box Plot":
            if not self._combo_has_valid_selection(self.box_feature):
                return

            feature = self.box_feature.currentText()

            self.graphView.ax.clear()

            self.graphView.ax.boxplot(df[feature].dropna(), vert=False)

            self.graphView.ax.set_title(f"{feature} Box Plot")

            self.graphView.draw()

        if self.graphType == "Heatmap":
            if ( not self._combo_has_valid_selection(self.heatmap_feature_x)
                or not self._combo_has_valid_selection(self.heatmap_feature_y)):
                return

            hm_x = self.heatmap_feature_x.currentText()
            hm_y = self.heatmap_feature_y.currentText()
            data = df[[hm_x, hm_y]]

            self.graphView.ax.clear()

            sns.heatmap(data, annot=True, cmap='coolwarm', ax=self.graphView.ax)

            self.graphView.ax.set_title(f"{hm_x} vs. {hm_y}")

            self.graphView.draw()

    def generate_report(self, data):
        numerical_cols = data.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = data.select_dtypes(include=['object', 'category', 'boolean']).columns.tolist()
        datetime_cols = data.select_dtypes(include=['datetime64[ns]', 'datetime']).columns.tolist()

        report = {
            "numerical": numerical_cols + datetime_cols,
            "categorical": categorical_cols,
            "distribution": numerical_cols
        }

        return report

    def update_feature_selections(self):
        file = self.fileCombo.currentText()

        if self.graphType == "Histogram":
            self.hist_feature.clear()
            self.hist_feature.addItem(self.default_text)

            if file != self.default_text:
                df = self.dataframes[file]
                self.hist_feature.addItems(self.generate_report(df)["numerical"])

        if self.graphType == "Scatter Plot":
            self.scat_feature_x.clear()
            self.scat_feature_x.addItem(self.default_text)
            self.scat_feature_y.clear()
            self.scat_feature_y.addItem(self.default_text)

            if file != self.default_text:
                df = self.dataframes[file]
                self.scat_feature_x.addItems(self.generate_report(df)["numerical"])
                self.scat_feature_y.addItems(self.generate_report(df)["numerical"])

        if self.graphType == "Box Plot":
            self.box_feature.clear()
            self.box_feature.addItem(self.default_text)

            if file != self.default_text:
                df = self.dataframes[file]
                self.box_feature.addItems(self.generate_report(df)["numerical"])

        if self.graphType == "Heatmap":
            self.heatmap_feature_x.clear()
            self.heatmap_feature_x.addItem(self.default_text)
            self.heatmap_feature_y.clear()
            self.heatmap_feature_y.addItem(self.default_text)

            if file != self.default_text:
                df = self.dataframes[file]
                self.heatmap_feature_x.addItems(self.generate_report(df)["numerical"])
                self.heatmap_feature_y.addItems(self.generate_report(df)["numerical"])

    def histo_inputs(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.hist_feature = QComboBox()
        self.hist_feature.addItem(self.default_text)
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
        self.scat_feature_x.addItem(self.default_text)
        self.scat_feature_x.currentTextChanged.connect(self.generate_graph)

        self.scat_feature_y = QComboBox()
        self.scat_feature_y.addItem(self.default_text)
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
        self.heatmap_feature_x.addItem(self.default_text)
        self.heatmap_feature_x.currentTextChanged.connect(self.generate_graph)

        self.heatmap_feature_y = QComboBox()
        self.heatmap_feature_y.addItem(self.default_text)
        self.heatmap_feature_y.currentTextChanged.connect(self.generate_graph)

        layout.addWidget(self.heatmap_feature_x)
        layout.addWidget(self.heatmap_feature_y)

        widget.setLayout(layout)
        return widget

class DataInformation(QDialog):
    default_text = "---"
    activeFile = ""
    def __init__(self, dfs, parent=None):
        super().__init__(parent)
        self.resize(900, 700)

        self.dataframes = dfs

        self.setWindowTitle("Data General Information:")

        self.fileCombo = QComboBox()
        self.fileCombo.addItem(self.default_text)
        self.fileCombo.addItems(list(self.dataframes.keys()))
        self.fileCombo.currentTextChanged.connect(self.update_table)

        #self.label = QLabel("General Information")
        self.table = QTableWidget()

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        #layout.addWidget(self.label)
        layout.addWidget(self.fileCombo)
        layout.addWidget(self.table)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def update_table(self, file: str):
        if file == self.activeFile: return

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
        info = summary.join(desc)

        self.table.setRowCount(info.shape[0])
        self.table.setColumnCount(info.shape[1])

        # Set column headers
        self.table.setHorizontalHeaderLabels(info.columns.astype(str))

        for row in range(info.shape[0]):
            for col in range(info.shape[1]):
                value = info.iat[row, col]

                # Handle NaN / None cleanly
                if pd.isna(value):
                    display = "-"
                else:
                    display = str(value)

                self.table.setItem(row, col, QTableWidgetItem(display))