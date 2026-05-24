# translatorTdev

A fast, minimal OCR screen translator overlay for Windows.

Designed for reading English web novels, manga, manhwa, comics, games, and subtitles.

---

## Features

- **Global hotkey** capture (works in any app, any window)
- **Screen freeze + drag selection** for precise region capture
- **PaddleOCR** for accurate text extraction
- **Intelligent OCR reconstruction** - fixes broken lines, hyphen splits, OCR errors
- **Natural translation** via Google Translate (free) or OpenAI GPT
- **Translation overlay** renders directly on screen over the selected region
- **Local translation cache** for speed and offline repeat translations
- **Dark minimal UI** - developer tool aesthetic
- **Vietnamese accent support**
- **Auto-fit text** in overlay

---

## Requirements

- Windows 10 or 11
- Python 3.12+
- Internet connection (for translation)

---

## Installation

### 1. Clone or download

```bash
git clone https://github.com/yourname/translatorTdev.git
cd translatorTdev
```

### 2. Create virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note on PaddlePaddle:** If the standard install fails on Windows, try:
> ```bash
> pip install paddlepaddle -f https://www.paddlepaddle.org.cn/whl/windows/mkl/avx/stable.html
> pip install paddleocr
> ```

---

## Running the App

```bash
python main.py
```

The app launches with a small settings window and registers a global hotkey.

On first launch, PaddleOCR will download model files (~100MB). This only happens once.

---

## Usage

### Basic Workflow

1. Launch `python main.py`
2. Switch to any app containing text (browser, manga viewer, game, etc.)
3. Press **Q** (or your configured hotkey)
4. The screen freezes with a dark overlay
5. **Click and drag** to select the text region
6. Press **Enter** to confirm
7. Wait for OCR (~1-3 seconds)
8. The translated text appears as an overlay
9. **Click the overlay** or press **ESC** to dismiss

---

## Hotkeys

| Key | Action |
|-----|--------|
| Q (default) | Activate capture mode |
| Drag (left mouse) | Select region |
| Enter | Confirm selection + start OCR |
| Escape | Cancel selection / close overlay |
| Click overlay | Dismiss translation overlay |

You can change the capture hotkey in Settings → Hotkeys.

---

## OCR Setup

The app uses **PaddleOCR** for text recognition.

### Supported OCR Languages

| Language | Setting Code |
|----------|-------------|
| English | `en` |
| Chinese (Simplified) | `ch` |
| Japanese | `japan` |
| Korean | `korean` |
| French | `french` |
| German | `german` |

Set the OCR language in Settings → OCR Settings to match your source content.

### First Run

On first use, PaddleOCR downloads recognition models. Ensure you have internet access.
Files are cached in `~/.paddleocr/`.

---

## Translation Setup

### Option 1: Google Translate (Default, Free)

No setup required. Uses `deep-translator` library.

Set **Translation Backend** to `Google Translate (Free)` in settings.

**Limitations:**
- Rate limits apply for heavy usage
- Quality is good but not as natural as GPT

### Option 2: OpenAI GPT (Best Quality)

For novel-quality, natural translations:

1. Get an API key from https://platform.openai.com/
2. Open Settings → Translation Backend → `OpenAI GPT`
3. Enter your API key in the **API Key** field
4. Select model (`gpt-4o-mini` recommended for speed/cost)

**Recommended model:** `gpt-4o-mini`
- Fast, cheap, excellent translation quality
- ~$0.0001 per translation (very low cost)

### Translation Cache

Translations are cached locally in `cache/translation_cache.json`.

- Same text is never translated twice
- Works offline for previously seen text
- Cache holds up to 500 entries (configurable in `settings.py`)

---

## Settings Reference

All settings saved to `settings.json` in the app directory.

| Setting | Default | Description |
|---------|---------|-------------|
| `source_language` | `en` | Source language code |
| `target_language` | `vi` | Target language code |
| `hotkey` | `q` | Global capture hotkey |
| `font_size` | `16` | Overlay text font size (pt) |
| `overlay_opacity` | `0.92` | Overlay window opacity (0.3-1.0) |
| `translation_backend` | `google` | `google` or `openai` |
| `openai_api_key` | `""` | OpenAI API key |
| `openai_model` | `gpt-4o-mini` | OpenAI model name |
| `ocr_language` | `en` | PaddleOCR language |
| `cache_translations` | `true` | Cache results locally |
| `cleanup_with_ai` | `false` | Use AI to fix OCR errors |
| `max_cache_size` | `500` | Max cached translations |

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
I           →    I can't do this
can't              anymore...
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

## Troubleshooting

### App doesn't start
- Ensure Python 3.12+ is installed
- Run `pip install -r requirements.txt` again
- Check for import errors: `python -c "import PySide6; import paddleocr"`

### Hotkey not working
- Run the app as Administrator (some apps block hotkeys)
- Try a different hotkey in Settings
- Check if another app is consuming the same hotkey

### OCR is slow
- First run initializes PaddleOCR (~5-10 seconds)
- Subsequent runs are faster (~1-3 seconds)
- PaddleOCR runs on CPU by default for compatibility

### OCR quality is poor
- Try selecting a larger region
- Ensure text is readable (not too small, not blurry)
- Try the `AI OCR Cleanup` option with an OpenAI key

### Translation not working
- Check internet connection (Google backend needs internet)
- Verify OpenAI API key is correct (if using OpenAI backend)
- Check the status bar for error messages

### Overlay text is too small/large
- Adjust **Font Size** in Settings
- The overlay auto-shrinks text if it doesn't fit

### PaddleOCR installation fails
```bash
# Try CPU-only version explicitly
pip install paddlepaddle==2.5.0 -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install paddleocr
```

### Vietnamese characters not rendering
- The app uses Segoe UI which supports Vietnamese on Windows 10/11
- Ensure Windows has Vietnamese language support installed

---

## Building Executable (.exe)

### Install PyInstaller

```bash
pip install pyinstaller
```

### Build Command

```bash
pyinstaller ^
  --onefile ^
  --windowed ^
  --name translatorTdev ^
  --add-data "settings.json;." ^
  --hidden-import paddleocr ^
  --hidden-import paddle ^
  --hidden-import pynput ^
  --hidden-import deep_translator ^
  main.py
```

### Output

The executable will be in `dist/translatorTdev.exe`.

### Portable Distribution

Copy the following to a distribution folder:
```
dist/translatorTdev.exe
cache/  (empty directory)
README.md
```

---

## Project Structure

```
translatorTdev/
├── main.py           # App entry point, orchestration
├── overlay.py        # Translation overlay window
├── capture.py        # Screen capture (mss)
├── ocr.py            # PaddleOCR wrapper
├── cleanup.py        # OCR text reconstruction + AI cleanup
├── translator.py     # Translation backends + caching
├── renderer.py       # Async pipeline worker
├── settings.py       # Settings management
├── hotkeys.py        # Global hotkey listener
├── ui/
│   ├── __init__.py
│   ├── main_window.py       # Settings window
│   └── selection_window.py  # Screen freeze + region selector
├── cache/
│   └── translation_cache.json  (auto-created)
├── settings.json       (auto-created on first run)
├── requirements.txt
└── README.md
```

---

## Architecture Notes

- **Thread safety:** OCR and translation run in a background thread. Qt signals/slots (QueuedConnection) are used for all UI updates from the background thread.
- **No continuous OCR:** OCR only runs when user explicitly captures a region. Zero background CPU usage.
- **Lazy initialization:** PaddleOCR initializes only on first use to keep startup fast.
- **Cache:** Translation cache persists between sessions.

---

## License

MIT License. Free to use and modify.