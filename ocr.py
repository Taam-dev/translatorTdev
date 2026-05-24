"""
ocr.py
------
OCR text extraction with multiple backend support.

Primary:  EasyOCR  (stable on Windows, no oneDNN issues)
Fallback: PaddleOCR (optional)
Fallback: Tesseract via pytesseract (optional)

EasyOCR is recommended - it works reliably on Windows 10/11
without the PaddlePaddle oneDNN driver issues.
"""

import numpy as np
from PIL import Image
from typing import Optional
import logging
import os
import sys

logger = logging.getLogger(__name__)


# ==================================================
# ENVIRONMENT PATCHES
# Suppress verbose output and fix known Windows issues
# ==================================================

def _patch_environment():
    """Apply environment variable patches before loading OCR libs."""
    # Suppress PaddlePaddle verbose logging
    os.environ.setdefault("GLOG_minloglevel", "3")
    os.environ.setdefault("GLOG_logtostderr", "0")
    os.environ.setdefault("FLAGS_call_stack_level", "0")

    # Disable oneDNN (MKL-DNN) to avoid the ConvertPirAttribute error on Windows
    # This is the root cause of the "ConvertPirAttribute2RuntimeAttribute" error
    os.environ["FLAGS_use_mkldnn"] = "0"
    os.environ["PADDLE_DISABLE_STATIC"] = "1"

    # Suppress EasyOCR/torch verbose output
    os.environ.setdefault("PYTHONWARNINGS", "ignore")


_patch_environment()


# ==================================================
# BASE CLASS
# ==================================================

class BaseOCREngine:
    """Abstract base for OCR backends."""

    def extract(self, image: Image.Image) -> list[dict]:
        """
        Extract text from PIL Image.

        Returns:
            List of dicts: {text, confidence, box}
            box: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
        """
        raise NotImplementedError

    def is_available(self) -> bool:
        """Check if this backend can be loaded."""
        raise NotImplementedError


# ==================================================
# EASYOCR BACKEND
# ==================================================

class EasyOCREngine(BaseOCREngine):
    """
    EasyOCR backend.

    Pros:
    - Stable on Windows (no oneDNN issues)
    - Good accuracy for English
    - Simple API

    Install: pip install easyocr
    """

    def __init__(self, languages: list[str] = None):
        self._languages = languages or ["en"]
        self._reader = None
        self._initialized = False

    def _initialize(self):
        if self._initialized:
            return

        try:
            import easyocr

            print(f"[OCR] Initializing EasyOCR (lang={self._languages})...")
            print("[OCR] First run will download models (~100MB), please wait...")

            # gpu=False for maximum compatibility
            # verbose=False to suppress download progress spam
            self._reader = easyocr.Reader(
                self._languages,
                gpu=False,
                verbose=False,
            )
            self._initialized = True
            print("[OCR] EasyOCR ready.")

        except ImportError:
            raise RuntimeError(
                "EasyOCR not installed.\n"
                "Run: pip install easyocr"
            )
        except Exception as e:
            raise RuntimeError(f"EasyOCR initialization failed: {e}")

    def is_available(self) -> bool:
        try:
            import easyocr
            return True
        except ImportError:
            return False

    def extract(self, image: Image.Image) -> list[dict]:
        """
        Run EasyOCR on a PIL Image.

        EasyOCR returns:
        [ ([x1,y1], [x2,y2], [x3,y3], [x4,y4]),  text,  confidence ]
        """
        self._initialize()

        # EasyOCR works best with numpy array
        img_array = np.array(image)

        # Handle grayscale images
        if len(img_array.shape) == 2:
            img_array = np.stack([img_array] * 3, axis=-1)
        elif img_array.shape[2] == 4:
            # RGBA -> RGB
            img_array = img_array[:, :, :3]

        try:
            # detail=1 returns bounding boxes
            # paragraph=False gives us per-word/line boxes
            results = self._reader.readtext(
                img_array,
                detail=1,
                paragraph=False,
            )
        except Exception as e:
            logger.error(f"EasyOCR readtext failed: {e}")
            print(f"[OCR] EasyOCR error: {e}")
            return []

        return self._parse_results(results)

    def _parse_results(self, raw: list) -> list[dict]:
        """Convert EasyOCR output to normalized format."""
        parsed = []
        for item in raw:
            try:
                if len(item) == 3:
                    box_raw, text, confidence = item
                elif len(item) == 2:
                    box_raw, text = item
                    confidence = 1.0
                else:
                    continue

                text = str(text).strip()
                if not text:
                    continue

                # EasyOCR box is list of 4 [x,y] points
                box = [[float(pt[0]), float(pt[1])] for pt in box_raw]

                parsed.append({
                    "text": text,
                    "confidence": float(confidence),
                    "box": box,
                })
            except Exception as e:
                logger.debug(f"Result parse error: {e}")
                continue

        return parsed

    def change_language(self, languages: list[str]):
        """Change OCR languages - requires re-init."""
        if sorted(languages) != sorted(self._languages):
            self._languages = languages
            self._initialized = False
            self._reader = None


# ==================================================
# PADDLEOCR BACKEND (FALLBACK)
# ==================================================

class PaddleOCREngine(BaseOCREngine):
    """
    PaddleOCR backend - optional fallback.

    Known issues on Windows:
    - Requires specific PaddlePaddle version
    - oneDNN driver issues (mitigated by FLAGS_use_mkldnn=0)
    - Slower initialization
    """

    def __init__(self, language: str = "en"):
        self._language = language
        self._ocr = None
        self._initialized = False

    def is_available(self) -> bool:
        try:
            import paddleocr
            return True
        except ImportError:
            return False

    def _initialize(self):
        if self._initialized:
            return

        try:
            from paddleocr import PaddleOCR
            print(f"[OCR] Initializing PaddleOCR (lang={self._language})...")

            errors = []

            # Attempt 1: New minimal API
            try:
                self._ocr = PaddleOCR(lang=self._language)
                self._initialized = True
                print("[OCR] PaddleOCR ready (new API).")
                return
            except Exception as e:
                errors.append(str(e))

            # Attempt 2: Old API without problematic args
            try:
                self._ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang=self._language,
                    use_gpu=False,
                    enable_mkldnn=False,  # Disable oneDNN explicitly
                )
                self._initialized = True
                print("[OCR] PaddleOCR ready (old API).")
                return
            except Exception as e:
                errors.append(str(e))

            # Attempt 3: Absolute bare minimum
            try:
                self._ocr = PaddleOCR()
                self._initialized = True
                print("[OCR] PaddleOCR ready (bare).")
                return
            except Exception as e:
                errors.append(str(e))

            raise RuntimeError("\n".join(errors))

        except ImportError:
            raise RuntimeError("PaddleOCR not installed.")

    def extract(self, image: Image.Image) -> list[dict]:
        self._initialize()
        img_array = np.array(image)

        raw = None
        try:
            raw = self._ocr.ocr(img_array, cls=True)
        except TypeError:
            try:
                raw = self._ocr.ocr(img_array)
            except Exception as e:
                print(f"[OCR] PaddleOCR.ocr() failed: {e}")
                return []
        except Exception as e:
            print(f"[OCR] PaddleOCR.ocr() failed: {e}")
            return []

        return self._parse(raw)

    def _parse(self, raw) -> list[dict]:
        if not raw or raw[0] is None:
            return []
        results = []
        try:
            for line in raw[0]:
                if not line or len(line) < 2:
                    continue
                box = [[float(p[0]), float(p[1])] for p in line[0]]
                text_info = line[1]
                if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                    text = str(text_info[0]).strip()
                    conf = float(text_info[1])
                else:
                    text = str(text_info).strip()
                    conf = 1.0
                if text:
                    results.append({"text": text, "confidence": conf, "box": box})
        except Exception as e:
            logger.error(f"PaddleOCR parse error: {e}")
        return results


# ==================================================
# SMART ENGINE SELECTOR
# ==================================================

# Language code mapping: settings code -> EasyOCR language list
EASYOCR_LANG_MAP = {
    "en":     ["en"],
    "vi":     ["en", "vi"],     # EasyOCR supports Vietnamese
    "ch":     ["ch_sim", "en"],
    "ja":     ["ja", "en"],
    "japan":  ["ja", "en"],
    "ko":     ["ko", "en"],
    "korean": ["ko", "en"],
    "fr":     ["fr", "en"],
    "french": ["fr", "en"],
    "de":     ["de", "en"],
    "german": ["de", "en"],
    "es":     ["es", "en"],
    "ru":     ["ru", "en"],
}

# Settings code -> PaddleOCR language string
PADDLE_LANG_MAP = {
    "en":     "en",
    "vi":     "en",   # PaddleOCR doesn't have Vietnamese, use English
    "ch":     "ch",
    "ja":     "japan",
    "japan":  "japan",
    "ko":     "korean",
    "korean": "korean",
    "fr":     "french",
    "french": "french",
    "de":     "german",
    "german": "german",
}


class OCREngineManager:
    """
    Manages OCR backend selection with automatic fallback.

    Priority order:
    1. EasyOCR  (most stable on Windows)
    2. PaddleOCR (fallback if EasyOCR unavailable)
    """

    def __init__(self):
        self._engine: Optional[BaseOCREngine] = None
        self._backend_name: str = ""
        self._current_lang: str = ""

    def get_engine(self, lang_code: str = "en") -> BaseOCREngine:
        """
        Get the best available OCR engine for the given language.
        Reuses existing engine if language hasn't changed.
        """
        if self._engine is not None and lang_code == self._current_lang:
            return self._engine

        self._current_lang = lang_code

        # Try EasyOCR first
        easyocr_langs = EASYOCR_LANG_MAP.get(lang_code, ["en"])
        easy = EasyOCREngine(languages=easyocr_langs)

        if easy.is_available():
            print(f"[OCR] Using EasyOCR backend (langs={easyocr_langs})")
            self._engine = easy
            self._backend_name = "easyocr"
            return self._engine

        # Try PaddleOCR
        paddle_lang = PADDLE_LANG_MAP.get(lang_code, "en")
        paddle = PaddleOCREngine(language=paddle_lang)

        if paddle.is_available():
            print(f"[OCR] Using PaddleOCR backend (lang={paddle_lang})")
            self._engine = paddle
            self._backend_name = "paddleocr"
            return self._engine

        raise RuntimeError(
            "No OCR backend available!\n"
            "Install EasyOCR:    pip install easyocr\n"
            "Install PaddleOCR:  pip install paddleocr paddlepaddle"
        )

    def extract(self, image: Image.Image, lang_code: str = "en") -> list[dict]:
        """Convenience: get engine and extract in one call."""
        engine = self.get_engine(lang_code)
        return engine.extract(image)

    @property
    def backend_name(self) -> str:
        return self._backend_name


# ==================================================
# UTILITY
# ==================================================

def get_bounding_rect(box: list) -> tuple[int, int, int, int]:
    """Convert quad box [[x,y]x4] to (x, y, w, h)."""
    xs = [pt[0] for pt in box]
    ys = [pt[1] for pt in box]
    x = int(min(xs))
    y = int(min(ys))
    w = int(max(xs)) - x
    h = int(max(ys)) - y
    return x, y, w, h


def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """
    Preprocess image to improve OCR accuracy.

    Steps:
    - Upscale small images (OCR struggles with tiny text)
    - Convert to RGB
    - Enhance contrast slightly
    """
    from PIL import ImageEnhance, ImageFilter

    # Ensure RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    w, h = image.size

    # Upscale if image is very small
    MIN_SIZE = 100
    if w < MIN_SIZE or h < MIN_SIZE:
        scale = max(MIN_SIZE / w, MIN_SIZE / h, 1.0)
        new_w = int(w * scale)
        new_h = int(h * scale)
        image = image.resize((new_w, new_h), Image.LANCZOS)
        print(f"[OCR] Upscaled image: {w}x{h} -> {new_w}x{new_h}")

    # Upscale for better OCR if image is small overall
    PREFERRED_MIN = 400
    if w < PREFERRED_MIN and h < PREFERRED_MIN:
        scale = 2.0
        image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        print(f"[OCR] Upscaled 2x for OCR quality")

    # Slight contrast boost helps OCR accuracy
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.3)

    return image


# ==================================================
# GLOBAL INSTANCE
# ==================================================

_manager = OCREngineManager()


def get_ocr_engine(language: str = "en") -> BaseOCREngine:
    """Get the best available OCR engine for the given language."""
    return _manager.get_engine(language)


def run_ocr(image: Image.Image, language: str = "en") -> list[dict]:
    """
    Main OCR entry point used by the pipeline.

    Preprocesses image then runs OCR.

    Args:
        image: PIL Image to process
        language: Language code from settings

    Returns:
        List of {text, confidence, box} dicts
    """
    # Preprocess for better accuracy
    processed = preprocess_image_for_ocr(image)

    engine = _manager.get_engine(language)
    results = engine.extract(processed)

    # Log results for debugging
    print(f"[OCR] Extracted {len(results)} text boxes:")
    for r in results:
        print(f"[OCR]   conf={r['confidence']:.2f}  text={r['text']!r}")

    return results