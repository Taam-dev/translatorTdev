"""
ui/selection_window.py
----------------------
The screen freeze and region selection overlay window.

When activated:
1. Takes a screenshot of the full screen
2. Shows it as a frozen overlay
3. Allows user to drag-select a rectangle
4. Returns the selected region on Enter
5. Cancels on Escape
"""

from PySide6.QtWidgets import QWidget, QApplication, QRubberBand
from PySide6.QtCore import (
    Qt, QRect, QPoint, QSize, Signal, QTimer
)
from PySide6.QtGui import (
    QPainter, QPixmap, QColor, QFont, QPen, QBrush, QScreen, QCursor
)
import sys


class SelectionWindow(QWidget):
    """
    Full-screen overlay window for region selection.

    Signals:
        region_selected(x, y, width, height): Emitted when user confirms selection
        selection_cancelled(): Emitted when user presses Escape
    """

    region_selected = Signal(int, int, int, int)
    selection_cancelled = Signal()

    def __init__(self, screenshot: QPixmap, parent=None):
        super().__init__(parent)

        self._screenshot = screenshot
        self._start_point = QPoint()
        self._end_point = QPoint()
        self._selecting = False
        self._selection_rect = QRect()
        self._confirmed = False

        self._setup_window()
        self._setup_ui()

    def _setup_window(self):
        """Configure the window to be a full-screen overlay."""
        # Get the full virtual desktop geometry (all monitors)
        screen = QApplication.primaryScreen()
        geometry = screen.virtualGeometry()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setGeometry(geometry)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

    def _setup_ui(self):
        """No child widgets needed - everything drawn in paintEvent."""
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def showEvent(self, event):
        """Ensure we receive keyboard events."""
        super().showEvent(event)
        self.setFocus()
        self.activateWindow()
        self.raise_()

    def paintEvent(self, event):
        """Paint the frozen screenshot with dark overlay and selection rectangle."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw the frozen screenshot as background
        painter.drawPixmap(0, 0, self._screenshot)

        # Draw dark semi-transparent overlay over entire screen
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

        # Draw instruction text
        self._draw_instructions(painter)

        # If actively selecting or selection made, draw the rectangle
        if not self._selection_rect.isNull() and self._selection_rect.isValid():
            self._draw_selection(painter)

    def _draw_instructions(self, painter: QPainter):
        """Draw user instruction text at top of screen."""
        painter.save()

        # Background for instructions
        instruction_rect = QRect(0, 0, self.width(), 40)
        painter.fillRect(instruction_rect, QColor(20, 20, 30, 200))

        # Instruction text
        painter.setPen(QColor(200, 200, 200))
        font = QFont("Segoe UI", 11)
        painter.setFont(font)

        if self._selection_rect.isNull() or not self._selection_rect.isValid():
            text = "Drag to select region  |  ENTER: Confirm  |  ESC: Cancel"
        else:
            w = abs(self._selection_rect.width())
            h = abs(self._selection_rect.height())
            text = (
                f"Selection: {w}x{h}px  |  "
                "ENTER: Translate  |  ESC: Cancel  |  Drag again to reselect"
            )

        painter.drawText(
            instruction_rect,
            Qt.AlignmentFlag.AlignCenter,
            text
        )
        painter.restore()

    def _draw_selection(self, painter: QPainter):
        """Draw the selection rectangle with handles."""
        painter.save()

        rect = self._selection_rect.normalized()

        # Clear the overlay inside selection (show original screenshot)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(rect, QColor(0, 0, 0, 0))
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        # Redraw screenshot in selection area (clear view)
        painter.drawPixmap(rect, self._screenshot, rect)

        # Draw selection border
        pen = QPen(QColor(100, 180, 255), 2, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.drawRect(rect)

        # Draw corner handles
        handle_size = 8
        handle_color = QColor(100, 180, 255)
        painter.setBrush(QBrush(handle_color))
        painter.setPen(Qt.PenStyle.NoPen)

        corners = [
            rect.topLeft(), rect.topRight(),
            rect.bottomLeft(), rect.bottomRight()
        ]
        for corner in corners:
            painter.drawRect(
                corner.x() - handle_size // 2,
                corner.y() - handle_size // 2,
                handle_size, handle_size
            )

        painter.restore()

    def mousePressEvent(self, event):
        """Start selection on left mouse button press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_point = event.position().toPoint()
            self._end_point = self._start_point
            self._selecting = True
            self._selection_rect = QRect(self._start_point, self._end_point)
            self.update()

    def mouseMoveEvent(self, event):
        """Update selection rectangle while dragging."""
        if self._selecting:
            self._end_point = event.position().toPoint()
            self._selection_rect = QRect(self._start_point, self._end_point)
            self.update()

    def mouseReleaseEvent(self, event):
        """Finalize rectangle on mouse release."""
        if event.button() == Qt.MouseButton.LeftButton and self._selecting:
            self._end_point = event.position().toPoint()
            self._selection_rect = QRect(
                self._start_point, self._end_point
            ).normalized()
            self._selecting = False
            self.update()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self._confirm_selection()
        elif event.key() == Qt.Key.Key_Escape:
            self._cancel_selection()
        else:
            super().keyPressEvent(event)

    def _confirm_selection(self):
        """Confirm the current selection and emit signal."""
        if self._selection_rect.isNull() or not self._selection_rect.isValid():
            return

        rect = self._selection_rect.normalized()

        if rect.width() < 10 or rect.height() < 10:
            return  # Too small, ignore

        self._confirmed = True
        self.hide()

        # Emit the selected region coordinates
        self.region_selected.emit(
            rect.x(), rect.y(),
            rect.width(), rect.height()
        )
        self.close()

    def _cancel_selection(self):
        """Cancel selection and close window."""
        self.hide()
        self.selection_cancelled.emit()
        self.close()


def take_qt_screenshot() -> QPixmap:
    """
    Capture the entire virtual screen as a QPixmap.
    Uses Qt's screen grab for compatibility.

    Returns:
        QPixmap of the full screen
    """
    screen = QApplication.primaryScreen()
    # Grab the entire virtual desktop
    virtual_geo = screen.virtualGeometry()
    pixmap = screen.grabWindow(
        0,
        virtual_geo.x(),
        virtual_geo.y(),
        virtual_geo.width(),
        virtual_geo.height()
    )
    return pixmap