"""
ui/main_window.py
-----------------
Main window với:
- Custom background image support
- App icon
- Crash-safe stdout redirect
- Log panel
- Capture button
- Local AI backend support
"""

import sys
import os
import threading
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QSpinBox,
    QPushButton,
    QLineEdit,
    QCheckBox,
    QGroupBox,
    QFormLayout,
    QStatusBar,
    QSystemTrayIcon,
    QMenu,
    QApplication,
    QSlider,
    QFrame,
    QSizePolicy,
    QPlainTextEdit,
    QScrollArea,
    QFileDialog,
)
from PySide6.QtCore import Qt, Signal, QTimer, QDateTime
from PySide6.QtGui import QIcon, QFont, QAction, QTextCursor, QPainter, QPixmap, QColor

from settings import settings, ASSETS_DIR, SETTINGS_DIR

# ==================================================
# ASSET HELPERS
# ==================================================


def get_asset(name: str) -> str:
    return str(ASSETS_DIR / name)


def get_icon() -> QIcon:
    """Load app icon - works both from source and .exe"""
    # Thử theo thứ tự ưu tiên
    candidates = [
        get_asset("icon.ico"),
        get_asset("icon.png"),
    ]
    for path in candidates:
        if os.path.exists(path):
            icon = QIcon(path)
            if not icon.isNull():
                return icon

    # Fallback: thử load trực tiếp từ _MEIPASS nếu đang chạy exe
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        import sys as _sys

        for fname in ("icon.ico", "icon.png"):
            path = os.path.join(_sys._MEIPASS, "assets", fname)
            if os.path.exists(path):
                icon = QIcon(path)
                if not icon.isNull():
                    return icon

    return QIcon()


# ==================================================
# STYLESHEET
# ==================================================

STYLESHEET = """
QMainWindow, QWidget#central_widget {
    background-color: transparent;
    color: #c8c8d4;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 12px;
}

QWidget#scroll_content {
    background-color: transparent;
}

QScrollArea {
    background: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background: transparent;
}

QGroupBox {
    background-color: rgba(10, 10, 22, 170);
    border: 1px solid rgba(50, 50, 90, 180);
    border-radius: 5px;
    margin-top: 8px;
    padding-top: 10px;
    color: #5a5a90;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 1px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    background-color: transparent;
}

QLabel {
    color: #9090b0;
    background: transparent;
}

QComboBox, QLineEdit, QSpinBox {
    background-color: rgba(10, 10, 25, 200);
    border: 1px solid rgba(45, 45, 80, 200);
    border-radius: 3px;
    padding: 4px 8px;
    color: #c0c0d8;
    min-height: 22px;
    selection-background-color: rgba(60, 60, 120, 200);
}

QComboBox:hover, QLineEdit:hover, QSpinBox:hover {
    border-color: rgba(70, 70, 140, 220);
}

QComboBox:focus, QLineEdit:focus, QSpinBox:focus {
    border-color: rgba(80, 80, 180, 255);
    background-color: rgba(12, 12, 30, 220);
}

QComboBox::drop-down {
    border: none;
    width: 22px;
}

QComboBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid rgba(80, 80, 160, 220);
    margin-right: 6px;
}

QComboBox QAbstractItemView {
    background-color: rgb(14, 14, 28);
    border: 1px solid rgba(45, 45, 80, 220);
    selection-background-color: rgba(35, 35, 70, 255);
    color: #c0c0d8;
    outline: none;
    padding: 2px;
}

QPushButton {
    background-color: rgba(20, 20, 40, 200);
    border: 1px solid rgba(45, 45, 80, 200);
    border-radius: 4px;
    padding: 5px 14px;
    color: #b0b0cc;
    font-size: 12px;
    min-height: 24px;
}

QPushButton:hover {
    background-color: rgba(30, 30, 60, 220);
    border-color: rgba(80, 80, 160, 220);
    color: #c8c8e8;
}

QPushButton:pressed {
    background-color: rgba(12, 12, 28, 230);
}

QPushButton:disabled {
    background-color: rgba(14, 14, 28, 180);
    border-color: rgba(30, 30, 50, 160);
    color: rgba(80, 80, 100, 180);
}

QPushButton#capture_btn {
    background-color: rgba(25, 25, 65, 210);
    border: 1px solid rgba(70, 70, 160, 200);
    border-radius: 5px;
    color: rgba(160, 160, 255, 240);
    font-size: 13px;
    font-weight: bold;
    padding: 10px 20px;
    min-height: 40px;
    letter-spacing: 0.5px;
}

QPushButton#capture_btn:hover {
    background-color: rgba(35, 35, 85, 230);
    border-color: rgba(100, 100, 200, 230);
    color: rgba(190, 190, 255, 255);
}

QPushButton#capture_btn:pressed {
    background-color: rgba(15, 15, 45, 230);
}

QPushButton#capture_btn:disabled {
    background-color: rgba(16, 16, 36, 180);
    border-color: rgba(35, 35, 65, 160);
    color: rgba(60, 60, 90, 180);
}

QPushButton#primary_btn {
    background-color: rgba(22, 22, 55, 210);
    border-color: rgba(60, 60, 150, 200);
    color: rgba(180, 180, 255, 240);
}

QPushButton#primary_btn:hover {
    background-color: rgba(32, 32, 75, 230);
}

QPushButton#test_btn {
    background-color: rgba(10, 20, 35, 200);
    border-color: rgba(30, 60, 100, 200);
    color: rgba(60, 130, 180, 220);
    padding: 3px 10px;
    min-height: 20px;
    font-size: 11px;
}

QPushButton#test_btn:hover {
    background-color: rgba(15, 28, 48, 220);
    border-color: rgba(50, 90, 150, 220);
    color: rgba(80, 160, 220, 240);
}

QPushButton#setup_btn {
    background-color: rgba(15, 20, 40, 200);
    border-color: rgba(40, 50, 100, 200);
    color: rgba(100, 110, 190, 220);
    padding: 3px 8px;
    min-height: 20px;
    font-size: 11px;
}

QPushButton#setup_btn:hover {
    background-color: rgba(22, 28, 55, 220);
    border-color: rgba(60, 70, 150, 220);
}

QCheckBox {
    color: #9090b0;
    spacing: 6px;
    background: transparent;
}

QCheckBox::indicator {
    width: 13px;
    height: 13px;
    border: 1px solid rgba(50, 50, 90, 200);
    border-radius: 2px;
    background-color: rgba(10, 10, 22, 200);
}

QCheckBox::indicator:checked {
    background-color: rgba(50, 50, 160, 220);
    border-color: rgba(80, 80, 200, 220);
}

QSlider::groove:horizontal {
    height: 3px;
    background: rgba(30, 30, 60, 200);
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: rgba(70, 70, 170, 220);
    border: none;
    width: 13px;
    height: 13px;
    margin: -5px 0;
    border-radius: 7px;
}

QSlider::sub-page:horizontal {
    background: rgba(55, 55, 150, 200);
    border-radius: 2px;
}

QPlainTextEdit#log_panel {
    background-color: rgba(5, 5, 12, 210);
    color: #606080;
    border: 1px solid rgba(25, 25, 45, 200);
    border-radius: 3px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 10px;
    padding: 4px;
    selection-background-color: rgba(40, 40, 80, 200);
}

QScrollBar:vertical {
    background: rgba(8, 8, 16, 180);
    width: 7px;
    border: none;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background: rgba(35, 35, 70, 200);
    border-radius: 3px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(55, 55, 110, 220);
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    height: 0;
}

QStatusBar {
    background-color: rgba(5, 5, 12, 200);
    color: #404060;
    border-top: 1px solid rgba(20, 20, 40, 200);
    font-size: 10px;
    font-family: 'Consolas', monospace;
}

QFrame#sep {
    background-color: rgba(25, 25, 50, 140);
    border: none;
}

QLabel#hotkey_display {
    color: rgba(110, 110, 210, 240);
    font-family: 'Consolas', monospace;
    font-size: 14px;
    font-weight: bold;
    border: 1px solid rgba(50, 50, 100, 200);
    border-radius: 3px;
    padding: 3px 10px;
    background-color: rgba(10, 10, 28, 200);
}
"""


# ==================================================
# BACKGROUND WIDGET
# ==================================================


class BackgroundWidget(QWidget):
    """
    Central widget that renders a custom background image
    with a dark overlay for readability.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bg_pixmap = None
        self._bg_opacity = 0.30
        self._load_background()

    def _load_background(self):
        self._bg_pixmap = None

        # Try user custom background first
        if settings.get("use_custom_background"):
            custom_path = settings.get("custom_background", "")
            if custom_path and os.path.isfile(custom_path):
                pix = QPixmap(custom_path)
                if not pix.isNull():
                    self._bg_pixmap = pix
                    self._bg_opacity = settings.get("background_opacity", 0.35)
                    return

        # Try generated default background
        default_bg = get_asset("background.png")
        if os.path.isfile(default_bg):
            pix = QPixmap(default_bg)
            if not pix.isNull():
                self._bg_pixmap = pix
                self._bg_opacity = 0.30
                return

        # Try to generate it
        try:
            assets_script = ASSETS_DIR / "generate_assets.py"
            if assets_script.exists():
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    "generate_assets", assets_script
                )
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                mod.generate_background()
                if os.path.isfile(default_bg):
                    pix = QPixmap(default_bg)
                    if not pix.isNull():
                        self._bg_pixmap = pix
                        self._bg_opacity = 0.30
        except Exception as e:
            print(f"[BG] Could not generate background: {e}")

    def reload_background(self):
        self._load_background()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w, h = self.width(), self.height()

        # Base dark fill
        painter.fillRect(0, 0, w, h, QColor(8, 8, 16))

        # Background image
        if self._bg_pixmap and not self._bg_pixmap.isNull():
            painter.setOpacity(self._bg_opacity)
            scaled = self._bg_pixmap.scaled(
                w,
                h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x_off = (w - scaled.width()) // 2
            y_off = (h - scaled.height()) // 2
            painter.drawPixmap(x_off, y_off, scaled)

        # Dark overlay to keep UI readable
        painter.setOpacity(1.0)
        painter.fillRect(0, 0, w, h, QColor(5, 5, 14, 180))

        painter.end()


# ==================================================
# LOG PANEL
# ==================================================


class LogPanel(QPlainTextEdit):
    """Color-coded, auto-scrolling log display."""

    MAX_LINES = 300

    LEVELS = {
        "info": ("·", "#505075"),
        "ok": ("✓", "#3a8a5a"),
        "warn": ("!", "#8a7a30"),
        "error": ("✗", "#8a3a3a"),
        "debug": ("·", "#383855"),
        "ocr": ("◎", "#305a8a"),
        "trans": ("→", "#305a6a"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("log_panel")
        self.setReadOnly(True)
        self.setMaximumBlockCount(self.MAX_LINES)
        self.setPlaceholderText("Activity log...")
        self.setMinimumHeight(110)
        self.setMaximumHeight(190)

    def append_log(self, message: str, level: str = "info"):
        if not message.strip():
            return

        ts = QDateTime.currentDateTime().toString("HH:mm:ss")
        icon, color = self.LEVELS.get(level, ("·", "#505075"))

        msg = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        html = (
            f'<span style="color:#252540;">[{ts}]</span> '
            f'<span style="color:{color};">{icon} {msg}</span>'
        )
        self.appendHtml(html)

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.setTextCursor(cursor)


# ==================================================
# STDOUT REDIRECTOR
# ==================================================

# ==================================================
# THREAD-SAFE STDOUT REDIRECTOR
# ==================================================

from PySide6.QtCore import QObject, Signal as QtSignal


class _LogBridge(QObject):
    """
    Bridge object sống trên main thread.
    Nhận log từ bất kỳ thread nào qua signal → update GUI an toàn.
    """

    log_signal = QtSignal(str, str)  # message, level

    def __init__(self, log_panel: "LogPanel"):
        super().__init__()
        self._log = log_panel
        # QueuedConnection → luôn chạy trên main thread
        self.log_signal.connect(self._on_log, Qt.ConnectionType.QueuedConnection)

    def _on_log(self, message: str, level: str):
        """Chỉ được gọi trên main thread."""
        try:
            self._log.append_log(message, level)
        except Exception:
            pass

    def emit_log(self, message: str, level: str):
        """Gọi từ bất kỳ thread nào — an toàn."""
        try:
            self.log_signal.emit(message, level)
        except Exception:
            pass


class SafeStdoutRedirector:
    """
    Redirect print() → LogPanel an toàn từ mọi thread.

    Flow:
      Thread bất kỳ → print() → write() → emit Qt signal
      → Qt tự route về main thread (QueuedConnection)
      → main thread update GUI → KHÔNG CRASH
    """

    def __init__(self, log_panel: "LogPanel"):
        self._real = sys.__stdout__
        self._buf = ""
        self._lock = threading.Lock()
        self._bridge = _LogBridge(log_panel)

    def write(self, text: str):
        # 1. Luôn ghi ra real stdout (console) trước
        try:
            self._real.write(text)
            self._real.flush()
        except Exception:
            pass

        # 2. Buffer → tách dòng → emit signal (thread-safe)
        try:
            if not isinstance(text, str):
                text = str(text)

            lines_to_emit = []
            with self._lock:
                self._buf += text
                while "\n" in self._buf:
                    idx = self._buf.index("\n")
                    line = self._buf[:idx].strip()
                    self._buf = self._buf[idx + 1 :]
                    if line:
                        lines_to_emit.append(line)

            # Emit NGOÀI lock để tránh deadlock
            for line in lines_to_emit:
                self._bridge.emit_log(line, self._classify(line))

        except Exception:
            pass

    def flush(self):
        try:
            self._real.flush()
        except Exception:
            pass

    def fileno(self):
        """Cần cho một số thư viện check fileno."""
        try:
            return self._real.fileno()
        except Exception:
            return -1

    def _classify(self, line: str) -> str:
        l = line.lower()
        if any(k in l for k in ("error", "fail", "exception", "traceback", "crash")):
            return "error"
        if "warn" in l:
            return "warn"
        if "[ocr]" in l:
            return "ocr"
        if "[pipeline]" in l:
            return "trans" if "translat" in l else "ocr"
        if any(k in l for k in ("done", "ready", "success", "initialized", "loaded")):
            return "ok"
        if any(k in l for k in ("[app]", "[hotkey", "[setting", "[translator]")):
            return "info"
        return "debug"


# ==================================================
# MAIN WINDOW
# ==================================================


class MainWindow(QMainWindow):
    """
    Main application window.

    Signals:
        settings_changed  — any setting saved
        hotkey_changed(str) — hotkey updated
        capture_requested — user wants to capture
    """

    settings_changed = Signal()
    hotkey_changed = Signal(str)
    capture_requested = Signal()
    _test_result_signal = Signal(bool, str)  # thread-safe signal for test result

    def _restore_stdout(self):
        """Restore stdout khi app đóng."""
        try:
            sys.stdout = sys.__stdout__
        except Exception:
            pass

    def closeEvent(self, event):
        """Hide to tray on close."""
        event.ignore()
        self.hide()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._updating_ui = False
        self._is_processing = False
        self._redirector = None

        self._setup_window()
        self._build_ui()
        self._load_current_settings()
        self._setup_tray()
        self._setup_stdout_redirect()

        # Connect test result signal — Qt routes to UI thread safely
        self._test_result_signal.connect(self._update_test_label)

    # ──────────────────────────────────────────────
    # WINDOW SETUP
    # ──────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowTitle("translatorTdev")
        self.setMinimumWidth(460)
        self.setMaximumWidth(560)
        self.setMinimumHeight(500)

        icon = get_icon()
        if not icon.isNull():
            self.setWindowIcon(icon)
            QApplication.setWindowIcon(icon)

        self.setStyleSheet(STYLESHEET)

    # ──────────────────────────────────────────────
    # UI BUILD
    # ──────────────────────────────────────────────

    def _build_ui(self):
        self._bg_widget = BackgroundWidget()
        self._bg_widget.setObjectName("central_widget")
        self.setCentralWidget(self._bg_widget)

        root = QVBoxLayout(self._bg_widget)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(8)

        root.addLayout(self._build_header())
        root.addWidget(self._make_sep())
        root.addWidget(self._build_capture_zone())
        root.addWidget(self._make_sep())

        # Scrollable settings area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea, QScrollArea > QWidget { "
            "background: transparent; border: none; }"
        )

        sc_content = QWidget()
        sc_content.setObjectName("scroll_content")
        sc_layout = QVBoxLayout(sc_content)
        sc_layout.setContentsMargins(0, 0, 4, 0)
        sc_layout.setSpacing(6)

        sc_layout.addWidget(self._build_language_group())
        sc_layout.addWidget(self._build_backend_group())
        sc_layout.addWidget(self._build_appearance_group())
        sc_layout.addWidget(self._build_hotkey_group())
        sc_layout.addWidget(self._build_ocr_group())
        sc_layout.addStretch()

        scroll.setWidget(sc_content)
        scroll.setMinimumHeight(240)
        root.addWidget(scroll, 1)

        root.addWidget(self._build_log_group())
        root.addLayout(self._build_bottom_buttons())

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

    # ── HEADER ───────────────────────────────────

    def _build_header(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)

        title = QLabel("translatorTdev")
        title.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        title.setStyleSheet(
            "color: rgba(90,90,200,240); letter-spacing: 1px; background: transparent;"
        )

        self._status_dot = QLabel("●")
        self._status_dot.setStyleSheet(
            "color: #3a8a5a; font-size: 9px; background: transparent;"
        )

        self._status_text = QLabel("idle")
        self._status_text.setStyleSheet(
            "color: #404060; font-size: 10px; background: transparent;"
        )

        ver = QLabel("v1.0")
        ver.setStyleSheet(
            "color: rgba(35,35,60,200); font-size: 10px; background: transparent;"
        )

        row.addWidget(title)
        row.addSpacing(6)
        row.addWidget(self._status_dot)
        row.addWidget(self._status_text)
        row.addStretch()
        row.addWidget(ver)
        return row

    # ── CAPTURE ZONE ─────────────────────────────

    def _build_capture_zone(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(5)

        self._capture_btn = QPushButton("  ⊡  Capture Region")
        self._capture_btn.setObjectName("capture_btn")
        self._capture_btn.setToolTip("Start region selection (same as global hotkey)")
        self._capture_btn.clicked.connect(self._on_capture_clicked)

        hint_row = QHBoxLayout()
        self._hotkey_hint = QLabel("or press  <b>Q</b>  anywhere on screen")
        self._hotkey_hint.setStyleSheet(
            "color: rgba(55,55,90,200); font-size: 10px; background: transparent;"
        )
        self._hotkey_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_row.addStretch()
        hint_row.addWidget(self._hotkey_hint)
        hint_row.addStretch()

        layout.addWidget(self._capture_btn)
        layout.addLayout(hint_row)
        return w

    # ── LANGUAGE ─────────────────────────────────

    def _build_language_group(self) -> QGroupBox:
        g = QGroupBox("Languages")
        form = QFormLayout(g)
        form.setSpacing(6)
        form.setContentsMargins(10, 12, 10, 8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        LANGS = [
            ("English", "en"),
            ("Vietnamese", "vi"),
            ("Chinese (Simplified)", "zh"),
            ("Japanese", "ja"),
            ("Korean", "ko"),
            ("French", "fr"),
            ("German", "de"),
            ("Spanish", "es"),
            ("Russian", "ru"),
        ]

        self._source_lang = QComboBox()
        self._target_lang = QComboBox()
        for name, code in LANGS:
            self._source_lang.addItem(name, code)
            self._target_lang.addItem(name, code)

        self._source_lang.currentIndexChanged.connect(self._on_setting_changed)
        self._target_lang.currentIndexChanged.connect(self._on_setting_changed)

        row = QHBoxLayout()
        row.setSpacing(4)
        row.addWidget(self._source_lang)
        swap_btn = QPushButton("⇆")
        swap_btn.setFixedWidth(28)
        swap_btn.setFixedHeight(26)
        swap_btn.setToolTip("Swap languages")
        swap_btn.clicked.connect(self._swap_languages)
        row.addWidget(swap_btn)
        row.addWidget(self._target_lang)

        form.addRow("Source → Target:", row)
        return g

    # ── BACKEND ──────────────────────────────────

    def _build_backend_group(self) -> QGroupBox:
        """Translation backend settings with Local AI support."""
        g = QGroupBox("Translation")
        form = QFormLayout(g)
        form.setSpacing(6)
        form.setContentsMargins(10, 12, 10, 8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Backend selector + Setup button
        self._backend_combo = QComboBox()
        self._backend_combo.addItem("Google Translate  (free, online)", "google")
        self._backend_combo.addItem("OpenAI GPT  (paid API key)", "openai")
        self._backend_combo.addItem("Ollama  (free local AI)  ⭐", "ollama")
        self._backend_combo.addItem("LM Studio  (free local AI)", "lmstudio")
        self._backend_combo.addItem("llama.cpp server  (advanced)", "llamacpp")
        self._backend_combo.currentIndexChanged.connect(self._on_backend_changed)

        backend_row = QHBoxLayout()
        backend_row.setSpacing(4)
        backend_row.addWidget(self._backend_combo)

        self._local_ai_btn = QPushButton("⚙ Setup")
        self._local_ai_btn.setObjectName("setup_btn")
        self._local_ai_btn.setFixedWidth(64)
        self._local_ai_btn.setFixedHeight(26)
        self._local_ai_btn.setToolTip("Open Local AI setup guide")
        self._local_ai_btn.clicked.connect(self._open_local_ai_setup)
        backend_row.addWidget(self._local_ai_btn)
        form.addRow("Backend:", backend_row)

        # Translation style selector
        self._style_combo = QComboBox()
        self._style_combo.addItem("Novel / Web Novel", "novel")
        self._style_combo.addItem("Manga / Manhwa / Comic", "manga")
        self._style_combo.addItem("Subtitle / Movie", "subtitle")
        self._style_combo.addItem("General", "general")
        self._style_combo.currentIndexChanged.connect(self._on_setting_changed)
        form.addRow("Style:", self._style_combo)

        # Ollama quick model field
        self._ollama_model_edit = QLineEdit()
        self._ollama_model_edit.setPlaceholderText("e.g. qwen2.5:7b  (Ollama model)")
        self._ollama_model_edit.editingFinished.connect(self._on_setting_changed)
        form.addRow("Ollama Model:", self._ollama_model_edit)

        # OpenAI API key
        self._api_key_edit = QLineEdit()
        self._api_key_edit.setPlaceholderText("sk-...  (OpenAI API key)")
        self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_edit.editingFinished.connect(self._on_setting_changed)
        form.addRow("API Key:", self._api_key_edit)

        # OpenAI model selector
        self._model_combo = QComboBox()
        self._model_combo.addItem("gpt-4o-mini  (fast)", "gpt-4o-mini")
        self._model_combo.addItem("gpt-4o  (best)", "gpt-4o")
        self._model_combo.addItem("gpt-3.5-turbo  (legacy)", "gpt-3.5-turbo")
        self._model_combo.currentIndexChanged.connect(self._on_setting_changed)
        form.addRow("GPT Model:", self._model_combo)

        # Test connection row
        test_row = QHBoxLayout()
        test_row.setSpacing(6)
        self._test_btn = QPushButton("⚡ Test Backend")
        self._test_btn.setObjectName("test_btn")
        self._test_btn.setFixedHeight(24)
        self._test_btn.clicked.connect(self._test_backend)
        self._test_label = QLabel("")
        self._test_label.setStyleSheet(
            "font-size: 10px; color: #405060; background: transparent;"
        )
        self._test_label.setWordWrap(True)
        test_row.addWidget(self._test_btn)
        test_row.addWidget(self._test_label, 1)
        form.addRow("", test_row)

        # Cache + cleanup options
        self._cache_check = QCheckBox("Cache translations locally")
        self._cache_check.stateChanged.connect(self._on_setting_changed)
        form.addRow("", self._cache_check)

        self._ai_cleanup_check = QCheckBox("AI OCR cleanup  (needs OpenAI key)")
        self._ai_cleanup_check.stateChanged.connect(self._on_setting_changed)
        form.addRow("", self._ai_cleanup_check)

        return g

    # ── APPEARANCE ───────────────────────────────

    def _build_appearance_group(self) -> QGroupBox:
        g = QGroupBox("Overlay & Appearance")
        form = QFormLayout(g)
        form.setSpacing(6)
        form.setContentsMargins(10, 12, 10, 8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Font size
        self._font_size_spin = QSpinBox()
        self._font_size_spin.setRange(8, 40)
        self._font_size_spin.setSuffix(" pt")
        self._font_size_spin.valueChanged.connect(self._on_setting_changed)
        form.addRow("Font Size:", self._font_size_spin)

        # Overlay opacity
        op_row = QHBoxLayout()
        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(30, 100)
        self._opacity_label = QLabel("92%")
        self._opacity_label.setFixedWidth(34)
        self._opacity_label.setStyleSheet("background: transparent;")
        self._opacity_slider.valueChanged.connect(self._on_opacity_changed)
        op_row.addWidget(self._opacity_slider)
        op_row.addWidget(self._opacity_label)
        form.addRow("Overlay Opacity:", op_row)

        # Separator
        form.addRow("", self._make_thin_sep())

        # Custom background toggle
        self._use_bg_check = QCheckBox("Custom window background")
        self._use_bg_check.stateChanged.connect(self._on_bg_toggle)
        form.addRow("", self._use_bg_check)

        # File picker
        bg_row = QHBoxLayout()
        bg_row.setSpacing(4)
        self._bg_path_edit = QLineEdit()
        self._bg_path_edit.setPlaceholderText("path/to/image.png or .jpg")
        self._bg_path_edit.setReadOnly(True)
        self._bg_path_edit.setStyleSheet(
            "QLineEdit { color: rgba(80,80,120,200); font-size: 10px; }"
        )
        browse_btn = QPushButton("Browse")
        browse_btn.setFixedWidth(60)
        browse_btn.setFixedHeight(24)
        browse_btn.clicked.connect(self._browse_background)

        clear_btn = QPushButton("✕")
        clear_btn.setFixedWidth(24)
        clear_btn.setFixedHeight(24)
        clear_btn.setToolTip("Clear custom background")
        clear_btn.clicked.connect(self._clear_background)

        bg_row.addWidget(self._bg_path_edit)
        bg_row.addWidget(browse_btn)
        bg_row.addWidget(clear_btn)
        form.addRow("Image:", bg_row)

        # Background opacity
        bg_op_row = QHBoxLayout()
        self._bg_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._bg_opacity_slider.setRange(5, 80)
        self._bg_opacity_label = QLabel("35%")
        self._bg_opacity_label.setFixedWidth(34)
        self._bg_opacity_label.setStyleSheet("background: transparent;")
        self._bg_opacity_slider.valueChanged.connect(self._on_bg_opacity_changed)
        bg_op_row.addWidget(self._bg_opacity_slider)
        bg_op_row.addWidget(self._bg_opacity_label)
        form.addRow("BG Opacity:", bg_op_row)

        return g

    # ── HOTKEYS ──────────────────────────────────

    def _build_hotkey_group(self) -> QGroupBox:
        g = QGroupBox("Hotkeys")
        layout = QVBoxLayout(g)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 12, 10, 8)

        row = QHBoxLayout()
        row.addWidget(QLabel("Capture key:"))

        self._hotkey_display = QLabel("Q")
        self._hotkey_display.setObjectName("hotkey_display")
        self._hotkey_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hotkey_display.setFixedWidth(36)
        row.addWidget(self._hotkey_display)

        self._hotkey_edit = QLineEdit()
        self._hotkey_edit.setPlaceholderText("type new key")
        self._hotkey_edit.setMaxLength(10)
        self._hotkey_edit.setFixedWidth(90)
        self._hotkey_edit.editingFinished.connect(self._on_hotkey_changed)
        row.addWidget(self._hotkey_edit)
        row.addStretch()

        info = QLabel("ESC = cancel selection   ·   ENTER = confirm")
        info.setStyleSheet(
            "color: rgba(45,45,75,200); font-size: 10px; background: transparent;"
        )

        layout.addLayout(row)
        layout.addWidget(info)
        return g

    # ── OCR ──────────────────────────────────────

    def _build_ocr_group(self) -> QGroupBox:
        g = QGroupBox("OCR Settings")
        form = QFormLayout(g)
        form.setSpacing(6)
        form.setContentsMargins(10, 12, 10, 8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._ocr_lang_combo = QComboBox()
        self._ocr_lang_combo.addItem("English", "en")
        self._ocr_lang_combo.addItem("Vietnamese + English", "vi")
        self._ocr_lang_combo.addItem("Chinese (Simplified)", "ch")
        self._ocr_lang_combo.addItem("Japanese", "ja")
        self._ocr_lang_combo.addItem("Korean", "ko")
        self._ocr_lang_combo.addItem("French", "fr")
        self._ocr_lang_combo.addItem("German", "de")
        self._ocr_lang_combo.currentIndexChanged.connect(self._on_setting_changed)
        form.addRow("OCR Language:", self._ocr_lang_combo)
        return g

    # ── LOG PANEL ────────────────────────────────

    def _build_log_group(self) -> QGroupBox:
        g = QGroupBox("Log")
        layout = QVBoxLayout(g)
        layout.setContentsMargins(6, 10, 6, 6)
        layout.setSpacing(3)

        self._log_panel = LogPanel()
        layout.addWidget(self._log_panel)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        clear_btn = QPushButton("Clear log")
        clear_btn.setFixedHeight(18)
        clear_btn.setStyleSheet(
            "QPushButton { font-size: 9px; padding: 1px 8px; "
            "border-color: rgba(25,25,45,180); color: rgba(60,60,90,200); "
            "background: rgba(8,8,18,180); }"
            "QPushButton:hover { color: rgba(90,90,130,220); }"
        )
        clear_btn.clicked.connect(self._log_panel.clear)
        btn_row.addWidget(clear_btn)
        layout.addLayout(btn_row)
        return g

    # ── BOTTOM BUTTONS ───────────────────────────

    def _build_bottom_buttons(self) -> QHBoxLayout:
        row = QHBoxLayout()

        minimize_btn = QPushButton("Minimize to tray")
        minimize_btn.clicked.connect(self._minimize_to_tray)

        self._save_btn = QPushButton("Save Settings")
        self._save_btn.setObjectName("primary_btn")
        self._save_btn.clicked.connect(self._save_settings)

        row.addWidget(minimize_btn)
        row.addStretch()
        row.addWidget(self._save_btn)
        return row

    # ── HELPERS ──────────────────────────────────

    def _make_sep(self) -> QFrame:
        f = QFrame()
        f.setObjectName("sep")
        f.setFrameShape(QFrame.Shape.HLine)
        f.setFixedHeight(1)
        f.setStyleSheet("background-color: rgba(25,25,50,140); border: none;")
        return f

    def _make_thin_sep(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.Shape.HLine)
        f.setFixedHeight(1)
        f.setStyleSheet("background-color: rgba(30,30,60,100); border: none;")
        return f

    # ──────────────────────────────────────────────
    # TRAY
    # ──────────────────────────────────────────────

    def _setup_tray(self):
        self._tray = QSystemTrayIcon(self)
        icon = get_icon()
        if not icon.isNull():
            self._tray.setIcon(icon)
        self._tray.setToolTip("translatorTdev")

        menu = QMenu()
        capture_act = QAction("⊡  Capture Region", self)
        capture_act.triggered.connect(self._on_capture_clicked)
        show_act = QAction("Show Settings", self)
        show_act.triggered.connect(self._show_window)
        quit_act = QAction("Quit", self)
        quit_act.triggered.connect(QApplication.quit)

        menu.addAction(capture_act)
        menu.addSeparator()
        menu.addAction(show_act)
        menu.addSeparator()
        menu.addAction(quit_act)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    def _show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def _minimize_to_tray(self):
        self.hide()

    # ──────────────────────────────────────────────
    # STDOUT REDIRECT
    # ──────────────────────────────────────────────

    def _setup_stdout_redirect(self):
        try:
            self._redirector = SafeStdoutRedirector(self._log_panel)
            sys.stdout = self._redirector
        except Exception as e:
            print(f"[Window] Stdout redirect failed: {e}", file=sys.__stdout__)

    # ──────────────────────────────────────────────
    # EVENT HANDLERS
    # ──────────────────────────────────────────────

    def _on_capture_clicked(self):
        if not self._is_processing:
            self.capture_requested.emit()

    def _on_setting_changed(self):
        if not self._updating_ui:
            self._save_settings()

    def _on_opacity_changed(self, value: int):
        self._opacity_label.setText(f"{value}%")
        if not self._updating_ui:
            self._save_settings()

    def _on_bg_opacity_changed(self, value: int):
        self._bg_opacity_label.setText(f"{value}%")
        if not self._updating_ui:
            settings.set("background_opacity", value / 100.0)
            self._bg_widget.reload_background()

    def _on_backend_changed(self):
        backend = self._backend_combo.currentData()
        is_openai = backend == "openai"
        is_local = backend in ("ollama", "lmstudio", "llamacpp")

        self._model_combo.setEnabled(is_openai)
        self._api_key_edit.setEnabled(is_openai)
        self._ollama_model_edit.setEnabled(backend == "ollama")
        self._local_ai_btn.setVisible(is_local)

        if not self._updating_ui:
            self._save_settings()

    def _on_hotkey_changed(self):
        new_key = self._hotkey_edit.text().strip().lower()
        if new_key:
            self._hotkey_display.setText(new_key.upper())
            self._hotkey_hint.setText(
                f"or press  <b>{new_key.upper()}</b>  anywhere on screen"
            )
            settings.set("hotkey", new_key)
            self.hotkey_changed.emit(new_key)

    def _on_bg_toggle(self, state: int):
        enabled = state == Qt.CheckState.Checked.value
        settings.set("use_custom_background", enabled)
        self._bg_widget.reload_background()

    def _swap_languages(self):
        si = self._source_lang.currentIndex()
        ti = self._target_lang.currentIndex()
        self._updating_ui = True
        self._source_lang.setCurrentIndex(ti)
        self._target_lang.setCurrentIndex(si)
        self._updating_ui = False
        self._save_settings()

    def _browse_background(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Background Image",
            str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.bmp *.webp);;All Files (*)",
        )
        if path:
            self._bg_path_edit.setText(path)
            settings.set("custom_background", path)
            settings.set("use_custom_background", True)
            self._use_bg_check.setChecked(True)
            self._bg_widget.reload_background()
            self.log(f"Background: {os.path.basename(path)}", "ok")

    def _clear_background(self):
        self._bg_path_edit.clear()
        settings.set("custom_background", "")
        settings.set("use_custom_background", False)
        self._use_bg_check.setChecked(False)
        self._bg_widget.reload_background()
        self.log("Background cleared.", "info")

    # ──────────────────────────────────────────────
    # LOCAL AI ACTIONS
    # ──────────────────────────────────────────────

    def _open_local_ai_setup(self):
        """Open the Local AI setup guide dialog."""
        from ui.local_ai_dialog import LocalAIDialog

        dlg = LocalAIDialog(self)
        dlg.backend_configured.connect(self._on_backend_configured)
        dlg.exec()

    def _on_backend_configured(self, backend_name: str):
        """Called when Local AI dialog selects a backend."""
        self._updating_ui = True
        self._set_combo_by_data(self._backend_combo, backend_name)
        self._updating_ui = False
        self._save_settings()
        self._test_label.setText(f"✓ Switched to {backend_name}")
        self._test_label.setStyleSheet(
            "font-size: 10px; color: #40a060; background: transparent;"
        )
        self.log(f"Backend: {backend_name}", "ok")

    def _test_backend(self):
        """Test current translation backend — fully async, non-blocking."""
        self._test_label.setText("Testing...")
        self._test_label.setStyleSheet(
            "font-size: 10px; color: #4060a0; background: transparent;"
        )
        self._test_btn.setEnabled(False)
        self._save_settings()

        from translator import reset_translator, get_translator

        reset_translator()

        def _run():
            ok = False
            msg = "Unknown error"
            try:
                t = get_translator()
                ok, msg = t.test_backend()
            except Exception as e:
                ok = False
                msg = str(e)
            finally:
                self._test_result_signal.emit(ok, msg)

        threading.Thread(target=_run, daemon=True, name="BackendTest").start()

    def _update_test_label(self, ok: bool, msg: str):
        """Receive test result on UI thread via signal."""
        self._test_btn.setEnabled(True)

        short = (msg[:55] + "…") if len(msg) > 55 else msg

        if ok:
            self._test_label.setText(f"✓  {short}")
            self._test_label.setStyleSheet(
                "font-size: 10px; color: #40a060; background: transparent;"
            )
            self.log(f"Backend OK: {msg}", "ok")
        else:
            self._test_label.setText(f"✗  {short}")
            self._test_label.setStyleSheet(
                "font-size: 10px; color: #a04040; background: transparent;"
            )
            self.log(f"Backend failed: {msg}", "error")

    # ──────────────────────────────────────────────
    # SETTINGS LOAD / SAVE
    # ──────────────────────────────────────────────

    def _set_combo_by_data(self, combo: QComboBox, value: str):
        for i in range(combo.count()):
            if combo.itemData(i) == value:
                combo.setCurrentIndex(i)
                return

    def _load_current_settings(self):
        self._updating_ui = True
        try:
            self._set_combo_by_data(
                self._source_lang, settings.get("source_language", "en")
            )
            self._set_combo_by_data(
                self._target_lang, settings.get("target_language", "vi")
            )
            self._set_combo_by_data(
                self._backend_combo, settings.get("translation_backend", "google")
            )
            self._set_combo_by_data(
                self._style_combo, settings.get("translation_style", "novel")
            )
            self._ollama_model_edit.setText(settings.get("ollama_model", "qwen2.5:7b"))
            self._api_key_edit.setText(settings.get("openai_api_key", ""))
            self._set_combo_by_data(
                self._model_combo, settings.get("openai_model", "gpt-4o-mini")
            )
            self._font_size_spin.setValue(settings.get("font_size", 16))
            pct = int(settings.get("overlay_opacity", 0.92) * 100)
            self._opacity_slider.setValue(pct)
            self._opacity_label.setText(f"{pct}%")

            hk = settings.get("hotkey", "q")
            self._hotkey_display.setText(hk.upper())
            self._hotkey_edit.setText(hk.upper())
            self._hotkey_hint.setText(
                f"or press  <b>{hk.upper()}</b>  anywhere on screen"
            )

            self._ai_cleanup_check.setChecked(settings.get("cleanup_with_ai", False))
            self._cache_check.setChecked(settings.get("cache_translations", True))
            self._set_combo_by_data(
                self._ocr_lang_combo, settings.get("ocr_language", "en")
            )

            self._use_bg_check.setChecked(settings.get("use_custom_background", False))
            custom_path = settings.get("custom_background", "")
            if custom_path:
                self._bg_path_edit.setText(custom_path)
            bg_op = int(settings.get("background_opacity", 0.35) * 100)
            self._bg_opacity_slider.setValue(bg_op)
            self._bg_opacity_label.setText(f"{bg_op}%")

            self._on_backend_changed()

        finally:
            self._updating_ui = False

    def _save_settings(self):
        if self._updating_ui:
            return

        settings.update(
            {
                "source_language": self._source_lang.currentData(),
                "target_language": self._target_lang.currentData(),
                "translation_backend": self._backend_combo.currentData(),
                "translation_style": self._style_combo.currentData(),
                "ollama_model": self._ollama_model_edit.text().strip() or "qwen2.5:7b",
                "openai_api_key": self._api_key_edit.text().strip(),
                "openai_model": self._model_combo.currentData(),
                "font_size": self._font_size_spin.value(),
                "overlay_opacity": self._opacity_slider.value() / 100.0,
                "hotkey": self._hotkey_edit.text().strip().lower() or "q",
                "cleanup_with_ai": self._ai_cleanup_check.isChecked(),
                "cache_translations": self._cache_check.isChecked(),
                "ocr_language": self._ocr_lang_combo.currentData(),
                "background_opacity": self._bg_opacity_slider.value() / 100.0,
                "use_custom_background": self._use_bg_check.isChecked(),
                "custom_background": self._bg_path_edit.text().strip(),
            }
        )
        self.settings_changed.emit()
        self._status_bar.showMessage("Saved.", 1500)

    # ──────────────────────────────────────────────
    # PUBLIC API  (called by AppController)
    # ──────────────────────────────────────────────

    def set_status(self, message: str, level: str = "ok"):
        """Update status dot + text + log."""
        colors = {
            "ok": ("#3a8a5a", "#40706a"),
            "warn": ("#8a7a30", "#706040"),
            "error": ("#8a3a3a", "#704040"),
            "processing": ("#3a5aaa", "#405090"),
            "idle": ("#303050", "#303050"),
        }
        c_dot, c_txt = colors.get(level, ("#404060", "#404060"))
        self._status_dot.setStyleSheet(
            f"color: {c_dot}; font-size: 9px; background: transparent;"
        )
        self._status_text.setStyleSheet(
            f"color: {c_txt}; font-size: 10px; background: transparent;"
        )
        self._status_text.setText(message)
        self._status_bar.showMessage(message)

        log_level = level if level in ("ok", "warn", "error") else "info"
        try:
            self._log_panel.append_log(message, log_level)
        except Exception:
            pass

    def set_processing(self, active: bool):
        """Toggle processing state."""
        self._is_processing = active
        self._capture_btn.setEnabled(not active)

        if active:
            self._capture_btn.setText("  ⏳  Processing...")
            self.set_status("Processing...", "processing")
        else:
            self._capture_btn.setText("  ⊡  Capture Region")
            hk = settings.get("hotkey", "q").upper()
            self.set_status(f"Ready  —  {hk} or click Capture", "ok")

    def log(self, message: str, level: str = "info"):
        """Write to log panel without changing status."""
        try:
            self._log_panel.append_log(message, level)
        except Exception:
            pass

    def closeEvent(self, event):
        """Hide to tray on close."""
        event.ignore()
        self.hide()

    def __del__(self):
        try:
            sys.stdout = sys.__stdout__
        except Exception:
            pass
