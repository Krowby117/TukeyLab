
from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QVBoxLayout,
    QLabel,
    QStackedWidget,
    QHBoxLayout,
    QPlainTextEdit,
    QTextEdit,
    QMessageBox
)

import pandas as pd
import tempfile


from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtWebEngineWidgets import QWebEngineView

import plotly.express as px
import plotly.figure_factory as ff

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure()
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)

class PlotlyWebEngine(QWebEngineView):
    _graph_inputs = {
        "Histogram": 1,
        "Scatter Plot": 1,
        "Box Plot": 1,
        "Heatmap": 1,
        "KDE Plot": 1,
        "Correlation Matrix": 1,
        "Line Plot": 1,
        "Bar Chart": 1,
        "Violin Plot": 1,
        "Pie Chart": 1,
    }

    def __init__(self):
        super().__init__()

        self.page().setBackgroundColor(QColor("#1e1e1e"))

        self._curr_item = ""
        self._temp_file = ""
        self._dataframes = {}

    def add_dataframe(self, name: str, data: pd.DataFrame):
        self._dataframes[name] = data

    def set_dataframes(self, dfs: dict):
        self._dataframes = dict(dfs)

    def update_view(self, metadata: dict):
        html = self._generate_graph_html(metadata)
        self._load_html(html)

    def _load_html(self, html: str):
        if html == "":
            return

        self._temp_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
        self._temp_file.write(html)
        self._temp_file.close()
        self.load(QUrl.fromLocalFile(self._temp_file.name))

    def _generate_graph_html(self, metadata: dict):
        if metadata is None or not metadata:
            return ""

        name = metadata.get("name", "")
        graph_type = metadata.get("type")
        data = metadata.get("data")
        params = metadata.get("params")

        if not name or graph_type not in self._graph_inputs or not data:
            return ""

        if name == self._curr_item:
            return ""

        self._curr_item = name

        # resets the plot area so a fresh graph gets updated
        self.setHtml("")

        # graph the dataframe(s) needed for the graph
        if self._graph_inputs[graph_type] != 1:
            raise ValueError("Unsupported graph type")

        source = data[0]
        if source not in self._dataframes:
            return ""

        df = self._dataframes[source]

        if graph_type == "Histogram":
            feature = params["feature"]
            bins = params["bins"]

            fig = px.histogram(df, x=feature, nbins=bins, title=name)
            fig.update_layout(template="plotly_dark")
            return fig.to_html(include_plotlyjs=True, full_html=True)

        if graph_type == "Scatter Plot":
            scat_x = params["x"]
            scat_y = params["y"]

            fig = px.scatter(df, x=scat_x, y=scat_y, title=name)
            fig.update_layout(template="plotly_dark")
            return fig.to_html(include_plotlyjs=True, full_html=True)

        if graph_type == "Box Plot":
            feature = params

            fig = px.box(df, y=feature, title=name)
            fig.update_layout(template="plotly_dark")
            return fig.to_html(include_plotlyjs=True, full_html=True)

        if graph_type == "Heatmap":
            hm_x = params["x"]
            hm_y = params["y"]

            fig = px.density_heatmap(df, x=hm_x, y=hm_y, title=name)
            fig.update_layout(template="plotly_dark")
            return fig.to_html(include_plotlyjs=True, full_html=True)

        if graph_type == "KDE Plot":
            feature = params

            fig = ff.create_distplot(
                hist_data=[df[feature].dropna().tolist()],
                group_labels=[feature],
                show_hist=False,
                show_rug=False,
            )
            fig.update_layout(template="plotly_dark")
            return fig.to_html(include_plotlyjs=True, full_html=True)

        if graph_type == "Correlation Matrix":
            corr = df.corr(numeric_only=True)

            fig = px.imshow(corr, title=name)
            fig.update_layout(template="plotly_dark")
            return fig.to_html(include_plotlyjs=True, full_html=True)

        if graph_type == "Line Plot":
            line_x = params["x"]
            line_y = params["y"]

            fig = px.line(df, x=line_x, y=line_y, title=name)
            fig.update_layout(template="plotly_dark")
            return fig.to_html(include_plotlyjs=True, full_html=True)

        if graph_type == "Bar Chart":
            bar_x = params["x"]
            bar_y = params["y"]

            fig = px.bar(df, x=bar_x, y=bar_y, title=name)
            fig.update_layout(template="plotly_dark")
            return fig.to_html(include_plotlyjs=True, full_html=True)

        if graph_type == "Violin Plot":
            feature = params

            fig = px.violin(df, y=feature, box=True, title=name)
            fig.update_layout(template="plotly_dark")
            return fig.to_html(include_plotlyjs=True, full_html=True)

        if graph_type == "Pie Chart":
            pie_names = params["names"]
            pie_values = params["values"]

            fig = px.pie(df, names=pie_names, values=pie_values, title=name)
            fig.update_layout(template="plotly_dark")
            return fig.to_html(include_plotlyjs=True, full_html=True)

        return ""

class NotesWidget(QWidget):
    save_note = Signal(str)
    def __init__(self):
        super().__init__()

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # top menu bar
        self.top_bar = QWidget()
        self.top_layout = QHBoxLayout(self.top_bar)
        self.top_label = QLabel("Project Notes: ")

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save)

        self.toggle_btn = QPushButton("Preview")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.clicked.connect(self.toggle_preview)

        self.top_layout.addWidget(self.top_label)
        self.top_layout.addStretch()
        self.top_layout.addWidget(self.save_btn)
        self.top_layout.addWidget(self.toggle_btn)

        # stacked widget to switch modes
        self.stack = QStackedWidget()

        # markdown editor mode
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Type your markdown here...")
        self.editor.setStyleSheet("QPlainTextEdit { border: 1px solid #404040; border-radius: 8px; background-color: #252526; color: #e7e7e7; padding: 8px; font-size: 12px; }")

        # markdown preview mode
        self.viewer = QTextEdit()
        self.viewer.setReadOnly(True)
        self.viewer.setStyleSheet("QTextEdit { border: 1px solid #404040; border-radius: 8px; background-color: #252526; color: #e7e7e7; padding: 8px; font-size: 12px; }")

        self.stack.addWidget(self.editor)  # Index 0
        self.stack.addWidget(self.viewer)  # Index 1

        # set up main layout
        self.main_layout.addWidget(self.top_bar)
        self.main_layout.addWidget(self.stack)
        self.setLayout(self.main_layout)

    def save(self):
        msg = QMessageBox()
        msg.setWindowTitle("Confirm Save")
        msg.setText("Are you sure you want to save? Saving the project notes will overwrite the previous save.")

        accept_btn = msg.addButton("Save Anyway", QMessageBox.AcceptRole)
        deny_btn = msg.addButton("Cancel", QMessageBox.RejectRole)
        msg.exec()

        if msg.clickedButton() == accept_btn:
            self.save_note.emit(self.editor.toPlainText())

    def open_note(self, note: str):
        self.editor.setPlainText(note)
        self.viewer.setMarkdown(note)

    def toggle_preview(self):
        if self.toggle_btn.isChecked():
            # switch to preview Mode
            markdown_text = self.editor.toPlainText()
            self.viewer.setMarkdown(markdown_text) # display as markdown

            self.stack.setCurrentIndex(1)
            self.toggle_btn.setText("Edit Mode")
        else:
            # switch to edit Mode
            self.stack.setCurrentIndex(0)
            self.toggle_btn.setText("Preview Mode")