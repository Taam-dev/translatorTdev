"""
settings.py
"""

import json
import os
import sys
from pathlib import Path

DEFAULT_SETTINGS = {
    "source_language": "en",
    "target_language": "vi",
    "hotkey": "q",
    "font_size": 16,
    "overlay_opacity": 0.92,
    "overlay_bg_color": "#0f0f1e",
    "overlay_text_color": "#e8e8e8",
    "translation_backend": "google",
    "translation_style": "novel",
    "openai_api_key": "",
    "openai_model": "gpt-4o-mini",
    "ollama_host": "http://localhost:11434",
    "ollama_model": "qwen2.5:7b",
    "lmstudio_host": "http://localhost:1234",
    "lmstudio_model": "local-model",
    "llamacpp_host": "http://localhost:8080",
    "ocr_language": "en",
    "cache_translations": True,
    "max_cache_size": 500,
    "cleanup_with_ai": False,
    "custom_background": "",
    "use_custom_background": False,
    "background_opacity": 0.35,
    "auto_start": False,
}


def get_resource_path(relative_path: str) -> Path:
    """
    Trả về đường dẫn đúng cả khi chạy từ source lẫn từ .exe
    PyInstaller extract files vào sys._MEIPASS khi chạy
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Chạy từ .exe → files được extract vào _MEIPASS
        base = Path(sys._MEIPASS)
    else:
        # Chạy từ source
        base = Path(os.path.dirname(os.path.abspath(__file__)))
    return base / relative_path


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(os.path.dirname(os.path.abspath(__file__)))


BASE_DIR = _get_base_dir()
SETTINGS_DIR = BASE_DIR
SETTINGS_FILE = BASE_DIR / "settings.json"
CACHE_DIR = BASE_DIR / "cache"

# ASSETS_DIR phải trỏ vào _MEIPASS khi chạy exe
# vì assets được bundle vào bên trong exe
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    ASSETS_DIR = Path(sys._MEIPASS) / "assets"
else:
    ASSETS_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "assets"


class Settings:
    def __init__(self):
        self._data = dict(DEFAULT_SETTINGS)
        self._ensure_dirs()
        self.load()

    def _ensure_dirs(self):
        try:
            CACHE_DIR.mkdir(exist_ok=True, parents=True)
        except Exception:
            pass
        try:
            ASSETS_DIR.mkdir(exist_ok=True, parents=True)
        except Exception:
            pass

    def load(self):
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                for key, default in DEFAULT_SETTINGS.items():
                    self._data[key] = saved.get(key, default)
            except Exception as e:
                print(f"[Settings] Load failed: {e}", file=sys.__stderr__)
                self._data = dict(DEFAULT_SETTINGS)
        else:
            self.save()

    def save(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Settings] Save failed: {e}", file=sys.__stderr__)

    def get(self, key, fallback=None):
        return self._data.get(key, fallback)

    def set(self, key, value):
        self._data[key] = value
        self.save()

    def get_all(self):
        return dict(self._data)

    def update(self, data: dict):
        self._data.update(data)
        self.save()


settings = Settings()
