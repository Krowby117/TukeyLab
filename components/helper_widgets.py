
from PySide6.QtCore import QUrl
from PySide6.QtGui import QColor


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

