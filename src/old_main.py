import sys
import random
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDial,
    QDoubleSpinBox,
    QFontComboBox,
    QLabel,
    QLCDNumber,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
    QMenu
)

window_titles = [
    "My App",
    "My App",
    "Still My App",
    "Still My App",
    "What on earth",
    "What on earth",
    "This is surprising",
    "This is surprising",
    "Something went wrong",
]

# Subclass of QMainWindow to customize the application main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")

        self.button_is_checked = False

        self.button = QPushButton("Press Me!")
        self.button.clicked.connect(self.button_clicked)

        self.windowTitleChanged.connect(self.window_title_changed)

        self.checkbox = QCheckBox("This guy's a fucking idiot")

        self.image = QLabel()
        self.image.setPixmap(QPixmap("ross.png"))
        self.image.setScaledContents(True)

        layout = QVBoxLayout()
        layout.addWidget(self.image)
        layout.addWidget(self.checkbox)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def button_clicked(self):
        new_window_title = random.choice(window_titles)
        self.setWindowTitle(new_window_title)

    def window_title_changed(self, window_title):
        if window_title == "Something went wrong":
            self.button.setDisabled(True)

    def contextMenuEvent(self, e):
        context = QMenu(self)
        context.addAction(QAction("test 1", self))
        context.addAction(QAction("test 2", self))
        context.addAction(QAction("test 3", self))
        context.exec(e.globalPos())

if __name__ == "__main__":
    app = QApplication([])

    widget = MainWindow()
    widget.show()

    app.exec()