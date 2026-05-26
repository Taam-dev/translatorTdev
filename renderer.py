"""
renderer.py
-----------
Async pipeline: Capture → OCR → Reconstruct → Translate

CRITICAL RULE: Không được gọi print() hay bất kỳ GUI method nào
               từ _worker() vì nó chạy trong background thread!
               Chỉ communicate qua Qt signals.
"""

import sys
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
    Background worker — full translation pipeline.
    Communicates với UI ONLY qua Qt signals (thread-safe).
    """

    started = Signal()
    ocr_done = Signal(list)
    text_ready = Signal(list)
    translation_done = Signal(list)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: Optional[threading.Thread] = None
        self._cancelled = False
        self._lock = threading.Lock()

    def run_pipeline(self, x: int, y: int, width: int, height: int):
        """Start pipeline trong background thread."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                # Pipeline cũ còn chạy → bỏ qua, tránh double-run
                return

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
        BACKGROUND THREAD.
        - KHÔNG gọi print() (stdout bị redirect vào GUI → CRASH)
        - KHÔNG access bất kỳ Qt widget nào
        - Chỉ dùng emit() để communicate
        - Dùng sys.__stderr__ nếu cần debug log
        """
        self.started.emit()

        try:
            # ── Step 1: Capture ───────────────────────────────────
            if self._check_cancelled():
                return

            t0 = time.time()
            try:
                image = capture_region(x, y, width, height)
            except Exception as e:
                self.error_occurred.emit(f"Capture failed: {e}")
                return

            print(
                f"[Pipeline] Capture done in {time.time()-t0:.2f}s", file=sys.__stderr__
            )

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

            print(
                f"[Pipeline] OCR done in {time.time()-t1:.2f}s "
                f"— {len(ocr_results)} boxes",
                file=sys.__stderr__,
            )

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

            print(
                f"[Pipeline] Reconstruction done in {time.time()-t2:.2f}s "
                f"— {len(paragraphs)} paragraphs",
                file=sys.__stderr__,
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

            print(
                f"[Pipeline] Translation done in {time.time()-t3:.2f}s",
                file=sys.__stderr__,
            )

            if not translated:
                self.error_occurred.emit("Translation produced no output.")
                return

            if not self._check_cancelled():
                self.translation_done.emit(translated)

        except Exception as e:
            import traceback

            tb = traceback.format_exc()
            print(f"[Pipeline] Unhandled error:\n{tb}", file=sys.__stderr__)
            if not self._cancelled:
                self.error_occurred.emit(f"Unexpected error: {e}")

        finally:
            self.finished.emit()
