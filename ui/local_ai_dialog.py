"""
ui/local_ai_dialog.py
---------------------
Local AI setup dialog với proper threading.
Dùng Qt Signal để communicate cross-thread - không bị treo.
"""

import threading
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QLineEdit, QTabWidget,
    QWidget, QTextEdit, QGroupBox, QFormLayout,
    QProgressBar, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QObject, QThread
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl

from settings import settings


# ==================================================
# STYLESHEET
# ==================================================

DIALOG_STYLE = """
QDialog {
    background-color: #0a0a16;
    color: #c0c0d8;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 12px;
}

QTabWidget::pane {
    border: 1px solid #1e1e38;
    border-radius: 3px;
    background: #0a0a16;
}

QTabBar::tab {
    background: #0e0e22;
    border: 1px solid #1e1e38;
    border-bottom: none;
    padding: 6px 14px;
    color: #6060a0;
    margin-right: 2px;
    border-radius: 3px 3px 0 0;
    font-size: 11px;
}

QTabBar::tab:selected {
    background: #141430;
    color: #a0a0e0;
    border-color: #2a2a50;
}

QTabBar::tab:hover {
    background: #121228;
    color: #8080c0;
}

QGroupBox {
    background: rgba(12, 12, 26, 180);
    border: 1px solid #1e1e38;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 10px;
    color: #505090;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 1px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}

QLabel {
    color: #9090b8;
    background: transparent;
}

QTextEdit#info_box {
    background: #060610;
    border: 1px solid #1a1a32;
    border-radius: 3px;
    color: #7070a0;
    font-family: 'Consolas', monospace;
    font-size: 10px;
    padding: 6px;
}

QLineEdit, QComboBox {
    background: #0c0c20;
    border: 1px solid #1e1e38;
    border-radius: 3px;
    padding: 4px 8px;
    color: #c0c0d8;
    min-height: 22px;
}

QLineEdit:focus, QComboBox:focus {
    border-color: #3a3a80;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #4040a0;
    margin-right: 6px;
}

QComboBox QAbstractItemView {
    background: #0c0c20;
    border: 1px solid #1e1e38;
    selection-background-color: #1e1e40;
    color: #c0c0d8;
    outline: none;
}

QPushButton {
    background: #121228;
    border: 1px solid #2a2a48;
    border-radius: 3px;
    padding: 5px 14px;
    color: #a0a0c8;
    min-height: 24px;
}

QPushButton:hover {
    background: #1c1c38;
    border-color: #4040a0;
    color: #c0c0e8;
}

QPushButton:pressed {
    background: #0a0a1e;
}

QPushButton:disabled {
    background: #0c0c1e;
    border-color: #1a1a30;
    color: #404060;
}

QPushButton#test_btn {
    background: #0e1e30;
    border-color: #204060;
    color: #4090c0;
}

QPushButton#test_btn:hover {
    background: #142030;
    border-color: #3060a0;
    color: #60b0e0;
}

QPushButton#test_btn:disabled {
    background: #0a1220;
    border-color: #152030;
    color: #304050;
}

QPushButton#pull_btn {
    background: #0e201e;
    border-color: #205048;
    color: #40a090;
}

QPushButton#pull_btn:hover {
    background: #142826;
    border-color: #30806a;
    color: #60c0b0;
}

QPushButton#pull_btn:disabled {
    background: #0a1410;
    border-color: #153028;
    color: #304840;
}

QPushButton#link_btn {
    background: transparent;
    border: none;
    color: #5050b0;
    padding: 2px 4px;
    min-height: 18px;
    text-align: left;
}

QPushButton#link_btn:hover {
    color: #8080e0;
}

QPushButton#apply_btn {
    background: #141838;
    border-color: #303878;
    color: #8080d0;
    font-weight: bold;
    padding: 6px 16px;
}

QPushButton#apply_btn:hover {
    background: #1c2050;
    border-color: #4848a0;
    color: #a0a0f0;
}

QProgressBar {
    background: #0a0a1e;
    border: 1px solid #1e1e38;
    border-radius: 3px;
    height: 8px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background: #2a4a80;
    border-radius: 2px;
}

QScrollArea {
    background: transparent;
    border: none;
}

QScrollBar:vertical {
    background: #080810;
    width: 6px;
    border: none;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background: #252540;
    border-radius: 3px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #353560;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}
"""


# ==================================================
# THREAD-SAFE TEST WORKER
# Uses Qt Signals so result always arrives on UI thread
# ==================================================

class TestWorker(QObject):
    """
    Runs backend test in a background thread.
    Emits result_ready signal on completion (Qt-thread-safe).
    """
    result_ready = Signal(bool, str)  # (success, message)

    def __init__(self, backend_type: str, host: str, model: str = ""):
        super().__init__()
        self.backend_type = backend_type
        self.host         = host
        self.model        = model

    def run(self):
        """Execute the test - called from background thread."""
        ok  = False
        msg = "Test failed"
        try:
            if self.backend_type == "ollama":
                from translator import OllamaBackend
                b = OllamaBackend(host=self.host, model=self.model)
                ok, msg = b.test_connection()

            elif self.backend_type == "lmstudio":
                from translator import LMStudioBackend
                b = LMStudioBackend(host=self.host, model=self.model)
                ok, msg = b.test_connection()

            elif self.backend_type == "llamacpp":
                from translator import LlamaCppBackend
                b = LlamaCppBackend(host=self.host)
                ok, msg = b.test_connection()

        except Exception as e:
            ok  = False
            msg = str(e)

        self.result_ready.emit(ok, msg)


class PullWorker(QObject):
    """
    Downloads an Ollama model in background.
    Emits progress and finished signals.
    """
    progress = Signal(str)   # status text
    finished = Signal(bool)  # success

    def __init__(self, host: str, model: str):
        super().__init__()
        self.host  = host
        self.model = model

    def run(self):
        try:
            from translator import OllamaBackend
            b  = OllamaBackend(host=self.host, model=self.model)
            ok = b.pull_model(self.model, progress_cb=self.progress.emit)
            self.finished.emit(ok)
        except Exception as e:
            print(f"[Pull] Error: {e}")
            self.finished.emit(False)


# ==================================================
# BASE TAB WITH SHARED TEST LOGIC
# ==================================================

class BaseLocalAITab(QWidget):
    """
    Shared base for all local AI tabs.
    Provides thread-safe test_connection() pattern.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._test_thread: QThread = None
        self._test_worker: TestWorker = None

    def _run_test(
        self,
        backend_type: str,
        host: str,
        model: str,
        btn: QPushButton,
        label: QLabel,
    ):
        """
        Run a connection test in background thread.
        Uses QThread + Signal for proper cross-thread safety.

        Args:
            backend_type: "ollama", "lmstudio", "llamacpp"
            host: Server URL
            model: Model name (empty for llamacpp)
            btn: Button to disable during test
            label: Label to show result in
        """
        # Prevent double-click
        if self._test_thread and self._test_thread.isRunning():
            return

        # Update UI immediately
        btn.setEnabled(False)
        btn.setText("Testing...")
        label.setText("Connecting...")
        label.setStyleSheet("color: #4060a0; font-size: 10px;")

        # Create worker + thread
        self._test_worker = TestWorker(backend_type, host, model)
        self._test_thread = QThread()
        self._test_worker.moveToThread(self._test_thread)

        # Wire signals
        self._test_thread.started.connect(self._test_worker.run)
        self._test_worker.result_ready.connect(
            lambda ok, msg: self._on_test_result(ok, msg, btn, label)
        )
        self._test_worker.result_ready.connect(self._test_thread.quit)
        self._test_thread.finished.connect(self._test_thread.deleteLater)

        self._test_thread.start()

    def _on_test_result(
        self,
        ok: bool,
        msg: str,
        btn: QPushButton,
        label: QLabel,
    ):
        """Receive test result on UI thread."""
        btn.setEnabled(True)
        btn.setText("⚡  Test Connection")

        if ok:
            label.setText(f"✓  {msg}")
            label.setStyleSheet("color: #40a060; font-size: 10px;")
        else:
            label.setText(f"✗  {msg}")
            label.setStyleSheet("color: #a04040; font-size: 10px;")


# ==================================================
# OLLAMA TAB
# ==================================================

class OllamaTab(BaseLocalAITab):
    """Setup tab for Ollama."""

    model_changed = Signal(str)

    MODELS = [
        # (display, tag, size, ram, note)
        ("qwen2.5:7b",  "qwen2.5:7b",  "4.7 GB", "8 GB",  "⭐ Best for EN↔VI/ZH"),
        ("qwen2.5:3b",  "qwen2.5:3b",  "2.0 GB", "4 GB",  "Lightweight + fast"),
        ("qwen2.5:14b", "qwen2.5:14b", "9.0 GB", "16 GB", "Highest quality"),
        ("gemma3:4b",   "gemma3:4b",   "3.3 GB", "6 GB",  "Good all-rounder"),
        ("gemma3:12b",  "gemma3:12b",  "8.1 GB", "12 GB", "Better quality"),
        ("llama3.2:3b", "llama3.2:3b", "2.0 GB", "4 GB",  "Very fast"),
        ("mistral:7b",  "mistral:7b",  "4.1 GB", "8 GB",  "Good for EU languages"),
        ("aya:8b",      "aya:8b",      "4.8 GB", "8 GB",  "Multilingual specialist"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pull_thread: QThread = None
        self._pull_worker: PullWorker = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        # ── Install instructions ───────────────────
        inst = QGroupBox("Installation")
        inst_l = QVBoxLayout(inst)
        inst_l.setSpacing(6)
        inst_l.setContentsMargins(10, 10, 10, 8)

        steps = QLabel(
            "1.  Download & install Ollama  (Windows installer)\n"
            "2.  Ollama runs automatically in background\n"
            "3.  Pull a model using the selector below\n"
            "4.  Click  Test Connection  to verify"
        )
        steps.setStyleSheet(
            "color: #7070a0; font-size: 11px; line-height: 1.5;"
        )
        steps.setWordWrap(True)
        inst_l.addWidget(steps)

        link_row = QHBoxLayout()
        link_btn = QPushButton("🔗  ollama.ai  —  download page")
        link_btn.setObjectName("link_btn")
        link_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://ollama.ai"))
        )
        link_row.addWidget(link_btn)
        link_row.addStretch()
        inst_l.addLayout(link_row)
        layout.addWidget(inst)

        # ── Model selection ───────────────────────
        model_g = QGroupBox("Model")
        model_f = QFormLayout(model_g)
        model_f.setSpacing(8)
        model_f.setContentsMargins(10, 12, 10, 10)
        model_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._model_combo = QComboBox()
        for display, tag, size, ram, note in self.MODELS:
            self._model_combo.addItem(
                f"{display}  ({size}, {ram})  —  {note}", tag
            )
        self._model_combo.currentIndexChanged.connect(self._on_model_selected)
        model_f.addRow("Select:", self._model_combo)

        self._custom_model = QLineEdit()
        self._custom_model.setPlaceholderText(
            "or type custom model name  (e.g. phi3:mini)"
        )
        self._custom_model.editingFinished.connect(self._on_custom_model)
        model_f.addRow("Custom:", self._custom_model)

        self._host_edit = QLineEdit()
        self._host_edit.setPlaceholderText("http://localhost:11434")
        self._host_edit.setText(
            settings.get("ollama_host", "http://localhost:11434")
        )
        self._host_edit.editingFinished.connect(self._save)
        model_f.addRow("Host:", self._host_edit)

        layout.addWidget(model_g)

        # ── Pull model ────────────────────────────
        pull_g = QGroupBox("Download Model")
        pull_l = QVBoxLayout(pull_g)
        pull_l.setSpacing(6)
        pull_l.setContentsMargins(10, 10, 10, 10)

        pull_info = QLabel(
            "Pull downloads the selected model (~2–9 GB).\n"
            "Models saved in  C:\\Users\\<you>\\.ollama\\models"
        )
        pull_info.setStyleSheet("color: #606080; font-size: 10px;")
        pull_info.setWordWrap(True)
        pull_l.addWidget(pull_info)

        pull_row = QHBoxLayout()
        self._pull_btn = QPushButton("⬇  Pull / Download Model")
        self._pull_btn.setObjectName("pull_btn")
        self._pull_btn.clicked.connect(self._pull_model)
        pull_row.addWidget(self._pull_btn)

        self._pull_status = QLabel("")
        self._pull_status.setStyleSheet("font-size: 10px; color: #4080a0;")
        pull_row.addWidget(self._pull_status, 1)
        pull_l.addLayout(pull_row)

        self._pull_progress = QProgressBar()
        self._pull_progress.setRange(0, 0)
        self._pull_progress.setVisible(False)
        self._pull_progress.setFixedHeight(6)
        pull_l.addWidget(self._pull_progress)

        layout.addWidget(pull_g)

        # ── Test connection ───────────────────────
        test_g = QGroupBox("Connection Test")
        test_l = QVBoxLayout(test_g)
        test_l.setContentsMargins(10, 10, 10, 10)

        test_row = QHBoxLayout()
        self._test_btn = QPushButton("⚡  Test Connection")
        self._test_btn.setObjectName("test_btn")
        self._test_btn.setFixedWidth(160)
        self._test_btn.clicked.connect(self._do_test)
        test_row.addWidget(self._test_btn)

        self._test_result = QLabel("Click to test Ollama connection")
        self._test_result.setStyleSheet("font-size: 10px; color: #404060;")
        self._test_result.setWordWrap(True)
        test_row.addWidget(self._test_result, 1)

        test_l.addLayout(test_row)
        layout.addWidget(test_g)

        # ── CLI reference ─────────────────────────
        cli_g = QGroupBox("Terminal Commands")
        cli_l = QVBoxLayout(cli_g)
        cli_l.setContentsMargins(10, 10, 10, 10)

        cli = QTextEdit()
        cli.setObjectName("info_box")
        cli.setReadOnly(True)
        cli.setFixedHeight(95)
        cli.setPlainText(
            "# Pull recommended model (4.7 GB):\n"
            "ollama pull qwen2.5:7b\n\n"
            "# Lightweight options:\n"
            "ollama pull qwen2.5:3b\n"
            "ollama pull gemma3:4b\n\n"
            "# List installed models:\n"
            "ollama list"
        )
        cli_l.addWidget(cli)
        layout.addWidget(cli_g)

        layout.addStretch()
        self._load_settings()

    def _load_settings(self):
        model = settings.get("ollama_model", "qwen2.5:7b")
        for i in range(self._model_combo.count()):
            if self._model_combo.itemData(i) == model:
                self._model_combo.setCurrentIndex(i)
                return
        self._custom_model.setText(model)

    def _get_current_model(self) -> str:
        custom = self._custom_model.text().strip()
        if custom:
            return custom
        return self._model_combo.currentData() or "qwen2.5:7b"

    def _on_model_selected(self):
        self._custom_model.clear()
        self._save()

    def _on_custom_model(self):
        if self._custom_model.text().strip():
            self._save()

    def _save(self):
        settings.update({
            "ollama_model": self._get_current_model(),
            "ollama_host":  self._host_edit.text().strip()
                            or "http://localhost:11434",
        })

    def _do_test(self):
        """Start async test using base class helper."""
        self._save()
        self._run_test(
            backend_type="ollama",
            host=self._host_edit.text().strip() or "http://localhost:11434",
            model=self._get_current_model(),
            btn=self._test_btn,
            label=self._test_result,
        )

    def _pull_model(self):
        """Download selected model via Ollama API."""
        if self._pull_thread and self._pull_thread.isRunning():
            return

        model = self._get_current_model()
        host  = self._host_edit.text().strip() or "http://localhost:11434"

        self._pull_btn.setEnabled(False)
        self._pull_btn.setText("⬇  Pulling...")
        self._pull_progress.setVisible(True)
        self._pull_status.setText(f"Starting download: {model}")
        self._pull_status.setStyleSheet("font-size: 10px; color: #4080a0;")

        self._pull_worker = PullWorker(host, model)
        self._pull_thread = QThread()
        self._pull_worker.moveToThread(self._pull_thread)

        self._pull_thread.started.connect(self._pull_worker.run)
        self._pull_worker.progress.connect(self._on_pull_progress)
        self._pull_worker.finished.connect(self._on_pull_done)
        self._pull_worker.finished.connect(self._pull_thread.quit)
        self._pull_thread.finished.connect(self._pull_thread.deleteLater)

        self._pull_thread.start()

    def _on_pull_progress(self, status: str):
        short = status[:65] + "..." if len(status) > 65 else status
        self._pull_status.setText(short)

    def _on_pull_done(self, success: bool):
        self._pull_btn.setEnabled(True)
        self._pull_btn.setText("⬇  Pull / Download Model")
        self._pull_progress.setVisible(False)

        if success:
            self._pull_status.setText("✓  Download complete!")
            self._pull_status.setStyleSheet("font-size: 10px; color: #40a060;")
        else:
            self._pull_status.setText("✗  Download failed — check terminal")
            self._pull_status.setStyleSheet("font-size: 10px; color: #a04040;")


# ==================================================
# LM STUDIO TAB
# ==================================================

class LMStudioTab(BaseLocalAITab):
    """Setup tab for LM Studio."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        # Instructions
        inst = QGroupBox("Installation")
        inst_l = QVBoxLayout(inst)
        inst_l.setContentsMargins(10, 10, 10, 8)

        steps = QLabel(
            "1.  Download LM Studio  (Windows installer)\n"
            "2.  Open LM Studio  →  search & download a model\n"
            "       Recommended:  Qwen2.5-7B-Instruct-GGUF\n"
            "3.  Go to  ↔ Local Server  tab  →  load model\n"
            "4.  Click  Start Server  (default port: 1234)\n"
            "5.  Click Test Connection below"
        )
        steps.setStyleSheet(
            "color: #7070a0; font-size: 11px; line-height: 1.5;"
        )
        steps.setWordWrap(True)
        inst_l.addWidget(steps)

        link_row = QHBoxLayout()
        link_btn = QPushButton("🔗  lmstudio.ai  —  download page")
        link_btn.setObjectName("link_btn")
        link_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://lmstudio.ai"))
        )
        link_row.addWidget(link_btn)
        link_row.addStretch()
        inst_l.addLayout(link_row)
        layout.addWidget(inst)

        # Connection settings
        conn = QGroupBox("Connection Settings")
        conn_f = QFormLayout(conn)
        conn_f.setSpacing(8)
        conn_f.setContentsMargins(10, 12, 10, 10)
        conn_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._host_edit = QLineEdit()
        self._host_edit.setText(
            settings.get("lmstudio_host", "http://localhost:1234")
        )
        self._host_edit.setPlaceholderText("http://localhost:1234")
        self._host_edit.editingFinished.connect(self._save)
        conn_f.addRow("API Host:", self._host_edit)

        self._model_edit = QLineEdit()
        self._model_edit.setText(
            settings.get("lmstudio_model", "local-model")
        )
        self._model_edit.setPlaceholderText(
            "Model ID shown in LM Studio server tab"
        )
        self._model_edit.editingFinished.connect(self._save)
        conn_f.addRow("Model ID:", self._model_edit)

        layout.addWidget(conn)

        # Recommended models
        rec = QGroupBox("Recommended Models  (search in LM Studio)")
        rec_l = QVBoxLayout(rec)
        rec_l.setContentsMargins(10, 10, 10, 10)

        rec_box = QTextEdit()
        rec_box.setObjectName("info_box")
        rec_box.setReadOnly(True)
        rec_box.setFixedHeight(110)
        rec_box.setPlainText(
            "Best models for translation quality:\n\n"
            "  Qwen2.5-7B-Instruct-GGUF     4.7 GB  ← Best for VI/ZH ⭐\n"
            "  Qwen2.5-14B-Instruct-GGUF    9.0 GB  ← High quality\n"
            "  Gemma-3-4B-Instruct-GGUF     3.3 GB  ← Fast, good quality\n"
            "  Mistral-7B-Instruct-v0.3      4.1 GB  ← EU languages\n"
            "  Llama-3.2-3B-Instruct-GGUF   2.0 GB  ← Lightweight\n\n"
            "In LM Studio: Search bar → type name → Download (↓)\n"
            "Then: Local Server tab → Load Model → Start Server"
        )
        rec_l.addWidget(rec_box)
        layout.addWidget(rec)

        # Test
        test_g = QGroupBox("Connection Test")
        test_l = QVBoxLayout(test_g)
        test_l.setContentsMargins(10, 10, 10, 10)

        test_row = QHBoxLayout()
        self._test_btn = QPushButton("⚡  Test Connection")
        self._test_btn.setObjectName("test_btn")
        self._test_btn.setFixedWidth(160)
        self._test_btn.clicked.connect(self._do_test)
        test_row.addWidget(self._test_btn)

        self._test_result = QLabel("Click to test LM Studio connection")
        self._test_result.setStyleSheet("font-size: 10px; color: #404060;")
        self._test_result.setWordWrap(True)
        test_row.addWidget(self._test_result, 1)
        test_l.addLayout(test_row)
        layout.addWidget(test_g)

        layout.addStretch()

    def _save(self):
        settings.update({
            "lmstudio_host":  self._host_edit.text().strip()
                              or "http://localhost:1234",
            "lmstudio_model": self._model_edit.text().strip()
                              or "local-model",
        })

    def _do_test(self):
        self._save()
        self._run_test(
            backend_type="lmstudio",
            host=self._host_edit.text().strip() or "http://localhost:1234",
            model=self._model_edit.text().strip() or "local-model",
            btn=self._test_btn,
            label=self._test_result,
        )


# ==================================================
# LLAMACPP TAB
# ==================================================

class LlamaCppTab(BaseLocalAITab):
    """Setup tab for llama.cpp server."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        # Instructions
        inst = QGroupBox("Setup")
        inst_l = QVBoxLayout(inst)
        inst_l.setContentsMargins(10, 10, 10, 8)

        steps = QLabel(
            "1.  Download llama.cpp Windows release (.zip)\n"
            "2.  Download a GGUF model  (HuggingFace)\n"
            "3.  Start server in terminal:\n"
            "       llama-server.exe -m model.gguf -c 4096 --port 8080\n"
            "4.  Click Test Connection below"
        )
        steps.setStyleSheet(
            "color: #7070a0; font-size: 11px; line-height: 1.5;"
        )
        steps.setWordWrap(True)
        inst_l.addWidget(steps)

        links_row = QHBoxLayout()
        for label, url in [
            ("🔗 llama.cpp releases",     "https://github.com/ggerganov/llama.cpp/releases"),
            ("🔗 GGUF models (HuggingFace)", "https://huggingface.co/models?search=qwen+gguf"),
        ]:
            b = QPushButton(label)
            b.setObjectName("link_btn")
            _u = url
            b.clicked.connect(
                lambda checked=False, u=_u: QDesktopServices.openUrl(QUrl(u))
            )
            links_row.addWidget(b)
        links_row.addStretch()
        inst_l.addLayout(links_row)
        layout.addWidget(inst)

        # Connection
        conn = QGroupBox("Connection Settings")
        conn_f = QFormLayout(conn)
        conn_f.setSpacing(8)
        conn_f.setContentsMargins(10, 12, 10, 10)
        conn_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._host_edit = QLineEdit()
        self._host_edit.setText(
            settings.get("llamacpp_host", "http://localhost:8080")
        )
        self._host_edit.setPlaceholderText("http://localhost:8080")
        self._host_edit.editingFinished.connect(self._save)
        conn_f.addRow("Server Host:", self._host_edit)

        layout.addWidget(conn)

        # Example command
        cmd_g = QGroupBox("Example Command")
        cmd_l = QVBoxLayout(cmd_g)
        cmd_l.setContentsMargins(10, 10, 10, 10)

        cmd_box = QTextEdit()
        cmd_box.setObjectName("info_box")
        cmd_box.setReadOnly(True)
        cmd_box.setFixedHeight(80)
        cmd_box.setPlainText(
            "# CPU only, no GPU needed (-ngl 0):\n"
            "llama-server.exe -m qwen2.5-7b-instruct-q4_k_m.gguf "
            "-c 4096 --port 8080 -ngl 0\n\n"
            "# With GPU acceleration:\n"
            "llama-server.exe -m model.gguf -c 4096 --port 8080 -ngl 33"
        )
        cmd_l.addWidget(cmd_box)
        layout.addWidget(cmd_g)

        # Test
        test_g = QGroupBox("Connection Test")
        test_l = QVBoxLayout(test_g)
        test_l.setContentsMargins(10, 10, 10, 10)

        test_row = QHBoxLayout()
        self._test_btn = QPushButton("⚡  Test Connection")
        self._test_btn.setObjectName("test_btn")
        self._test_btn.setFixedWidth(160)
        self._test_btn.clicked.connect(self._do_test)
        test_row.addWidget(self._test_btn)

        self._test_result = QLabel("Click to test llama.cpp connection")
        self._test_result.setStyleSheet("font-size: 10px; color: #404060;")
        self._test_result.setWordWrap(True)
        test_row.addWidget(self._test_result, 1)
        test_l.addLayout(test_row)
        layout.addWidget(test_g)

        layout.addStretch()

    def _save(self):
        settings.set(
            "llamacpp_host",
            self._host_edit.text().strip() or "http://localhost:8080"
        )

    def _do_test(self):
        self._save()
        self._run_test(
            backend_type="llamacpp",
            host=self._host_edit.text().strip() or "http://localhost:8080",
            model="",
            btn=self._test_btn,
            label=self._test_result,
        )


# ==================================================
# MAIN DIALOG
# ==================================================

class LocalAIDialog(QDialog):
    """Local AI setup dialog with 3 tabs."""

    backend_configured = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Local AI Setup — translatorTdev")
        self.setMinimumWidth(560)
        self.setMinimumHeight(540)
        self.setModal(True)
        self.setStyleSheet(DIALOG_STYLE)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # Header
        header = QLabel("  ⚙  Local AI Translation Setup")
        header.setStyleSheet(
            "color: #7070d0; font-size: 14px; font-weight: bold; "
            "background: transparent; padding: 4px 0;"
        )
        layout.addWidget(header)

        sub = QLabel(
            "Run AI translation 100% free and offline after model download. "
            "Ollama is recommended for most users."
        )
        sub.setStyleSheet("color: #606080; font-size: 11px;")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        # Quick comparison
        cmp = QTextEdit()
        cmp.setObjectName("info_box")
        cmp.setReadOnly(True)
        cmp.setFixedHeight(66)
        cmp.setPlainText(
            "  Provider      Ease      Quality    Min RAM    Internet after setup\n"
            "  ──────────────────────────────────────────────────────────────────\n"
            "  Ollama        ★★★★★    ★★★★☆     4 GB       Not needed  ✓\n"
            "  LM Studio     ★★★★☆    ★★★★☆     4 GB       Not needed  ✓\n"
            "  llama.cpp     ★★☆☆☆    ★★★★☆     4 GB       Not needed  ✓"
        )
        layout.addWidget(cmp)

        # Tabs
        self._tabs = QTabWidget()
        self._ollama_tab   = OllamaTab()
        self._lmstudio_tab = LMStudioTab()
        self._llamacpp_tab = LlamaCppTab()

        self._tabs.addTab(self._ollama_tab,   "  Ollama  (Recommended)  ")
        self._tabs.addTab(self._lmstudio_tab, "  LM Studio  ")
        self._tabs.addTab(self._llamacpp_tab, "  llama.cpp  ")
        layout.addWidget(self._tabs, 1)

        # Bottom buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        for label, backend in [
            ("✓ Use Ollama",    "ollama"),
            ("✓ Use LM Studio", "lmstudio"),
            ("✓ Use llama.cpp", "llamacpp"),
        ]:
            b = QPushButton(label)
            b.setObjectName("apply_btn")
            _backend = backend
            b.clicked.connect(
                lambda checked=False, n=_backend: self._apply(n)
            )
            btn_row.addWidget(b)

        btn_row.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _apply(self, backend_name: str):
        """Save backend choice and close dialog."""
        settings.set("translation_backend", backend_name)
        from translator import reset_translator
        reset_translator()
        self.backend_configured.emit(backend_name)
        self.accept()