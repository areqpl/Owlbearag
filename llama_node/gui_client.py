import sys
import httpx
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QMessageBox,
)
from PyQt6.QtCore import Qt

# Configuration - adjust as needed
SERVER_URL = "http://127.0.0.1:8000/query"  # FastAPI endpoint


def query_server(question: str) -> str:
    """Send a question to the RAG server and return the response text.

    Parameters
    ----------
    question: str
        The user query.
    Returns
    -------
    str
        The server's answer or an error message.
    """
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(SERVER_URL, json={"query": question})
            resp.raise_for_status()
            data = resp.json()
            # Expected response format from server.py
            return data.get("response", "[No response field]")
    except Exception as e:
        return f"Error contacting server: {e}"


class RAGGui(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Owlbearag RAG Assistant")
        self.setMinimumSize(600, 400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header / description
        header = QLabel("Ask a question and the RAG server will answer using the loaded index.")
        header.setWordWrap(True)
        layout.addWidget(header)

        # Input area
        input_layout = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Enter your question here…")
        input_layout.addWidget(self.input_edit)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.handle_send)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)

        # Response display
        self.response_box = QTextEdit()
        self.response_box.setReadOnly(True)
        layout.addWidget(self.response_box)

    def handle_send(self):
        query = self.input_edit.text().strip()
        if not query:
            QMessageBox.warning(self, "Empty query", "Please type a question before sending.")
            return
        self.response_box.append(f"▶️ <b>Question:</b> {query}\n")
        QApplication.processEvents()  # Update UI before network call
        answer = query_server(query)
        self.response_box.append(f"<b>Answer:</b> {answer}\n")
        self.input_edit.clear()


def main():
    app = QApplication(sys.argv)
    gui = RAGGui()
    gui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
