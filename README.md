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

- 🖱️ **Hotkey trigger** — Press a configurable key to start capture
- 🔲 **Region selection** — Drag to select any area on screen  
- 🔍 **OCR** — Powered by EasyOCR (works offline after first run)
- 🌏 **Multiple translation backends:**
  - Google Translate *(free, online)*
  - OpenAI GPT-4o *(best quality, paid)*
  - Ollama *(free, local AI — 100% offline)*
  - LM Studio *(free, local AI — 100% offline)*
  - llama.cpp server *(advanced local AI)*
- 📝 **Overlay display** — Translation shown directly over selected region
- 💾 **Translation cache** — Avoid re-translating same text
- ⚙️ **Configurable** — Font size, opacity, colors, hotkey, languages

---

## 🚀 Quick Start

### Option A: Download Release (Recommended)
1. Go to [Releases](https://github.com/Taam-dev/translatorTdev/releases)
2. Download `TranslatorTdev-v1.0.0-windows.zip`
3. Extract and run `TranslatorTdev.exe`
4. No Python installation needed!

### Option B: Run from Source
```bash
# Clone repo
git clone https://github.com/Taam-dev/translatorTdev.git
cd translatorTdev

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
📖 How to Use
text

1. Launch TranslatorTdev
2. Press the hotkey (default: Q) or click "Capture"
3. Drag to select the screen region containing text
4. Press ENTER to confirm selection
5. Wait for OCR + Translation (1-5 seconds)
6. Read the translation overlay
7. Click overlay or press ESC to dismiss
⚙️ Configuration
Translation Backends
Backend	Quality	Cost	Internet	Setup
Google Translate	⭐⭐⭐	Free	Required	None
OpenAI GPT-4o	⭐⭐⭐⭐⭐	Paid	Required	API Key
Ollama	⭐⭐⭐⭐	Free	After setup	Install Ollama
LM Studio	⭐⭐⭐⭐	Free	After setup	Install LM Studio
llama.cpp	⭐⭐⭐⭐	Free	After setup	Manual setup
Recommended Models (Ollama)
Bash

# Best for Vietnamese/Chinese translation
ollama pull qwen2.5:7b

# Fast, low RAM
ollama pull gemma3:4b

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

Select a larger region
Make sure text is clear and not too small
Check OCR language matches screen text language
Translation is slow?

First run downloads EasyOCR models (~100MB)
Local AI (Ollama) needs model loaded in RAM
Switch to Google Translate for fastest results
App crashes?

Check crash.log in app folder
Make sure you're using the correct Python version
Try reinstalling: pip install -r requirements.txt --force-reinstall
Hotkey not working?

Try running as Administrator
Change hotkey in Settings (avoid conflict with other apps)
🏗️ Project Structure
text

translatorTdev/
├── main.py              # Entry point & app controller
├── renderer.py          # Async OCR→Translate pipeline
├── ocr.py               # OCR engine (EasyOCR/PaddleOCR)
├── capture.py           # Screen capture
├── overlay.py           # Translation overlay window
├── translator.py        # Translation backends
├── cleanup.py           # OCR text reconstruction
├── hotkeys.py           # Global hotkey manager
├── settings.py          # Settings management
├── ui/
│   ├── main_window.py   # Main UI window
│   ├── selection_window.py  # Region selection overlay
│   └── local_ai_dialog.py   # Local AI setup dialog
├── assets/              # Icons and images
└── cache/               # Translation cache
📋 Changelog
v1.0.0 (2025-01-xx)
🎉 Initial release
✅ EasyOCR integration
✅ 5 translation backends
✅ Configurable overlay
✅ Translation cache
✅ Global hotkey support
🤝 Contributing
Pull requests welcome!

Fork the repo
Create feature branch: git checkout -b feature/amazing-feature
Commit: git commit -m 'Add amazing feature'
Push: git push origin feature/amazing-feature
Open Pull Request
📄 License
MIT License — see LICENSE for details.

