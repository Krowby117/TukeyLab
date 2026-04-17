
import ollama
from PySide6.QtWidgets import QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit
from PySide6.QtCore import QThread, Signal

class ChatbotGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.is_thinking = False

        self.input = QLineEdit()
        self.input.setPlaceholderText("Enter messsage here...")

        self.button = QPushButton("Send")
        self.button.clicked.connect(self.send_message)

        self.chatlog = QTextEdit()
        self.chatlog.setReadOnly(True)

        self.messageBar = QHBoxLayout()
        self.messageBar.addWidget(self.input)
        self.messageBar.addWidget(self.button)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.chatlog)
        self.layout.addLayout(self.messageBar)

        self.setLayout(self.layout)

    def send_message(self):
        if self.is_thinking:
            return

        message = self.input.text()
        if message:
            # don't let the user send a new message until the worker is done
            self.is_thinking = True
            self.button.setEnabled(False)

            # print out the users message
            self.chatlog.append(f"You: {message} \n")
            self.input.clear()

            # start worker thread and print out the response
            self.worker = LLMWorker(message)
            self.worker.finished.connect(self.display_response)
            self.worker.finished.connect(self.on_finish)
            self.worker.start()

    def display_response(self, response):
        self.chatlog.append(f"Bot: {response}")

    def on_finish(self):
        self.is_thinking = False
        self.button.setEnabled(True)

class LLMWorker(QThread):
    finished = Signal(str)

    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt

    def run(self):
        response = self.ask_llm()
        self.finished.emit(response)

    def ask_llm(self):
        response = ollama.chat(
            model='phi',
            messages=[
                {'role': 'user', 'content': f"Answer clearly: {self.prompt}"}
            ]
        )

        return response['message']['content']