
from PySide6.QtWidgets import (
    QDialog,
    QComboBox,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QWidget,
    QFormLayout,
    QSlider
)

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from enum import Enum

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
    dataType: str   = ""
    numInputs: int  = -1

    activeFile: str = default_text

    # Have all file / feature selections instanced but just not visible
    # Single mode enables just the first one
    # Double mode enables both the first two
    # Multi mode enables the mutli select box

    # Selected files/features are in lists
    # Selected files        [x, y, z]
    selectedFiles = ["", ""]
    # Selected features     [a, b, c]
    selectedFeatures = ["", ""]

    def __init__(self, df):
        super().__init__()

        self.dataframes = df

        self.setWindowTitle("Create New Table:")

        self.tableCombo = QComboBox()
        self.tableCombo.addItem(self.default_text)
        self.tableCombo.addItems(list(self.table_options.keys()))
        self.tableCombo.currentTextChanged.connect(self.updateDialogOptions)
        # choosing a new graph type should change what feature options are shown and how many

        ## ---- File combo menus ---- ##
        self.fileComboOne = QComboBox()
        self.fileComboOne.addItem(self.default_text)
        self.fileComboOne.currentTextChanged.connect(lambda text: self.updateFeatureCombo(text, 0))

        self.fileComboTwo = QComboBox()
        self.fileComboTwo.addItem(self.default_text)
        self.fileComboTwo.currentTextChanged.connect(lambda text: self.updateFeatureCombo(text, 1))

        self.fileComboBar = QHBoxLayout()
        self.fileComboBar.addWidget(self.fileComboOne)
        self.fileComboBar.addWidget(self.fileComboTwo)
        # choosing a new file should update what feature options are shown

        ## ---- Feature combo menus ---- ##
        self.featureComboOne = QComboBox()
        self.featureComboOne.currentTextChanged.connect(lambda text: self.updateGraphView(text, 0))

        self.featureComboTwo = QComboBox()
        self.featureComboTwo.currentTextChanged.connect(lambda text: self.updateGraphView(text, 1))

        self.featureComboBar = QHBoxLayout()
        self.featureComboBar.addWidget(self.featureComboOne)
        self.featureComboBar.addWidget(self.featureComboTwo)
        # choosing a new feature should update what the graph is showing

        self.graphView = MplCanvas(self)

        self.generateButton = QPushButton("Generate Graph")
        self.generateButton.clicked.connect(self.generateGraph)

        layout = QVBoxLayout()
        layout.addWidget(self.tableCombo)
        layout.addLayout(self.fileComboBar)
        layout.addLayout(self.featureComboBar)
        layout.addWidget(self.graphView)
        layout.addWidget(self.generateButton)

        self.setLayout(layout)

        # set default values
        self.tableCombo.setCurrentText(self.default_text)
        self.fileCombo.setCurrentText(self.default_text)

    def updateDialogOptions(self, gtype: str):
        # if same table type then no need to update
        if gtype == self.graphType:
            return
        elif gtype == self.default_text:
            self.graphType = ""
            return

        # update graph settings
        self.graphType = gtype
        self.dataType = self.table_options[gtype][0]
        self.numInputs = self.table_options[gtype][1]

        if self.numInputs == 1:
            self.featureComboOne.setVisible(True)
            self.fileComboOne.setVisible(True)

            self.fileComboTwo.setVisible(False)
            self.featureComboTwo.setVisible(False)
        if self.numInputs == 2:
            self.featureComboOne.setVisible(True)
            self.fileComboOne.setVisible(True)

            self.fileComboTwo.setVisible(True)
            self.featureComboTwo.setVisible(True)

        # update amount of file and feature selections
        self.updateFeatureCombo(self.activeFile, -1)
        self.updateGraphView("", -1)

    def updateFeatureCombo(self, file: str, num: int):
        # if same table file then no need to update
        if file == self.activeFile or num == -1:
            return
        elif file == self.default_text:
            self.activeFile = ""
            self.featureCombo.clear()
            return

        self.activeFile = file
        self.selectedFiles[num] = file

        # clear the current list of items
        self.featureCombo.clear()
        data_report = self.generate_report(self.dataframes[file])


        if self.dataType == "":
            return
        self.featureCombo.addItems(data_report[self.dataType])

    def updateGraphView(self, feature: str, num: int):
        if not self.activeFile or feature == "" or num == -1:
            return

        df = self.dataframes[self.activeFile]

        if feature not in df.columns:
            return

        self.selectedFeatures[num] = feature

    def generateGraph(self):
        # if the user has not selected the correct amount of files / features
        if self.graphType == "Histogram":
            if self.hist_file.currentText() == self.default_text or self.hist_feature.currentText() == self.default_text:
                return

            df = self.dataframes[self.hist_file.currentText()]
            feature = self.hist_feature.currentText()

            self.graphView.ax.clear()

            self.graphView.ax.hist(df[feature].dropna(), bins=10)

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

    def generate_histo_inputs(self):
        widget = QWidget()
        layout = QFormLayout()

        self.hist_file = QComboBox()
        self.hist_file.addItems(list(self.table_options.keys()))

        self.hist_feature = QComboBox()

        self.bins = QSlider()
        self.bins.setRange(1, 100)

        layout.addRow("File:", self.hist_file)
        layout.addRow("Feature:", self.hist_feature)
        layout.addRow("Bins:", self.bins)

        widget.setLayout(layout)
        return widget

    def generate_box_inputs(self):
        pass

    def generate_scatter_inputs(self):
        pass

    def generate_heatmap_inputs(self):
        pass

    def generate_bar_inputs(self):
        pass

    def generate_pie_inputs(self):
        pass