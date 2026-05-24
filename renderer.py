"""
renderer.py
-----------
Async pipeline: Capture → OCR → Reconstruct → Translate
"""

import threading
import time
from typing import Optional

from PySide6.QtCore import QObject, Signal, QRect
from capture import capture_region
from ocr import run_ocr          # ← use new unified entry point
from cleanup import reconstruct_ocr_text
from translator import get_translator
from settings import settings


class TranslationWorker(QObject):
    """
    Background worker running the full translation pipeline.
    Communicates with UI via Qt signals (thread-safe).
    """

    started          = Signal()
    ocr_done         = Signal(list)   # raw OCR results
    text_ready       = Signal(list)   # reconstructed paragraphs
    translation_done = Signal(list)   # translated paragraphs
    error_occurred   = Signal(str)
    finished         = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: Optional[threading.Thread] = None
        self._cancelled = False

    def run_pipeline(self, x: int, y: int, width: int, height: int):
        """Start pipeline in background thread."""
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

    def _worker(self, x: int, y: int, width: int, height: int):
        self.started.emit()

        try:
            # ── Step 1: Capture ──────────────────────────────────
            if self._cancelled:
                return
            print(f"[Pipeline] Capturing region: ({x},{y}) {width}×{height}")
            t0 = time.time()
            image = capture_region(x, y, width, height)
            print(f"[Pipeline] Capture done in {time.time()-t0:.2f}s")

            # ── Step 2: OCR ───────────────────────────────────────
            if self._cancelled:
                return
            print("[Pipeline] Running OCR...")
            t1 = time.time()
            lang = settings.get("ocr_language", "en")
            ocr_results = run_ocr(image, lang)
            print(f"[Pipeline] OCR done in {time.time()-t1:.2f}s. "
                  f"Found {len(ocr_results)} text boxes.")
            self.ocr_done.emit(ocr_results)

            if not ocr_results:
                self.error_occurred.emit(
                    "No text detected in selected region.\n"
                    "Tips: select a region with clear readable text, "
                    "make sure the OCR language matches the text."
                )
                return

            # ── Step 3: Reconstruct ───────────────────────────────
            if self._cancelled:
                return
            print("[Pipeline] Reconstructing text...")
            t2 = time.time()
            paragraphs = reconstruct_ocr_text(ocr_results)
            print(f"[Pipeline] Reconstruction done in {time.time()-t2:.2f}s")
            self.text_ready.emit(paragraphs)

            if not paragraphs:
                self.error_occurred.emit("Could not reconstruct any text.")
                return

            # ── Step 4: Translate ─────────────────────────────────
            if self._cancelled:
                return
            print("[Pipeline] Translating...")
            t3 = time.time()
            translator = get_translator()
            translated = translator.translate_paragraphs(paragraphs)
            print(f"[Pipeline] Translation done in {time.time()-t3:.2f}s")
            self.translation_done.emit(translated)

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"[Pipeline] Unhandled error:\n{tb}")
            self.error_occurred.emit(str(e))

        finally:
            self.finished.emit()