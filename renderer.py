"""
renderer.py
-----------
Async pipeline: Capture → OCR → Reconstruct → Translate
FIXED: Removed all print() calls from background thread
       to prevent GUI access violation crash.
"""

import threading
import time
from typing import Optional

from PySide6.QtCore import QObject, Signal
from capture import capture_region
from ocr import run_ocr
from cleanup import reconstruct_ocr_text
from translator import get_translator
from settings import settings

import logging

log = logging.getLogger("pipeline")


class TranslationWorker(QObject):
    """
    Background worker - full translation pipeline.
    Communicates với UI ONLY qua Qt signals (thread-safe).

    CRITICAL: Không được gọi print() hay bất kỳ GUI method nào
              từ _worker() vì nó chạy trong background thread!
    """

    started = Signal()
    ocr_done = Signal(list)
    text_ready = Signal(list)
    translation_done = Signal(list)
    error_occurred = Signal(str)
    finished = Signal()

    # Signal để log AN TOÀN từ background thread về main thread
    _log_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: Optional[threading.Thread] = None
        self._cancelled = False
        self._lock = threading.Lock()

        # Log signal → chỉ in ra console (KHÔNG gọi GUI)
        # Dùng QueuedConnection để về main thread trước
        self._log_signal.connect(
            self._safe_log,
            # QueuedConnection đảm bảo chạy trên main thread
        )

    def _safe_log(self, msg: str):
        """Chỉ được gọi từ main thread qua signal."""
        # Dùng logging module thay vì print để tránh stdout redirect
        log.debug(msg)

    def _thread_log(self, msg: str):
        """
        Log AN TOÀN từ background thread.
        KHÔNG dùng print() trực tiếp!
        """
        # Emit signal → sẽ được xử lý trên main thread
        self._log_signal.emit(msg)

    def run_pipeline(self, x: int, y: int, width: int, height: int):
        """Start pipeline trong background thread."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return  # Pipeline cũ còn chạy, bỏ qua

            self._cancelled = False
            self._thread = threading.Thread(
                target=self._worker,
                args=(x, y, width, height),
                daemon=True,
                name="OCRTranslatePipeline",
            )
            self._thread.start()

    def cancel(self):
        self._cancelled = True

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _check_cancelled(self) -> bool:
        return self._cancelled

    def _worker(self, x: int, y: int, width: int, height: int):
        """
        BACKGROUND THREAD - CRITICAL RULES:
        1. KHÔNG gọi print() ← stdout bị redirect vào GUI → CRASH
        2. KHÔNG access bất kỳ Qt widget nào trực tiếp
        3. Chỉ communicate qua emit() signals
        4. Dùng _thread_log() thay vì print()
        """
        self.started.emit()

        try:
            # ── Step 1: Capture ──────────────────────────────────
            if self._check_cancelled():
                return

            t0 = time.time()
            try:
                image = capture_region(x, y, width, height)
            except Exception as e:
                self.error_occurred.emit(f"Capture failed: {e}")
                return

            elapsed = time.time() - t0
            self._thread_log(f"Capture done in {elapsed:.2f}s")

            # ── Step 2: OCR ───────────────────────────────────────
            if self._check_cancelled():
                return

            t1 = time.time()
            try:
                lang = settings.get("ocr_language", "en")
                ocr_results = run_ocr(image, lang)
            except Exception as e:
                self.error_occurred.emit(f"OCR failed: {e}")
                return

            elapsed = time.time() - t1
            self._thread_log(f"OCR done in {elapsed:.2f}s — {len(ocr_results)} boxes")
            self.ocr_done.emit(ocr_results)

            if not ocr_results:
                self.error_occurred.emit(
                    "No text detected in selected region.\n"
                    "Tips: chọn vùng có chữ rõ ràng, đúng ngôn ngữ OCR."
                )
                return

            # ── Step 3: Reconstruct ───────────────────────────────
            if self._check_cancelled():
                return

            t2 = time.time()
            try:
                paragraphs = reconstruct_ocr_text(ocr_results)
                paragraphs = [p.strip() for p in paragraphs if p and p.strip()]
            except Exception as e:
                self.error_occurred.emit(f"Reconstruction failed: {e}")
                return

            elapsed = time.time() - t2
            self._thread_log(
                f"Reconstruction done in {elapsed:.2f}s — {len(paragraphs)} paragraphs"
            )
            self.text_ready.emit(paragraphs)

            if not paragraphs:
                self.error_occurred.emit("Could not reconstruct any text.")
                return

            # ── Step 4: Translate ─────────────────────────────────
            if self._check_cancelled():
                return

            t3 = time.time()
            try:
                translator = get_translator()
                translated = translator.translate_paragraphs(paragraphs)
                translated = [p.strip() for p in translated if p and p.strip()]
            except Exception as e:
                self.error_occurred.emit(f"Translation failed: {e}")
                return

            elapsed = time.time() - t3
            self._thread_log(f"Translation done in {elapsed:.2f}s")

            if not translated:
                self.error_occurred.emit("Translation produced no output.")
                return

            if not self._check_cancelled():
                self.translation_done.emit(translated)

        except Exception as e:
            import traceback

            tb = traceback.format_exc()
            # Ghi vào stderr (không bị redirect) thay vì print
            import sys

            print(tb, file=sys.__stderr__)
            if not self._cancelled:
                self.error_occurred.emit(f"Unexpected error: {e}")

        finally:
            self.finished.emit()
