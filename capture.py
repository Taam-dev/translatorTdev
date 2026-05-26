"""
capture.py
----------
Handles screen capture using mss.
Captures only the user-selected region to minimize CPU usage.
"""

import mss
import mss.tools
import numpy as np
from PIL import Image


def capture_region(x: int, y: int, width: int, height: int) -> Image.Image:
    """
    Capture a specific screen region and return as PIL Image.

    Args:
        x: Left coordinate of the region
        y: Top coordinate of the region
        width: Width of the region
        height: Height of the region

    Returns:
        PIL Image of the captured region
    """
    if width <= 0 or height <= 0:
        raise ValueError(f"Invalid capture dimensions: {width}x{height}")

    monitor = {
        "top": y,
        "left": x,
        "width": width,
        "height": height,
    }

    with mss.mss() as sct:
        screenshot = sct.grab(monitor)
        # Convert mss screenshot to PIL Image
        img = Image.frombytes(
            "RGB", (screenshot.width, screenshot.height), screenshot.rgb
        )

    return img


def capture_full_screen(monitor_index: int = 1) -> Image.Image:
    """
    Capture the full screen (used for freeze effect).

    Args:
        monitor_index: Monitor to capture (1 = primary)

    Returns:
        PIL Image of the full screen
    """
    with mss.mss() as sct:
        monitor = sct.monitors[monitor_index]
        screenshot = sct.grab(monitor)
        img = Image.frombytes(
            "RGB", (screenshot.width, screenshot.height), screenshot.rgb
        )
    return img


def pil_to_numpy(img: Image.Image) -> np.ndarray:
    """Convert PIL Image to numpy array (for PaddleOCR)."""
    return np.array(img)


def get_primary_monitor_size() -> tuple[int, int]:
    """Return (width, height) of the primary monitor."""
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        return monitor["width"], monitor["height"]
