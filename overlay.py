"""
overlay.py
----------
The translation result overlay window.

Renders translated text over the selected screen region.
Features:
- Transparent click-through (pass mouse events to windows below)
- Always-on-top positioning
- Adjustable opacity
- Auto-wrapping text
- Vietnamese accent support
- Non-blocking rendering
"""

from PySide6.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QRect, QTimer, Signal, QPoint
from PySide6.QtGui import (
    QPainter, QColor, QFont, QFontMetrics, QPen, QBrush,
    QPainterPath, QLinearGradient
)
from settings import settings
import math


class TranslationOverlay(QWidget):
    """
    Always-on-top transparent overlay that renders translated text
    directly on screen over the selected region.

    Supports:
    - Click-through (mouse passes to underlying windows)
    - Adjustable opacity
    - Auto-fit text
    - Vietnamese/Unicode text rendering
    - Close on click or timeout
    """

    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._region: QRect = QRect()
        self._paragraphs: list[str] = []
        self._font_size: int = settings.get("font_size", 16)
        self._opacity: float = settings.get("overlay_opacity", 0.92)
        self._bg_color = QColor(settings.get("overlay_bg_color", "#1a1a2e"))
        self._text_color = QColor(settings.get("overlay_text_color", "#e8e8e8"))

        # Auto-close timer (0 = never auto-close)
        self._auto_close_timer = QTimer(self)
        self._auto_close_timer.setSingleShot(True)
        self._auto_close_timer.timeout.connect(self._close_overlay)

        self._setup_window()

    def _setup_window(self):
        """Configure overlay window properties."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setWindowOpacity(self._opacity)

    def show_translation(
        self,
        region: QRect,
        paragraphs: list[str],
        auto_close_ms: int = 0
    ):
        """
        Display translated text over the specified screen region.

        Args:
            region: Screen region where original text was (QRect)
            paragraphs: List of translated paragraph strings
            auto_close_ms: Auto-close after N milliseconds (0 = never)
        """
        self._region = region
        self._paragraphs = paragraphs
        self._font_size = settings.get("font_size", 16)
        self._opacity = settings.get("overlay_opacity", 0.92)
        self._bg_color = QColor(settings.get("overlay_bg_color", "#1a1a2e"))
        self._text_color = QColor(settings.get("overlay_text_color", "#e8e8e8"))

        # Position and size overlay to cover the selected region
        # Add some padding
        padding = 8
        self.setGeometry(
            region.x() - padding,
            region.y() - padding,
            region.width() + padding * 2,
            region.height() + padding * 2
        )

        self.setWindowOpacity(self._opacity)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        self.show()
        self.raise_()
        self.update()

        if auto_close_ms > 0:
            self._auto_close_timer.start(auto_close_ms)

    def paintEvent(self, event):
        """Custom paint: draw background + translated text."""
        if not self._paragraphs:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        rect = self.rect()

        # Draw background with rounded corners
        painter.save()
        path = QPainterPath()
        path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), 6, 6)

        # Background color with opacity
        bg = QColor(self._bg_color)
        painter.fillPath(path, bg)

        # Subtle border
        painter.setPen(QPen(QColor(80, 80, 120, 180), 1))
        painter.drawPath(path)
        painter.restore()

        # Draw translated text
        self._draw_text(painter, rect)

        painter.end()

    def _draw_text(self, painter: QPainter, rect: QRect):
        """
        Draw translated paragraphs with auto-sizing font.

        Tries to fit all text within the overlay region.
        Reduces font size if text overflows.
        """
        if not self._paragraphs:
            return

        padding = 12
        text_rect = rect.adjusted(padding, padding, -padding, -padding)

        full_text = "\n\n".join(self._paragraphs)

        # Auto-fit: try to find the right font size
        font_size = self._font_size
        min_font_size = 9

        while font_size >= min_font_size:
            font = self._make_font(font_size)
            painter.setFont(font)
            fm = QFontMetrics(font)

            # Calculate required height for text with word wrap
            bounding = fm.boundingRect(
                text_rect,
                Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignLeft,
                full_text
            )

            if bounding.height() <= text_rect.height():
                break  # Text fits at this size
            font_size -= 1

        # Draw the text
        font = self._make_font(font_size)
        painter.setFont(font)
        painter.setPen(QPen(self._text_color))
        painter.drawText(
            text_rect,
            Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            full_text
        )

    def _make_font(self, size: int) -> QFont:
        """Create a font suitable for translated text (supports Vietnamese)."""
        # Font stack: prefer fonts with good Vietnamese/Unicode support
        font_families = [
            "Segoe UI",
            "Arial Unicode MS",
            "Noto Sans",
            "Liberation Sans",
            "DejaVu Sans",
            "Arial",
        ]
        font = QFont()
        font.setFamilies(font_families)
        font.setPointSize(size)
        font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
        return font

    def mousePressEvent(self, event):
        """Close overlay on click."""
        self._close_overlay()

    def keyPressEvent(self, event):
        """Close overlay on Escape."""
        if event.key() == Qt.Key.Key_Escape:
            self._close_overlay()
        else:
            super().keyPressEvent(event)

    def _close_overlay(self):
        """Hide and emit closed signal."""
        self._auto_close_timer.stop()
        self.hide()
        self.closed.emit()

    def update_settings(self):
        """Reload settings (call when settings change)."""
        self._font_size = settings.get("font_size", 16)
        self._opacity = settings.get("overlay_opacity", 0.92)
        self._bg_color = QColor(settings.get("overlay_bg_color", "#1a1a2e"))
        self._text_color = QColor(settings.get("overlay_text_color", "#e8e8e8"))
        self.setWindowOpacity(self._opacity)
        self.update()