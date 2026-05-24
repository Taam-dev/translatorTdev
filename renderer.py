"""
renderer.py
-----------
Async pipeline: Capture → OCR → Reconstruct → Translate
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


class TranslationWorker(QObject):
    """
    Background worker running the full translation pipeline.
    Communicates with UI via Qt signals (thread-safe).
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
        """Start pipeline in background thread.

        Nếu pipeline cũ còn chạy → wait cho nó xong trước.
        """
        with self._lock:
            # Cancel pipeline cũ nếu đang chạy
            if self._thread is not None and self._thread.is_alive():
                print("[Pipeline] Previous pipeline still running, cancelling...")
                self._cancelled = True
                # Không join ở đây (sẽ block UI thread)
                # Thay vào đó dùng flag để thread cũ tự dừng
                return  # Không start pipeline mới, tránh double-run

            self._cancelled = False
            self._thread = threading.Thread(
                target=self._worker,
                args=(x, y, width, height),
                daemon=True,
                name="OCRTranslatePipeline",
            )
            self._thread.start()

    def cancel(self):
        """Request cancellation. Non-blocking."""
        self._cancelled = True
        # Không join ở đây vì có thể được gọi từ main thread
        # Thread sẽ tự dừng tại checkpoint _cancelled tiếp theo

    def is_running(self) -> bool:
        """Check if pipeline thread is currently active."""
        return self._thread is not None and self._thread.is_alive()

    def _check_cancelled(self) -> bool:
        """Checkpoint: return True nếu đã bị cancel."""
        return self._cancelled

    def _worker(self, x: int, y: int, width: int, height: int):
        """Main worker chạy trong background thread."""

        # Emit started từ thread - OK vì QueuedConnection
        self.started.emit()

        success = False
        try:
            # ── Step 1: Capture ──────────────────────────────────
            if self._check_cancelled():
                return

            print(f"[Pipeline] Capturing region: ({x},{y}) {width}×{height}")
            t0 = time.time()

            try:
                image = capture_region(x, y, width, height)
            except ValueError as e:
                self.error_occurred.emit(f"Invalid capture region: {e}")
                return
            except Exception as e:
                self.error_occurred.emit(f"Capture failed: {e}")
                return

            print(f"[Pipeline] Capture done in {time.time()-t0:.2f}s")

            # ── Step 2: OCR ───────────────────────────────────────
            if self._check_cancelled():
                return

            print("[Pipeline] Running OCR...")
            t1 = time.time()

            try:
                lang = settings.get("ocr_language", "en")
                ocr_results = run_ocr(image, lang)
            except Exception as e:
                self.error_occurred.emit(f"OCR failed: {e}")
                return

            print(
                f"[Pipeline] OCR done in {time.time()-t1:.2f}s — "
                f"{len(ocr_results)} boxes."
            )
            self.ocr_done.emit(ocr_results)

            if not ocr_results:
                self.error_occurred.emit(
                    "No text detected in selected region.\n"
                    "Tips: chọn vùng có chữ rõ ràng, "
                    "đảm bảo ngôn ngữ OCR đúng với text."
                )
                return

            # ── Step 3: Reconstruct ───────────────────────────────
            if self._check_cancelled():
                return

            print("[Pipeline] Reconstructing text...")
            t2 = time.time()

            try:
                paragraphs = reconstruct_ocr_text(ocr_results)
            except Exception as e:
                self.error_occurred.emit(f"Text reconstruction failed: {e}")
                return

            print(f"[Pipeline] Reconstruction done in {time.time()-t2:.2f}s")

            # Lọc paragraphs rỗng
            paragraphs = [p for p in paragraphs if p and p.strip()]
            self.text_ready.emit(paragraphs)

            if not paragraphs:
                self.error_occurred.emit("Could not reconstruct any text.")
                return

            # ── Step 4: Translate ─────────────────────────────────
            if self._check_cancelled():
                return

            print("[Pipeline] Translating...")
            t3 = time.time()

            try:
                translator = get_translator()
                translated = translator.translate_paragraphs(paragraphs)
            except Exception as e:
                self.error_occurred.emit(f"Translation failed: {e}")
                return

            print(f"[Pipeline] Translation done in {time.time()-t3:.2f}s")

            # Lọc kết quả rỗng
            translated = [p for p in translated if p and p.strip()]

            if not translated:
                self.error_occurred.emit("Translation produced no output.")
                return

            if not self._check_cancelled():
                self.translation_done.emit(translated)
                success = True

        except Exception as e:
            import traceback

            tb = traceback.format_exc()
            print(f"[Pipeline] Unhandled error:\n{tb}")
            if not self._cancelled:
                self.error_occurred.emit(f"Unexpected error: {e}")

        finally:
            # finished luôn được emit để unlock _busy
            # nhưng chỉ khi không bị cancel giữa chừng
            self.finished.emit()
