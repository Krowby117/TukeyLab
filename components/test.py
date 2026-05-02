import sys
import tempfile
import os
import pandas as pd
import plotly.express as px

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView


def build_html() -> str:
    """Generate a simple Plotly scatter chart as a self-contained HTML string."""
    df = pd.DataFrame({
        "x": [1, 2, 3, 4, 5],
        "y": [10, 4, 7, 2, 9],
        "label": ["A", "B", "C", "D", "E"],
    })
    fig = px.scatter(df, x="x", y="y", text="label", title="QWebEngineView + Plotly Test")
    fig.update_traces(textposition="top center", marker=dict(size=12))
    fig.update_layout(template="plotly_dark")
    return fig.to_html(include_plotlyjs=True, full_html=True)


def load_plotly(view: QWebEngineView) -> str:
    """Write HTML to a temp file and load it — avoids QWebEngineView's 2 MB setHtml limit."""
    html = build_html()
    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
    tmp.write(html)
    tmp.close()
    view.load(QUrl.fromLocalFile(tmp.name))
    return tmp.name  # caller can delete later if desired


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plotly + QWebEngineView")
        self.resize(900, 600)

        self.web = QWebEngineView()
        self._tmp_file = load_plotly(self.web)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web)
        self.setCentralWidget(container)

    def closeEvent(self, event):
        # Clean up temp file on close
        if os.path.exists(self._tmp_file):
            os.remove(self._tmp_file)
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
