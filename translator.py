"""
translator.py
-------------
Translation backends:

1. Google Translate  — free, online, no setup
2. OpenAI GPT        — best quality, paid API
3. Ollama            — FREE local AI (Llama, Qwen, Gemma...)
4. LM Studio         — FREE local AI (OpenAI-compatible API)
5. llama.cpp server  — FREE local AI (raw server)

Local AI backends (3,4,5) run 100% offline after model download.
Quality is significantly better than Google Translate for literary content.
"""

import json
import hashlib
import time
import re
from pathlib import Path
from typing import Optional
from settings import settings, CACHE_DIR

TRANSLATION_CACHE_FILE = CACHE_DIR / "translation_cache.json"


# ==================================================
# TRANSLATION CACHE
# ==================================================


class TranslationCache:
    """Persistent local translation cache."""

    def __init__(self, max_size: int = 500):
        self.max_size = max_size
        self._cache: dict = {}
        self._load()

    def _load(self):
        if TRANSLATION_CACHE_FILE.exists():
            try:
                with open(TRANSLATION_CACHE_FILE, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}

    def _save(self):
        try:
            with open(TRANSLATION_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Cache] Save failed: {e}")

    def _key(self, text: str, src: str, tgt: str, backend: str) -> str:
        content = f"{backend}:{src}:{tgt}:{text}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, text: str, src: str, tgt: str, backend: str = "") -> Optional[str]:
        return self._cache.get(self._key(text, src, tgt, backend))

    def set(self, text: str, src: str, tgt: str, translation: str, backend: str = ""):
        if len(self._cache) >= self.max_size:
            # Remove oldest 10%
            keys = list(self._cache.keys())
            for k in keys[: max(1, len(keys) // 10)]:
                del self._cache[k]
        self._cache[self._key(text, src, tgt, backend)] = translation
        self._save()

    def clear(self):
        self._cache = {}
        self._save()

    def size(self) -> int:
        return len(self._cache)


_cache = TranslationCache(max_size=settings.get("max_cache_size", 500))


# ==================================================
# LANGUAGE HELPERS
# ==================================================

LANG_NAMES = {
    "en": "English",
    "vi": "Vietnamese",
    "zh": "Chinese (Simplified)",
    "ja": "Japanese",
    "ko": "Korean",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "ru": "Russian",
    "th": "Thai",
    "id": "Indonesian",
    "pt": "Portuguese",
    "ar": "Arabic",
    "hi": "Hindi",
}


def lang_name(code: str) -> str:
    return LANG_NAMES.get(code, code.upper())


# ==================================================
# TRANSLATION PROMPT BUILDER
# ==================================================


def build_translation_prompt(
    text: str,
    source: str,
    target: str,
    style: str = "novel",
) -> str:
    """
    Build a high-quality translation prompt optimized for
    web novels, manga, manhwa, and literary content.

    Args:
        text: Text to translate
        source: Source language code
        target: Target language code
        style: "novel", "manga", "subtitle", "general"
    """
    src_name = lang_name(source)
    tgt_name = lang_name(target)

    style_instructions = {
        "novel": (
            "This is web novel / light novel content. "
            "Preserve the narrative style, dramatic tension, and character voices. "
            "Keep honorifics (san, kun, nim, etc.) untranslated. "
            "Preserve character names exactly as written."
        ),
        "manga": (
            "This is manga / manhwa / manhua dialogue. "
            "Keep translations short and punchy to fit speech bubbles. "
            "Preserve sound effects style (BOOM, SLASH, etc.). "
            "Keep character names untranslated."
        ),
        "subtitle": (
            "This is subtitle text. "
            "Keep translations concise and natural for reading speed. "
            "Preserve speaker emotion and tone."
        ),
        "general": ("Translate naturally and accurately."),
    }

    style_note = style_instructions.get(style, style_instructions["novel"])

    prompt = f"""You are a professional {src_name}-to-{tgt_name} literary translator.

Task: Translate the following {src_name} text to {tgt_name}.

Rules:
- Sound completely natural in {tgt_name} — not like a translation
- Preserve the original tone, emotion, and writing style
- Preserve character names (do not translate proper nouns)
- Preserve honorifics and cultural terms when appropriate
- Fix any OCR artifacts or broken formatting in the source text
- Do NOT add explanations, notes, or translator comments
- Return ONLY the translated text, nothing else

Style note: {style_note}

{src_name} text to translate:
{text}

{tgt_name} translation:"""

    return prompt


# ==================================================
# BACKEND: GOOGLE TRANSLATE (free, online)
# ==================================================


class GoogleTranslateBackend:
    """
    Google Translate via deep-translator.
    Free, no API key, but requires internet.
    Quality: ⭐⭐⭐ (decent but robotic for literary content)
    """

    NAME = "google"

    def __init__(self):
        self._GT = None
        self._load()

    def _load(self):
        try:
            from deep_translator import GoogleTranslator

            self._GT = GoogleTranslator
        except ImportError:
            raise RuntimeError(
                "deep-translator not installed.\n" "Run: pip install deep-translator"
            )

    def translate(self, text: str, source: str, target: str) -> str:
        if not text.strip():
            return text
        try:
            # Google has ~5000 char limit per request
            if len(text) > 4500:
                return self._translate_chunked(text, source, target)
            t = self._GT(source=source, target=target)
            result = t.translate(text)
            return result or text
        except Exception as e:
            print(f"[Google] Translation error: {e}")
            return text

    def _translate_chunked(self, text: str, source: str, target: str) -> str:
        """Split long text at sentence boundaries and translate in chunks."""
        # Split at paragraph or sentence boundaries
        chunks = re.split(r"(\n\n|\. (?=[A-Z]))", text)
        translated = []
        buf = ""
        for chunk in chunks:
            if len(buf) + len(chunk) < 4500:
                buf += chunk
            else:
                if buf:
                    t = self._GT(source=source, target=target)
                    translated.append(t.translate(buf) or buf)
                buf = chunk
        if buf:
            t = self._GT(source=source, target=target)
            translated.append(t.translate(buf) or buf)
        return "".join(translated)

    def is_available(self) -> bool:
        return self._GT is not None

    def test_connection(self) -> tuple[bool, str]:
        try:
            t = self._GT(source="en", target="vi")
            result = t.translate("hello")
            return bool(result), "OK"
        except Exception as e:
            return False, str(e)


# ==================================================
# BACKEND: OPENAI (paid, best quality)
# ==================================================


class OpenAIBackend:
    """
    OpenAI GPT translation.
    Paid API, highest quality.
    Quality: ⭐⭐⭐⭐⭐
    """

    NAME = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import openai

            self._client = openai.OpenAI(api_key=self.api_key)
        return self._client

    def translate(self, text: str, source: str, target: str) -> str:
        if not text.strip() or not self.api_key:
            return text
        prompt = build_translation_prompt(
            text, source, target, style=settings.get("translation_style", "novel")
        )
        try:
            client = self._get_client()
            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional literary translator. Return only the translation, no explanations.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2000,
                temperature=0.3,
            )
            return resp.choices[0].message.content.strip() or text
        except Exception as e:
            print(f"[OpenAI] Error: {e}")
            return text

    def is_available(self) -> bool:
        return bool(self.api_key)

    def test_connection(self) -> tuple[bool, str]:
        try:
            client = self._get_client()
            resp = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Say OK"}],
                max_tokens=5,
            )
            return True, f"Model: {self.model}"
        except Exception as e:
            return False, str(e)


# ==================================================
# BACKEND: OLLAMA (free local AI)
# ==================================================


class OllamaBackend:
    """
    Ollama local AI backend.

    Ollama runs LLMs locally — 100% free, offline after setup.
    Recommended models for translation:
    - qwen2.5:7b        — Best for EN↔VI, EN↔ZH (multilingual)
    - gemma3:4b         — Good quality, fast, low RAM
    - llama3.2:3b       — Fast, decent quality
    - mistral:7b        — Good for European languages
    - qwen2.5:14b       — Higher quality, needs 16GB RAM
    - aya:8b            — Specifically trained for multilingual

    Install: https://ollama.ai
    Models:  ollama pull qwen2.5:7b

    Quality: ⭐⭐⭐⭐ (excellent for Asian languages with qwen)
    """

    NAME = "ollama"
    DEFAULT_HOST = "http://localhost:11434"

    # Recommended models ranked by translation quality
    RECOMMENDED_MODELS = [
        ("qwen2.5:7b", "Best for EN↔VI/ZH, 4.7GB", "4GB RAM"),
        ("gemma3:4b", "Fast, good quality, 3.3GB", "6GB RAM"),
        ("qwen2.5:14b", "High quality, 9GB", "16GB RAM"),
        ("llama3.2:3b", "Very fast, 2GB", "4GB RAM"),
        ("aya:8b", "Multilingual specialist, 5GB", "8GB RAM"),
        ("mistral:7b", "Good for EU languages, 4.1GB", "8GB RAM"),
        ("qwen2.5:3b", "Lightweight, 2GB", "4GB RAM"),
    ]

    def __init__(self, host: str = None, model: str = "qwen2.5:7b"):
        self.host = (host or self.DEFAULT_HOST).rstrip("/")
        self.model = model
        self._session = None

    def _get_session(self):
        if self._session is None:
            import requests

            self._session = requests.Session()
            self._session.headers.update({"Content-Type": "application/json"})
        return self._session

    def translate(self, text: str, source: str, target: str) -> str:
        if not text.strip():
            return text

        prompt = build_translation_prompt(
            text, source, target, style=settings.get("translation_style", "novel")
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
                "num_predict": 2048,
                # Keep model loaded for 5 minutes between requests
                "keep_alive": "5m",
            },
        }

        try:
            session = self._get_session()
            resp = session.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=120,  # Local models can be slow on first token
            )
            resp.raise_for_status()
            data = resp.json()
            result = data.get("response", "").strip()

            # Clean up common model output artifacts
            result = self._clean_output(result, text)
            return result or text

        except Exception as e:
            print(f"[Ollama] Error: {e}")
            return text

    def _clean_output(self, output: str, original: str) -> str:
        """Remove common LLM output artifacts."""
        # Remove "Translation:" prefix if model added it
        output = re.sub(
            r"^(Translation|Translated|Output|Result|Answer)\s*:\s*",
            "",
            output,
            flags=re.IGNORECASE,
        ).strip()

        # Remove surrounding quotes if the whole thing is quoted
        if output.startswith('"') and output.endswith('"') and output.count('"') == 2:
            output = output[1:-1]

        # Remove "Note:" or explanations at end
        output = re.sub(
            r"\n*(Note|Translator\'?s? note|TN)\s*:.*$",
            "",
            output,
            flags=re.IGNORECASE | re.DOTALL,
        ).strip()

        return output

    def is_available(self) -> bool:
        """Check if Ollama server is running."""
        try:
            import requests

            resp = requests.get(f"{self.host}/api/tags", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def test_connection(self) -> tuple[bool, str]:
        """Test connection and return (success, message)."""
        try:
            import requests

            resp = requests.get(f"{self.host}/api/tags", timeout=5)
            if resp.status_code != 200:
                return False, f"HTTP {resp.status_code}"

            data = resp.json()
            models = [m["name"] for m in data.get("models", [])]

            if not models:
                return False, "Ollama running but no models installed"

            if self.model.split(":")[0] in " ".join(models):
                return (
                    True,
                    f"Model '{self.model}' ready. All models: {', '.join(models)}",
                )
            else:
                return False, (
                    f"Model '{self.model}' not found.\n"
                    f"Available: {', '.join(models)}\n"
                    f"Install: ollama pull {self.model}"
                )
        except Exception as e:
            return False, f"Cannot connect to Ollama at {self.host}: {e}"

    def list_models(self) -> list[str]:
        """List all installed Ollama models."""
        try:
            import requests

            resp = requests.get(f"{self.host}/api/tags", timeout=5)
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def pull_model(self, model_name: str, progress_cb=None) -> bool:
        """
        Pull (download) a model. Calls progress_cb(status_str) during download.
        This is a blocking call - run in a thread.
        """
        try:
            import requests

            resp = requests.post(
                f"{self.host}/api/pull",
                json={"name": model_name},
                stream=True,
                timeout=600,
            )
            for line in resp.iter_lines():
                if line:
                    data = json.loads(line)
                    status = data.get("status", "")
                    if progress_cb:
                        progress_cb(status)
                    if data.get("error"):
                        print(f"[Ollama] Pull error: {data['error']}")
                        return False
            return True
        except Exception as e:
            print(f"[Ollama] Pull failed: {e}")
            return False


# ==================================================
# BACKEND: LM STUDIO (free local AI, OpenAI-compatible)
# ==================================================


class LMStudioBackend:
    """
    LM Studio local AI backend.

    LM Studio provides an OpenAI-compatible local API.
    Download any GGUF model and run it locally.

    Recommended models for translation:
    - Qwen2.5-7B-Instruct-GGUF (best for Vietnamese/Chinese)
    - Gemma-3-4B-Instruct-GGUF (fast, good quality)
    - Mistral-7B-Instruct-GGUF (good for European languages)

    Install LM Studio: https://lmstudio.ai
    Then: Start Local Server in LM Studio

    Quality: ⭐⭐⭐⭐ (same as Ollama, depends on model)
    """

    NAME = "lmstudio"
    DEFAULT_HOST = "http://localhost:1234"

    def __init__(self, host: str = None, model: str = "local-model"):
        self.host = (host or self.DEFAULT_HOST).rstrip("/")
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import openai

            self._client = openai.OpenAI(
                base_url=f"{self.host}/v1",
                api_key="lm-studio",  # LM Studio doesn't need a real key
            )
        return self._client

    def translate(self, text: str, source: str, target: str) -> str:
        if not text.strip():
            return text

        prompt = build_translation_prompt(
            text, source, target, style=settings.get("translation_style", "novel")
        )

        try:
            client = self._get_client()
            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional literary translator. Return only the translation, no explanations.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2000,
                temperature=0.3,
            )
            result = resp.choices[0].message.content.strip()

            # Clean output artifacts
            result = re.sub(
                r"^(Translation|Translated)\s*:\s*", "", result, flags=re.IGNORECASE
            ).strip()

            return result or text
        except Exception as e:
            print(f"[LMStudio] Error: {e}")
            return text

    def is_available(self) -> bool:
        try:
            import requests

            resp = requests.get(
                f"{self.host}/v1/models",
                timeout=3,
                headers={"Authorization": "Bearer lm-studio"},
            )
            return resp.status_code == 200
        except Exception:
            return False

    def test_connection(self) -> tuple[bool, str]:
        try:
            import requests

            resp = requests.get(
                f"{self.host}/v1/models",
                timeout=5,
                headers={"Authorization": "Bearer lm-studio"},
            )
            if resp.status_code == 200:
                data = resp.json()
                models = [m["id"] for m in data.get("data", [])]
                if models:
                    return True, f"LM Studio running. Models: {', '.join(models)}"
                return True, "LM Studio running (no model loaded)"
            return False, f"HTTP {resp.status_code}"
        except Exception as e:
            return False, f"Cannot connect to LM Studio at {self.host}: {e}"

    def list_models(self) -> list[str]:
        try:
            import requests

            resp = requests.get(
                f"{self.host}/v1/models",
                timeout=5,
                headers={"Authorization": "Bearer lm-studio"},
            )
            data = resp.json()
            return [m["id"] for m in data.get("data", [])]
        except Exception:
            return []


# ==================================================
# BACKEND: LLAMACPP SERVER
# ==================================================


class LlamaCppBackend:
    """
    llama.cpp HTTP server backend.
    For advanced users running llama.cpp manually.

    Start server:
        llama-server -m model.gguf --port 8080 -c 4096

    Quality: ⭐⭐⭐⭐ (depends on model)
    """

    NAME = "llamacpp"
    DEFAULT_HOST = "http://localhost:8080"

    def __init__(self, host: str = None):
        self.host = (host or self.DEFAULT_HOST).rstrip("/")

    def translate(self, text: str, source: str, target: str) -> str:
        if not text.strip():
            return text

        prompt = build_translation_prompt(text, source, target)

        payload = {
            "prompt": prompt,
            "n_predict": 2048,
            "temperature": 0.3,
            "top_p": 0.9,
            "stop": ["\n\n\n", "---", "Note:", "Translator"],
        }

        try:
            import requests

            resp = requests.post(
                f"{self.host}/completion",
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            result = data.get("content", "").strip()
            return result or text
        except Exception as e:
            print(f"[llama.cpp] Error: {e}")
            return text

    def is_available(self) -> bool:
        try:
            import requests

            resp = requests.get(f"{self.host}/health", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def test_connection(self) -> tuple[bool, str]:
        try:
            import requests

            resp = requests.get(f"{self.host}/health", timeout=5)
            if resp.status_code == 200:
                return True, f"llama.cpp server running at {self.host}"
            return False, f"HTTP {resp.status_code}"
        except Exception as e:
            return False, f"Cannot connect: {e}"


# ==================================================
# MAIN TRANSLATOR
# ==================================================


class Translator:
    """
    Main translation interface.
    Selects backend from settings, handles caching,
    supports all 5 backends.
    """

    BACKENDS = {
        "google": GoogleTranslateBackend,
        "openai": OpenAIBackend,
        "ollama": OllamaBackend,
        "lmstudio": LMStudioBackend,
        "llamacpp": LlamaCppBackend,
    }

    def __init__(self):
        self._backend = None
        self._backend_name = ""
        self._init_backend()

    def _init_backend(self):
        name = settings.get("translation_backend", "google")

        try:
            if name == "google":
                self._backend = GoogleTranslateBackend()

            elif name == "openai":
                self._backend = OpenAIBackend(
                    api_key=settings.get("openai_api_key", ""),
                    model=settings.get("openai_model", "gpt-4o-mini"),
                )

            elif name == "ollama":
                self._backend = OllamaBackend(
                    host=settings.get("ollama_host", "http://localhost:11434"),
                    model=settings.get("ollama_model", "qwen2.5:7b"),
                )

            elif name == "lmstudio":
                self._backend = LMStudioBackend(
                    host=settings.get("lmstudio_host", "http://localhost:1234"),
                    model=settings.get("lmstudio_model", "local-model"),
                )

            elif name == "llamacpp":
                self._backend = LlamaCppBackend(
                    host=settings.get("llamacpp_host", "http://localhost:8080"),
                )

            else:
                self._backend = GoogleTranslateBackend()
                name = "google"

            self._backend_name = name
            print(f"[Translator] Backend: {name}")

        except Exception as e:
            print(f"[Translator] Backend init failed: {e}")
            self._backend = GoogleTranslateBackend()
            self._backend_name = "google"

    def translate(self, text, source=None, target=None):
        src = source or settings.get("source_language", "en")
        tgt = target or settings.get("target_language", "vi")

        if not text.strip():
            return text

        if settings.get("translation_backend", "google") != self._backend_name:
            self._init_backend()

        cached = _cache.get(text, src, tgt, self._backend_name)
        if cached:
            return cached

        try:
            result = self._backend.translate(text, src, tgt)
        except Exception:
            result = text

        if result and result != text:
            _cache.set(text, src, tgt, result, self._backend_name)

        return result

    def translate_paragraphs(self, paragraphs: list[str]) -> list[str]:
        if not paragraphs:
            return []

        backend = settings.get("translation_backend", "google")

        if backend in ("ollama", "lmstudio", "llamacpp", "openai"):
            return self._translate_as_block(paragraphs)

        return [self.translate(p) for p in paragraphs]

    # ================= FIXED FUNCTION =================
    def _translate_as_block(self, paragraphs: list[str]) -> list[str]:
        """
        Join paragraphs → translate → split back
        """

        if not paragraphs:
            return []

        if len(paragraphs) == 1:
            result = self.translate(paragraphs[0])
            return [result] if result and result.strip() else paragraphs

        SEP = "\n§§§\n"
        combined = SEP.join(paragraphs)

        if len(combined) > 6000:
            return [self.translate(p) if p.strip() else p for p in paragraphs]

        translated = self.translate(combined)

        if not translated or not translated.strip():
            return paragraphs

        # try split by separator
        if "§§§" in translated:
            parts = [p.strip() for p in translated.split("§§§")]
            parts = [p for p in parts if p]

            if len(parts) == len(paragraphs):
                return parts

        # fallback split
        parts = [p.strip() for p in translated.split("\n\n") if p.strip()]
        if len(parts) == len(paragraphs):
            return parts

        # final fallback
        return [translated.strip()] + paragraphs[1:]

    def test_backend(self):
        if hasattr(self._backend, "test_connection"):
            return self._backend.test_connection()
        return self._backend.is_available(), "OK"

    def get_cache_stats(self):
        return {
            "size": _cache.size(),
            "max": settings.get("max_cache_size", 500),
        }

    def clear_cache(self):
        _cache.clear()


# Global instance
_translator: Optional[Translator] = None


def get_translator() -> Translator:
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator


def reset_translator():
    """Force re-initialization (call after settings change)."""
    global _translator
    _translator = None
