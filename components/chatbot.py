from __future__ import annotations

from PySide6.QtWidgets import QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel
from PySide6.QtCore import QThread, Signal

from components.project_ai import DatasetCatalogController


class ChatbotGUI(QWidget):
    def __init__(self, controller: DatasetCatalogController):
        super().__init__()

        self.is_thinking = False
        self.controller = controller
        self.history: list[dict[str, str]] = []

        self.header = QLabel("Project Dataset + EDA Assistant")
        self.header.setObjectName("chatHeader")

        self.input = QLineEdit()
        self.input.setObjectName("chatInput")
        self.input.setPlaceholderText("Ask about datasets, missing values, stats, and correlations...")
        self.input.returnPressed.connect(self.send_message)

        self.button = QPushButton("Send")
        self.button.setObjectName("sendButton")
        self.button.clicked.connect(self.send_message)

        self.chatlog = QTextEdit()
        self.chatlog.setObjectName("chatLog")
        self.chatlog.setReadOnly(True)

        self.messageBar = QHBoxLayout()
        self.messageBar.setSpacing(8)
        self.messageBar.addWidget(self.input)
        self.messageBar.addWidget(self.button)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)
        self.layout.addWidget(self.header)
        self.layout.addWidget(self.chatlog)
        self.layout.addLayout(self.messageBar)

        self.setLayout(self.layout)
        self._setup_ui_style()
        self.chatlog.append(
            "Bot: I can help you explore project datasets with EDA tasks like overviews, missingness checks, summary stats, and correlations."
        )

    def _setup_ui_style(self):
        self.chatlog.setMinimumHeight(260)
        self.button.setMinimumWidth(72)
        self.setStyleSheet(
            """
            QLabel#chatHeader {
                font-size: 13px;
                font-weight: 600;
                color: #d4d4d4;
                padding: 4px 2px;
            }
            QTextEdit#chatLog {
                border: 1px solid #404040;
                border-radius: 8px;
                background-color: #252526;
                color: #e7e7e7;
                padding: 8px;
                font-size: 12px;
            }
            QLineEdit#chatInput {
                border: 1px solid #505050;
                border-radius: 8px;
                background-color: #1f1f1f;
                color: #f0f0f0;
                padding: 7px 10px;
            }
            QLineEdit#chatInput:focus {
                border: 1px solid #4da3ff;
            }
            QPushButton#sendButton {
                border: 1px solid #4da3ff;
                border-radius: 8px;
                background-color: #2d5fa8;
                color: white;
                font-weight: 600;
                padding: 7px 12px;
            }
            QPushButton#sendButton:hover {
                background-color: #3a74c7;
            }
            QPushButton#sendButton:disabled {
                border-color: #666666;
                background-color: #3d3d3d;
                color: #b8b8b8;
            }
            """
        )

    def send_message(self):
        if self.is_thinking:
            return

        message = self.input.text()
        if message:
            self.is_thinking = True
            self.button.setEnabled(False)

            self.chatlog.append(f"You: {message} \n")
            self.input.clear()

            self.history.append({"role": "user", "content": message})
            self.history = self.history[-16:]

            self.worker = LLMWorker(message, list(self.history), self.controller)
            self.worker.finished.connect(self.display_response)
            self.worker.finished.connect(self.on_finish)
            self.worker.start()

    def display_response(self, response: str):
        self.chatlog.append(f"Bot: {response} \n")
        self.history.append({"role": "assistant", "content": response})
        self.history = self.history[-16:]

    def on_finish(self):
        self.is_thinking = False
        self.button.setEnabled(True)


class LLMWorker(QThread):
    finished = Signal(str)

    def __init__(self, prompt: str, history: list[dict[str, str]], controller: DatasetCatalogController):
        super().__init__()
        self.prompt = prompt
        self.history = history
        self.controller = controller

    def run(self):
        response = self.ask_controller()
        self.finished.emit(response)

    def ask_controller(self):
        return self.controller.process_message(self.prompt, self.history)
