
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
    QStackedWidget
)

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class Dataset:
    def __init__(self, name, data):
        self.name = name
        self.data = data

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
        "Box Plot":         ["numerical", 1],
        "Scatter Plot":     ["numerical", 2],
        "Heatmap":          ["numerical", 2],
        "Bar Chart":        ["categorical", 0],
        "Pie Chart":        ["categorical", 0]
    }

    graphType: str   = default_text

    def __init__(self, df):
        super().__init__()

        self.dataframes = df

        self.setWindowTitle("Create New Table:")

        self.tableCombo = QComboBox()
        self.tableCombo.addItem(self.default_text)
        self.tableCombo.addItems(list(self.table_options.keys()))
        self.tableCombo.currentTextChanged.connect(self.update_inputs)
        # choosing a new graph type should change what feature options are shown and how many

        self.defaultLabel = QLabel("Select a graph type to continue")
        self.histoWidget = self.histo_inputs()
        self.scatWidget = self.scatter_inputs()

        self.inputStack = QStackedWidget()
        self.inputStack.addWidget(self.defaultLabel)
        self.inputStack.addWidget(self.histoWidget)
        self.inputStack.addWidget(self.scatWidget)

        self.graphView = MplCanvas(self)

        self.generateButton = QPushButton("Generate Graph")
        self.generateButton.clicked.connect(self.generate_graph)

        layout = QVBoxLayout()
        layout.addWidget(self.tableCombo)
        layout.addWidget(self.inputStack)
        layout.addWidget(self.graphView)
        layout.addWidget(self.generateButton)

        self.setLayout(layout)

    def update_inputs(self, graph_type: str):
        if graph_type == self.default_text:
            return

        mapping = {
            self.default_text: 0,
            "Histogram": 1,
            "Scatter Plot": 2,
        }

        self.graphType = graph_type
        self.inputStack.setCurrentIndex(mapping[graph_type])
        self.update_feature_selections()

    def generate_graph(self):
        # if the user has not selected the correct amount of files / features
        if self.graphType == "Histogram":
            if self.hist_file.currentText() == self.default_text or self.hist_feature.currentText() == self.default_text:
                return

            df = self.dataframes[self.hist_file.currentText()]
            feature = self.hist_feature.currentText()

            self.graphView.ax.clear()

            self.graphView.ax.hist(df[feature].dropna(), bins=self.bins.value())

            self.graphView.ax.set_title(f"{feature} Distribution")
            self.graphView.ax.set_xlabel(feature)
            self.graphView.ax.set_ylabel("Frequency")

            self.graphView.draw()

    def generate_report(self, data):
        numerical_cols = data.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = data.select_dtypes(include=['object', 'category', 'boolean']).columns.tolist()
        datetime_cols = data.select_dtypes(include=['datetime']).columns.tolist()

        report = {
            "numerical": numerical_cols + datetime_cols,
            "categorical": categorical_cols,
            "distribution": numerical_cols
        }

        return report

    def update_feature_selections(self):
        if self.graphType == "Histogram":
            file = self.hist_file.currentText()
            self.hist_feature.clear()

            if file == self.default_text:
                return

            df = self.dataframes[file]
            self.hist_feature.addItems(self.generate_report(df)["numerical"])

        if self.graphType == "Scatter Plot":
            file_x = self.scat_file_x.currentText()
            self.scat_feature_x.clear()

            if file_x != self.default_text:
                df = self.dataframes[file_x]
                self.scat_feature_x.addItems(self.generate_report(df)["numerical"])

            file_y = self.scat_file_y.currentText()
            self.scat_feature_y.clear()

            if file_y != self.default_text:
                df = self.dataframes[file_y]
                self.scat_feature_y.addItems(self.generate_report(df)["numerical"])

    def histo_inputs(self):
        widget = QWidget()
        layout = QFormLayout()

        self.hist_file = QComboBox()
        self.hist_file.addItem(self.default_text)
        self.hist_file.addItems(list(self.dataframes.keys()))
        self.hist_file.currentTextChanged.connect(self.update_feature_selections)

        self.hist_feature = QComboBox()
        self.hist_feature.addItem(self.default_text)

        self.bins = QSlider()
        self.bins.setOrientation(Qt.Orientation.Horizontal)
        self.bins.setRange(1, 50)

        layout.addRow("File:", self.hist_file)
        layout.addRow("Feature:", self.hist_feature)
        layout.addRow("Bins:", self.bins)

        widget.setLayout(layout)
        return widget

    def box_inputs(self):
        pass

    def scatter_inputs(self):
        widget = QWidget()
        layout = QFormLayout()

        self.scat_file_x = QComboBox()
        self.scat_file_x.addItem(self.default_text)
        self.scat_file_x.addItems(list(self.dataframes.keys()))
        self.scat_file_x.currentTextChanged.connect(self.update_feature_selections)

        self.scat_feature_x = QComboBox()
        self.scat_feature_x.addItems(self.default_text)

        self.scat_file_y = QComboBox()
        self.scat_file_y.addItem(self.default_text)
        self.scat_file_y.addItems(list(self.dataframes.keys()))
        self.scat_file_y.currentTextChanged.connect(self.update_feature_selections)

        self.scat_feature_y = QComboBox()
        self.scat_feature_y.addItems(self.default_text)

        x_row_layout = QHBoxLayout()
        x_row_layout.addWidget(self.scat_file_x)
        x_row_layout.addWidget(self.scat_feature_x)
        layout.addRow("X Axis:", x_row_layout)

        y_row_layout = QHBoxLayout()
        y_row_layout.addWidget(self.scat_file_y)
        y_row_layout.addWidget(self.scat_feature_y)
        layout.addRow("Y Axis:", y_row_layout)

        widget.setLayout(layout)
        return widget

    def heatmap_inputs(self):
        pass

    def bar_inputs(self):
        pass

    def pie_inputs(self):
        pass