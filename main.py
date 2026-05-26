"""
main.py
-------
Application entry point for translatorTdev.
Compatible với cả .py script và PyInstaller --windowed exe.
"""

import faulthandler

faulthandler.enable()
import sys
import os

# ==================================================
# PHẢI FIX STDIO TRƯỚC KHI IMPORT BẤT CỨ THỨ GÌ
# Khi PyInstaller --windowed: sys.stdout/stderr = None
# faulthandler.enable() crash ngay nếu sys.stderr is None
# ==================================================


def _fix_stdio():
    """Fix stdout/stderr=None khi chạy windowed exe."""
    try:
        if sys.stderr is None:
            sys.stderr = open(os.devnull, "w", encoding="utf-8", errors="replace")
        if sys.stdout is None:
            sys.stdout = open(os.devnull, "w", encoding="utf-8", errors="replace")
        if sys.__stderr__ is None:
            sys.__stderr__ = sys.stderr
        if sys.__stdout__ is None:
            sys.__stdout__ = sys.stdout
    except Exception:
        pass


_fix_stdio()

# Bây giờ mới safe để dùng faulthandler
try:
    import faulthandler

    faulthandler.enable()
except Exception:
    pass

# ==================================================
# LOG FILE - chỉ khi chạy windowed exe
# Ghi log ra file để debug khi không có console
# ==================================================

_log_file = None


def _setup_log_file():
    """Tạo log file bên cạnh exe để debug."""
    global _log_file
    try:
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        log_path = os.path.join(base_dir, "translatorTdev.log")

        import datetime

        _log_file = open(log_path, "a", encoding="utf-8", errors="replace", buffering=1)
        _log_file.write(f"\n{'='*60}\n")
        _log_file.write(f"Started: {datetime.datetime.now()}\n")
        _log_file.write(f"Python:  {sys.version}\n")
        _log_file.write(f"Frozen:  {getattr(sys, 'frozen', False)}\n")
        _log_file.write(f"Exe:     {sys.executable}\n")
        _log_file.write(f"{'='*60}\n\n")
        _log_file.flush()

        # Redirect stdout/stderr về log file khi là frozen exe
        sys.stdout = _log_file
        sys.stderr = _log_file
    except Exception as e:
        # Không crash nếu không tạo được log file
        pass


# Chỉ setup log file khi chạy từ exe
if getattr(sys, "frozen", False):
    _setup_log_file()

# ==================================================
# PATH SETUP
# ==================================================

# Thêm thư mục gốc vào sys.path
if getattr(sys, "frozen", False):
    # Khi frozen: _MEIPASS là thư mục temp chứa files
    _base = sys._MEIPASS
    _exe_dir = os.path.dirname(sys.executable)
    # Ưu tiên thư mục exe (chứa settings.json, cache, assets thật)
    sys.path.insert(0, _exe_dir)
    sys.path.insert(0, _base)
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ==================================================
# MAIN IMPORTS
# ==================================================

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QRect, Signal, QObject

from settings import settings
from hotkeys import get_hotkey_manager
from ui.main_window import MainWindow
from ui.selection_window import SelectionWindow, take_qt_screenshot
from overlay import TranslationOverlay
from renderer import TranslationWorker

# ==================================================
# GLOBAL EXCEPTION HANDLER
# ==================================================


def _install_exception_handler(app: QApplication):
    """Hiện dialog thay vì crash âm thầm."""
    import traceback

    def handle_exception(exc_type, exc_value, exc_tb):
        # Ghi vào log
        try:
            tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            _safe_print(f"UNHANDLED EXCEPTION:\n{tb_str}")
        except Exception:
            pass

        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return

        try:
            tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            short = f"{exc_type.__name__}: {exc_value}"
        except Exception:
            tb_str = "Could not format traceback"
            short = "Unknown error"

        try:
            msg = QMessageBox()
            msg.setWindowTitle("translatorTdev — Error")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText(f"An error occurred:\n\n{short}")
            msg.setDetailedText(tb_str)
            msg.setStandardButtons(
                QMessageBox.StandardButton.Ignore | QMessageBox.StandardButton.Close
            )
            if msg.exec() == QMessageBox.StandardButton.Close:
                sys.exit(1)
        except Exception:
            sys.exit(1)

    sys.excepthook = handle_exception


# ==================================================
# UTILITY
# ==================================================


def _safe_print(msg: str):
    """Print không crash dù stdout/stderr là None."""
    for stream in (sys.stderr, sys.__stderr__, sys.stdout, sys.__stdout__):
        try:
            if stream is not None:
                print(msg, file=stream, flush=True)
                return
        except Exception:
            pass


# ==================================================
# APP CONTROLLER
# ==================================================


class AppController(QObject):
    """
    Orchestrates: Hotkey → Selection → OCR → Translate → Overlay
    """

    _trigger_signal = Signal()
    _error_signal = Signal(str)

    def __init__(self, app: QApplication):
        super().__init__()
        self._app = app
        self._main_window = None
        self._selection_window = None
        self._overlay = None
        self._worker = None
        self._busy = False
        self._capture_region = QRect()
        self._setup()

    def _setup(self):
        # Main window
        self._main_window = MainWindow()
        self._main_window.settings_changed.connect(self._on_settings_changed)
        self._main_window.hotkey_changed.connect(self._on_hotkey_changed)
        self._main_window.capture_requested.connect(self._start_selection)

        # Overlay
        self._overlay = TranslationOverlay()
        self._overlay.closed.connect(self._on_overlay_closed)

        # Worker
        self._worker = TranslationWorker()
        self._worker.started.connect(self._on_pipeline_started)
        self._worker.ocr_done.connect(self._on_ocr_done)
        self._worker.text_ready.connect(self._on_text_ready)
        self._worker.translation_done.connect(self._on_translation_done)
        self._worker.error_occurred.connect(self._on_pipeline_error)
        self._worker.finished.connect(self._on_pipeline_finished)

        # Thread-safe signals
        self._trigger_signal.connect(
            self._start_selection, Qt.ConnectionType.QueuedConnection
        )
        self._error_signal.connect(self._show_error, Qt.ConnectionType.QueuedConnection)

        self._setup_hotkey()
        self._main_window.show()

        hotkey = settings.get("hotkey", "q").upper()
        self._main_window.set_processing(False)
        self._main_window.log(f"translatorTdev ready. Hotkey: {hotkey}", "ok")

    def _setup_hotkey(self):
        mgr = get_hotkey_manager()
        hk = settings.get("hotkey", "q")
        mgr.set_hotkey(hk, self._on_hotkey_pressed)
        mgr.start()

    # ── Hotkey ────────────────────────────────────

    def _on_hotkey_pressed(self):
        if not self._busy:
            self._trigger_signal.emit()

    # ── Selection ─────────────────────────────────

    def _start_selection(self):
        if self._busy:
            self._main_window.log("Already processing, please wait.", "warn")
            return

        self._cleanup_selection_window()
        self._main_window.log("Starting region selection...", "info")

        try:
            pixmap = take_qt_screenshot()
        except Exception as e:
            self._show_error(f"Screenshot failed: {e}")
            return

        self._selection_window = SelectionWindow(pixmap)
        self._selection_window.region_selected.connect(self._on_region_selected)
        self._selection_window.selection_cancelled.connect(self._on_selection_cancelled)
        self._selection_window.showFullScreen()
        self._selection_window.setFocus()

    def _cleanup_selection_window(self):
        if self._selection_window is not None:
            try:
                try:
                    self._selection_window.region_selected.disconnect()
                    self._selection_window.selection_cancelled.disconnect()
                except RuntimeError:
                    pass
                self._selection_window.close()
                self._selection_window.deleteLater()
            except Exception as e:
                _safe_print(f"[Main] SelectionWindow cleanup: {e}")
            finally:
                self._selection_window = None

    def _on_region_selected(self, x: int, y: int, w: int, h: int):
        if w <= 0 or h <= 0:
            self._main_window.log(f"Invalid region: {w}×{h}px — try again", "warn")
            return

        self._main_window.log(f"Region: ({x},{y})  {w}×{h}px", "info")
        self._cleanup_selection_window()
        self._overlay.hide()
        self._capture_region = QRect(x, y, w, h)
        self._busy = True
        self._main_window.set_processing(True)
        self._worker.run_pipeline(x, y, w, h)

    def _on_selection_cancelled(self):
        self._cleanup_selection_window()
        self._main_window.log("Selection cancelled.", "warn")
        self._main_window.set_status("Cancelled", "warn")

    # ── Pipeline callbacks ─────────────────────────

    def _on_pipeline_started(self):
        self._main_window.set_status("Capturing & running OCR...", "processing")

    def _on_ocr_done(self, results: list):
        n = len(results)
        self._main_window.log(f"OCR: {n} box(es) found", "ocr" if n > 0 else "warn")

    def _on_text_ready(self, paragraphs: list):
        self._main_window.log(f"Reconstructed {len(paragraphs)} paragraph(s)", "ocr")
        for i, p in enumerate(paragraphs, 1):
            preview = (p[:80] + "...") if len(p) > 80 else p
            self._main_window.log(f"  [{i}] {preview}", "debug")
        self._main_window.set_status("Translating...", "processing")

    def _on_translation_done(self, translated: list):
        if not translated:
            self._show_error("Translation produced no output.")
            return

        self._main_window.log(
            f"Translation done — {len(translated)} paragraph(s)", "trans"
        )
        for i, p in enumerate(translated, 1):
            preview = (p[:80] + "...") if len(p) > 80 else p
            self._main_window.log(f"  [{i}] {preview}", "trans")

        self._overlay.show_translation(
            region=self._capture_region,
            paragraphs=translated,
        )
        self._main_window.set_status("Done — click overlay to dismiss", "ok")

    def _on_pipeline_finished(self):
        """Luôn được gọi khi pipeline kết thúc (dù success hay error)."""
        self._busy = False
        self._main_window.set_processing(False)

    def _on_pipeline_error(self, error: str):
        """Được emit từ background thread → dùng error_signal."""
        self._error_signal.emit(error)

    def _show_error(self, msg: str):
        self._main_window.log(f"ERROR: {msg}", "error")
        self._main_window.set_status(f"Error: {msg[:80]}", "error")
        self._busy = False
        self._main_window.set_processing(False)

    # ── Settings ──────────────────────────────────

    def _on_settings_changed(self):
        self._overlay.update_settings()

    def _on_hotkey_changed(self, new_key: str):
        mgr = get_hotkey_manager()
        mgr.stop()
        mgr.set_hotkey(new_key, self._on_hotkey_pressed)
        mgr.start()
        self._main_window.log(f"Hotkey → {new_key.upper()}", "ok")

    def _on_overlay_closed(self):
        hk = settings.get("hotkey", "q").upper()
        self._main_window.set_status(f"Ready  —  press {hk} or click Capture", "ok")

    def quit(self):
        """Graceful shutdown."""
        _safe_print("[Main] Shutting down...")
        try:
            get_hotkey_manager().stop()
        except Exception:
            pass
        try:
            if self._worker:
                self._worker.cancel()
        except Exception:
            pass
        try:
            self._cleanup_selection_window()
        except Exception:
            pass
        try:
            if self._main_window:
                self._main_window._restore_stdout()
        except Exception:
            pass
        try:
            if _log_file:
                _log_file.flush()
                _log_file.close()
        except Exception:
            pass
        self._app.quit()


# ==================================================
# ENTRY POINT
# ==================================================


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("translatorTdev")
    app.setApplicationVersion("1.0.0")
    app.setQuitOnLastWindowClosed(False)

    _install_exception_handler(app)

    controller = AppController(app)
    app.aboutToQuit.connect(controller.quit)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
