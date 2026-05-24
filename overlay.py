"""
overlay.py
----------
The translation result overlay window.
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QFont, QFontMetrics, QPen, QPainterPath
from settings import settings


class TranslationOverlay(QWidget):
    """
    Always-on-top transparent overlay that renders translated text
    directly on screen over the selected region.
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

        self._auto_close_timer = QTimer(self)
        self._auto_close_timer.setSingleShot(True)
        self._auto_close_timer.timeout.connect(self._close_overlay)

        self._setup_window()

    def _setup_window(self):
        """Configure overlay window properties."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        # Mặc định: click-through (không chặn mouse)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setWindowOpacity(self._opacity)

    def show_translation(
        self, region: QRect, paragraphs: list[str], auto_close_ms: int = 0
    ):
        """Display translated text over the specified screen region."""
        # Validate input
        if not paragraphs or not any(p.strip() for p in paragraphs):
            print("[Overlay] No valid paragraphs to display")
            return

        self._region = region
        # Lọc paragraphs rỗng
        self._paragraphs = [p for p in paragraphs if p and p.strip()]

        # Reload settings
        self._font_size = settings.get("font_size", 16)
        self._opacity = settings.get("overlay_opacity", 0.92)
        self._bg_color = QColor(settings.get("overlay_bg_color", "#1a1a2e"))
        self._text_color = QColor(settings.get("overlay_text_color", "#e8e8e8"))

        # Positioning với padding
        padding = 8
        self.setGeometry(
            region.x() - padding,
            region.y() - padding,
            region.width() + padding * 2,
            region.height() + padding * 2,
        )

        self.setWindowOpacity(self._opacity)

        # BẬT mouse events để user có thể click đóng overlay
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

        # Background với rounded corners
        path = QPainterPath()
        path.addRoundedRect(
            float(rect.x()),
            float(rect.y()),
            float(rect.width()),
            float(rect.height()),
            6.0,
            6.0,
        )

        bg = QColor(self._bg_color)
        painter.fillPath(path, bg)

        # Border
        painter.setPen(QPen(QColor(80, 80, 120, 180), 1))
        painter.drawPath(path)

        # Text
        self._draw_text(painter, rect)

        painter.end()

    def _draw_text(self, painter: QPainter, rect: QRect):
        """Draw translated paragraphs với auto-sizing font."""
        if not self._paragraphs:
            return

        padding = 12
        text_rect = rect.adjusted(padding, padding, -padding, -padding)
        full_text = "\n\n".join(self._paragraphs)

        font_size = self._font_size
        min_font_size = 8

        # Auto-fit: giảm font cho đến khi text vừa
        while font_size >= min_font_size:
            font = self._make_font(font_size)
            fm = QFontMetrics(font)

            bounding = fm.boundingRect(
                text_rect,
                Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignLeft,
                full_text,
            )

            if bounding.height() <= text_rect.height():
                break
            font_size -= 1

        font = self._make_font(font_size)
        painter.setFont(font)
        painter.setPen(QPen(self._text_color))
        painter.drawText(
            text_rect,
            Qt.TextFlag.TextWordWrap
            | Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignTop,
            full_text,
        )

    def _make_font(self, size: int) -> QFont:
        """Font với Vietnamese/Unicode support."""
        font = QFont()
        font.setFamilies(
            [
                "Segoe UI",
                "Arial Unicode MS",
                "Noto Sans",
                "Liberation Sans",
                "DejaVu Sans",
                "Arial",
            ]
        )
        font.setPointSize(max(size, 8))  # Không cho nhỏ hơn 8pt
        font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
        return font

    def mousePressEvent(self, event):
        """Click để đóng overlay."""
        self._close_overlay()

    def keyPressEvent(self, event):
        """Escape để đóng overlay."""
        if event.key() == Qt.Key.Key_Escape:
            self._close_overlay()
        else:
            super().keyPressEvent(event)

    def _close_overlay(self):
        """Hide và emit closed signal."""
        self._auto_close_timer.stop()
        # Reset về click-through sau khi đóng
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.hide()
        self.closed.emit()

    def update_settings(self):
        """Reload settings (gọi khi settings thay đổi)."""
        self._font_size = settings.get("font_size", 16)
        self._opacity = settings.get("overlay_opacity", 0.92)
        self._bg_color = QColor(settings.get("overlay_bg_color", "#1a1a2e"))
        self._text_color = QColor(settings.get("overlay_text_color", "#e8e8e8"))
        self.setWindowOpacity(self._opacity)
        if self.isVisible():
            self.update()
