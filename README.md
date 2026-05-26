<div align="center">

# 🌐 TranslatorTdev

**Real-time screen translation tool**  
Capture any screen region → OCR → Translate → Display overlay

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![PySide6](https://img.shields.io/badge/PySide6-6.x-green?logo=qt)](https://doc.qt.io/qtforpython/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Release](https://img.shields.io/github/v/release/YOUR_USERNAME/translatorTdev)](https://github.com/YOUR_USERNAME/translatorTdev/releases)

![Demo](assets/demo.gif)

</div>

---

## ✨ Features

- **Global hotkey** capture (works in any app, any window)
- **Screen freeze + drag selection** for precise region capture
- **EasyOCR** for accurate text extraction (with PaddleOCR fallback)
- **Intelligent OCR reconstruction** — fixes broken lines, hyphen splits, OCR errors
- **5 translation backends** — Google Translate, OpenAI GPT, Ollama, LM Studio, llama.cpp
- **Local AI support** — translate 100% offline with Ollama or LM Studio
- **Translation overlay** renders directly on screen over the selected region
- **Local translation cache** for speed and offline repeat translations
- **Dark minimal UI** — developer tool aesthetic
- **Vietnamese accent support**
- **Auto-fit text** in overlay

---

## 🚀 Quick Start

- Windows 10 or 11 (64-bit)
- Python 3.10+
- Internet connection (for Google / OpenAI backends)
- For local AI: Ollama or LM Studio installed separately

---

## Installation

### Option A — Download Release *(No Python needed)*

1. Go to [Releases](https://github.com/Taam-dev/translatorTdev/releases)
2. Download `TranslatorTdev-v1.0.0-windows.zip`
3. Extract and run `TranslatorTdev.exe`

> First launch downloads EasyOCR models (~100 MB). Internet required for this step only.

---

### Option B — Run from Source

#### 1. Clone or download

### Option B: Run from Source
```bash
git clone https://github.com/YOUR_USERNAME/translatorTdev.git
cd translatorTdev

#### 2. Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate

#### 3. Install dependencies

```bash
pip install -r requirements.txt

#### 4. Run

```bash
python main.py
📖 How to Use
text

---

# Lightweight
ollama pull qwen2.5:3b
Settings (settings.json)
JSON

{
  "hotkey": "q",
  "source_language": "en",
  "target_language": "vi",
  "translation_backend": "google",
  "ocr_language": "en",
  "font_size": 16,
  "overlay_opacity": 0.92,
  "overlay_bg_color": "#1a1a2e",
  "overlay_text_color": "#e8e8e8",
  "cache_translations": true
}
📦 Requirements
Windows 10/11 (64-bit)
Python 3.10+ (source only)
~500MB disk space (EasyOCR models)
RAM: 4GB minimum, 8GB recommended
🔧 Troubleshooting
OCR not detecting text?

1. Launch `TranslatorTdev.exe` or `python main.py`
2. Switch to any app containing text (browser, manga viewer, game, etc.)
3. Press **Q** (or your configured hotkey)
4. The screen freezes with a dark overlay
5. **Click and drag** to select the text region
6. Press **Enter** to confirm
7. Wait for OCR + translation (1–5 seconds)
8. The translated text appears as an overlay
9. **Click the overlay** or press **Esc** to dismiss

First run downloads EasyOCR models (~100MB)
Local AI (Ollama) needs model loaded in RAM
Switch to Google Translate for fastest results
App crashes?

Check crash.log in app folder
Make sure you're using the correct Python version
Try reinstalling: pip install -r requirements.txt --force-reinstall
Hotkey not working?

| Key | Action |
|-----|--------|
| `Q` (default) | Activate capture mode |
| Left mouse drag | Select region |
| Enter | Confirm selection → start OCR + translate |
| Escape | Cancel selection / close overlay |
| Click overlay | Dismiss translation overlay |

You can change the capture hotkey in **Settings → Hotkeys**.

---

## Translation Backends

### Google Translate *(Default, Free)*

No setup required. Uses the `deep-translator` library.

- Requires internet connection
- Good quality for most content
- Rate limits may apply for heavy usage

---

### OpenAI GPT *(Best Quality)*

1. Get an API key from https://platform.openai.com/
2. Open Settings → Translation Backend → `OpenAI GPT`
3. Enter your API key in the **API Key** field
4. Select model (`gpt-4o-mini` recommended for speed and cost)

**Recommended:** `gpt-4o-mini` — fast, cheap, excellent translation quality.

---

### Ollama *(Free Local AI — 100% Offline)*

Ollama runs AI models locally on your machine. No internet needed after setup.

#### Step 1 — Install Ollama

Download and install from https://ollama.ai

#### Step 2 — Pull a translation model

Open a terminal and run:

```bash
# Best for Vietnamese / Chinese (recommended)
ollama pull qwen2.5:7b

# Fast, low RAM usage (~4 GB)
ollama pull gemma3:4b

# Lightweight option (~2 GB)
ollama pull qwen2.5:3b
```

> Model download size: 2–9 GB depending on model. Only needed once.

#### Step 3 — Start Ollama server

Ollama starts automatically after installation.
To verify it is running, open a browser and go to:
```
http://localhost:11434
```
You should see: `Ollama is running`

#### Step 4 — Configure TranslatorTdev

1. Open TranslatorTdev
2. Settings → Translation Backend → `Ollama (free local AI)`
3. Set **Ollama Model** to the model you pulled (e.g. `qwen2.5:7b`)
4. Click **Test Backend** to verify connection

> **Important:** Ollama must be running before you use the tool.
> The model must be pulled before selecting it in settings.

#### Recommended models by use case

| Model | Best for | RAM needed | Size |
|-------|----------|------------|------|
| `qwen2.5:7b` | Vietnamese, Chinese, general | 6 GB | 4.7 GB |
| `gemma3:4b` | Fast, low resource | 4 GB | 3.3 GB |
| `qwen2.5:14b` | Highest quality | 16 GB | 9 GB |
| `qwen2.5:3b` | Very low resource | 3 GB | 2 GB |
| `aya:8b` | Multilingual specialist | 8 GB | 5 GB |

---

### LM Studio *(Free Local AI — 100% Offline)*

LM Studio provides a GUI to run GGUF models locally with an OpenAI-compatible API.

#### Step 1 — Install LM Studio

Download from https://lmstudio.ai and install it.

#### Step 2 — Download a model inside LM Studio

1. Open LM Studio
2. Go to the **Discover** tab
3. Search for a model (recommended: `Qwen2.5-7B-Instruct-GGUF`)
4. Click **Download**

#### Step 3 — Start the local server

1. Go to the **Local Server** tab in LM Studio
2. Select your downloaded model
3. Click **Start Server**
4. Server runs at `http://localhost:1234` by default

#### Step 4 — Configure TranslatorTdev

1. Settings → Translation Backend → `LM Studio (free local AI)`
2. Click **Test Backend** to verify

> **Important:** LM Studio server must be running and a model must be loaded
> before using the tool.

---

### llama.cpp Server *(Advanced)*

For advanced users running llama.cpp manually.

```bash
# Start llama.cpp server with your model
llama-server -m your-model.gguf --port 8080 -c 4096
```

Then set backend to `llama.cpp server` in settings.

---

## OCR Setup

The app uses **EasyOCR** as the primary OCR engine, with PaddleOCR as fallback.

### Supported OCR Languages

| Language | Setting Code |
|----------|-------------|
| English | `en` |
| Vietnamese + English | `vi` |
| Chinese (Simplified) | `ch` |
| Japanese | `ja` |
| Korean | `ko` |
| French | `fr` |
| German | `de` |

Set the OCR language in **Settings → OCR Settings** to match your source content.

### First Run

On first use, EasyOCR downloads recognition models (~100 MB).
Files are cached in `%USERPROFILE%\.EasyOCR\`.

---

## OCR Text Reconstruction

The app intelligently reconstructs broken OCR output:

### Hyphen Split Repair
```
beauti-     →    beautiful
ful
```

### Broken Line Merging
```
I           →    I can't do this anymore...
can't
do this
anymore...
```

### Common OCR Error Correction
```
l can't     →    I can't
d0 this     →    do this
rn aybe     →    maybe
```

---

## Settings Reference

All settings are saved automatically to `settings.json`.

| Setting | Default | Description |
|---------|---------|-------------|
| `source_language` | `en` | Language of text on screen |
| `target_language` | `vi` | Language to translate into |
| `hotkey` | `q` | Global capture hotkey |
| `font_size` | `16` | Overlay font size (pt) |
| `overlay_opacity` | `0.92` | Overlay opacity (0.3–1.0) |
| `translation_backend` | `google` | Active backend |
| `translation_style` | `novel` | `novel` / `manga` / `subtitle` / `general` |
| `openai_api_key` | `""` | OpenAI API key |
| `openai_model` | `gpt-4o-mini` | OpenAI model |
| `ollama_host` | `http://localhost:11434` | Ollama server URL |
| `ollama_model` | `qwen2.5:7b` | Ollama model name |
| `lmstudio_host` | `http://localhost:1234` | LM Studio server URL |
| `ocr_language` | `en` | OCR recognition language |
| `cache_translations` | `true` | Cache results locally |
| `cleanup_with_ai` | `false` | Use AI to fix OCR errors |
| `max_cache_size` | `500` | Max cached translations |

---

## Troubleshooting

### App doesn't start
- Ensure Python 3.10+ is installed
- Run `pip install -r requirements.txt` again
- Check for import errors: `python -c "import PySide6; import easyocr"`

### Hotkey not working
- Run the app as Administrator
- Try a different hotkey in Settings
- Check if another app is consuming the same hotkey

### OCR is slow
- First run initializes EasyOCR and downloads models
- Subsequent runs are faster (1–3 seconds)
- EasyOCR runs on CPU by default for compatibility

### OCR quality is poor
- Select a larger region with clearer text
- Match the OCR language to the text on screen
- Enable **AI OCR Cleanup** in settings (requires OpenAI key)

### Ollama not connecting
- Make sure Ollama is installed and running
- Open `http://localhost:11434` in a browser — should show `Ollama is running`
- Make sure you have pulled the model: `ollama pull qwen2.5:7b`
- Click **Test Backend** in settings to diagnose

### LM Studio not connecting
- Make sure LM Studio is open and the **Local Server** is started
- A model must be loaded in the server tab before connecting
- Check that the server port matches (`1234` by default)

### Translation overlay not showing
- Make sure the selected region contains readable text
- Check the log panel in the settings window for error details
- Try switching to Google Translate to isolate if it is an OCR or translation issue

### Vietnamese characters not rendering
- The app uses Segoe UI which supports Vietnamese on Windows 10/11
- Ensure Windows has Vietnamese language support installed

---

## Project Structure

```
translatorTdev/
├── main.py                  # Entry point & app controller
├── renderer.py              # Async OCR → Translate pipeline
├── ocr.py                   # OCR engine (EasyOCR / PaddleOCR)
├── capture.py               # Screen capture (mss)
├── overlay.py               # Translation overlay window
├── translator.py            # All translation backends
├── cleanup.py               # OCR text reconstruction
├── hotkeys.py               # Global hotkey manager (pynput)
├── settings.py              # Settings load / save
├── ui/
│   ├── main_window.py       # Main settings window
│   ├── selection_window.py  # Fullscreen region selector
│   └── local_ai_dialog.py   # Local AI setup dialog
├── assets/                  # Icons and background images
├── cache/                   # Local translation cache
└── requirements.txt         # Python dependencies
```

Fork the repo
Create feature branch: git checkout -b feature/amazing-feature
Commit: git commit -m 'Add amazing feature'
Push: git push origin feature/amazing-feature
Open Pull Request
📄 License
MIT License — see LICENSE for details.

## Architecture Notes

- **Thread safety:** OCR and translation run in a background thread. Qt signals with `QueuedConnection` handle all UI updates from background threads safely.
- **No continuous OCR:** OCR only runs when the user explicitly captures a region. Zero background CPU usage.
- **Lazy initialization:** EasyOCR initializes only on first use to keep startup fast.
- **Persistent cache:** Translation cache survives between sessions.

---

## Changelog

### v1.0.0
- 🎉 Initial public release
- ✅ EasyOCR as primary engine with PaddleOCR fallback
- ✅ 5 translation backends (Google, OpenAI, Ollama, LM Studio, llama.cpp)
- ✅ Thread-safe pipeline — no UI freezes or crashes
- ✅ Configurable overlay (font, opacity, colors)
- ✅ Persistent translation cache
- ✅ Global hotkey via pynput
- ✅ Minimize to system tray

---

## License

MIT License. Free to use and modify.
