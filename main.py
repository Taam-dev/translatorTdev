"""
main.py
-------
Application entry point for translatorTdev.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QRect, Signal, QObject

from settings import settings
from hotkeys import get_hotkey_manager
from ui.main_window import MainWindow
from ui.selection_window import SelectionWindow, take_qt_screenshot
from overlay import TranslationOverlay
from renderer import TranslationWorker


class AppController(QObject):
    """
    Main application controller.
    Manages the full capture → OCR → translate → overlay workflow.
    """

    _trigger_signal = Signal()
    _error_signal = Signal(str)

    def __init__(self, app: QApplication):
        super().__init__()
        self._app = app
        self._main_window: MainWindow = None
        self._selection_window: SelectionWindow = None
        self._overlay: TranslationOverlay = None
        self._worker: TranslationWorker = None
        self._busy = False
        self._capture_region: QRect = QRect()

        self._setup()

    def _setup(self):
        """Initialize all components and wire signals."""
        # Main window
        self._main_window = MainWindow()
        self._main_window.settings_changed.connect(self._on_settings_changed)
        self._main_window.hotkey_changed.connect(self._on_hotkey_changed)
        self._main_window.capture_requested.connect(self._start_selection)

        # Overlay
        self._overlay = TranslationOverlay()
        self._overlay.closed.connect(self._on_overlay_closed)

        # Pipeline worker
        self._worker = TranslationWorker()
        self._worker.started.connect(self._on_pipeline_started)
        self._worker.ocr_done.connect(self._on_ocr_done)
        self._worker.text_ready.connect(self._on_text_ready)
        self._worker.translation_done.connect(self._on_translation_done)
        self._worker.error_occurred.connect(self._on_pipeline_error)
        self._worker.finished.connect(self._on_pipeline_finished)

        # Thread-safe signals for hotkey callback
        self._trigger_signal.connect(
            self._start_selection,
            Qt.ConnectionType.QueuedConnection
        )
        self._error_signal.connect(
            self._show_error,
            Qt.ConnectionType.QueuedConnection
        )

        # Global hotkey
        self._setup_hotkey()

        # Show window
        self._main_window.show()

        hotkey = settings.get("hotkey", "q").upper()
        self._main_window.set_processing(False)
        self._main_window.log(
            f"translatorTdev ready. Hotkey: {hotkey}", "ok"
        )

    def _setup_hotkey(self):
        mgr = get_hotkey_manager()
        hotkey = settings.get("hotkey", "q")
        mgr.set_hotkey(hotkey, self._on_hotkey_pressed)
        mgr.start()

    # ==================================================
    # HOTKEY
    # ==================================================

    def _on_hotkey_pressed(self):
        """Called from pynput thread - must use signal."""
        if self._busy:
            return
        self._trigger_signal.emit()

    # ==================================================
    # SELECTION
    # ==================================================

    def _start_selection(self):
        """Show fullscreen selection overlay."""
        if self._busy:
            self._main_window.log("Already processing, please wait.", "warn")
            return

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

    def _on_region_selected(self, x: int, y: int, w: int, h: int):
        """User confirmed selection region."""
        self._main_window.log(
            f"Region selected: ({x},{y})  {w}×{h}px", "info"
        )
        self._overlay.hide()
        self._capture_region = QRect(x, y, w, h)
        self._busy = True
        self._main_window.set_processing(True)
        self._worker.run_pipeline(x, y, w, h)

    def _on_selection_cancelled(self):
        """User pressed Escape."""
        self._main_window.log("Selection cancelled.", "warn")
        self._main_window.set_status("Cancelled", "warn")

    # ==================================================
    # PIPELINE CALLBACKS
    # ==================================================

    def _on_pipeline_started(self):
        self._main_window.set_status("Capturing & running OCR...", "processing")

    def _on_ocr_done(self, results: list):
        count = len(results)
        self._main_window.log(
            f"OCR complete — {count} text block(s) found", "ocr"
        )
        if count == 0:
            self._main_window.log("No text detected in region.", "warn")

    def _on_text_ready(self, paragraphs: list):
        self._main_window.log(
            f"Text reconstructed — {len(paragraphs)} paragraph(s)", "ocr"
        )
        for i, p in enumerate(paragraphs, 1):
            preview = p[:80] + "..." if len(p) > 80 else p
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
            preview = p[:80] + "..." if len(p) > 80 else p
            self._main_window.log(f"  [{i}] {preview}", "trans")

        self._overlay.show_translation(
            region=self._capture_region,
            paragraphs=translated,
        )
        self._main_window.set_status("Translation shown — click overlay to dismiss", "ok")

    def _on_pipeline_finished(self):
        self._busy = False
        self._main_window.set_processing(False)

    def _on_pipeline_error(self, error: str):
        self._error_signal.emit(error)

    def _show_error(self, msg: str):
        self._main_window.log(f"ERROR: {msg}", "error")
        self._main_window.set_status(f"Error: {msg}", "error")
        self._busy = False
        self._main_window.set_processing(False)

    # ==================================================
    # SETTINGS
    # ==================================================

    def _on_settings_changed(self):
        self._overlay.update_settings()

    def _on_hotkey_changed(self, new_key: str):
        mgr = get_hotkey_manager()
        mgr.stop()
        mgr.set_hotkey(new_key, self._on_hotkey_pressed)
        mgr.start()
        self._main_window.log(f"Hotkey changed to: {new_key.upper()}", "ok")

    def _on_overlay_closed(self):
        hotkey = settings.get("hotkey", "q").upper()
        self._main_window.set_status(
            f"Ready  —  press {hotkey} or click Capture", "ok"
        )

    def quit(self):
        get_hotkey_manager().stop()
        if self._worker:
            self._worker.cancel()
        self._app.quit()


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("translatorTdev")
    app.setQuitOnLastWindowClosed(False)

    controller = AppController(app)
    app.aboutToQuit.connect(controller.quit)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()