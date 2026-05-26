"""
ui/selection_window.py
----------------------
Screen freeze và region selection overlay window.
"""

from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QRect, QPoint, Signal, QTimer
from PySide6.QtGui import QPainter, QPixmap, QColor, QFont, QPen, QBrush, QCursor


class SelectionWindow(QWidget):
    """
    Full-screen overlay cho phép user kéo chọn vùng màn hình.

    Signals:
        region_selected(x, y, w, h): User xác nhận vùng chọn
        selection_cancelled():       User nhấn Escape
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

        # Flag chống double-emit
        self._signal_emitted = False

        self._setup_window()

    def _setup_window(self):
        """Configure full-screen overlay window."""
        screen = QApplication.primaryScreen()
        geometry = screen.virtualGeometry()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.X11BypassWindowManagerHint
        )

        # QUAN TRỌNG: KHÔNG dùng WA_DeleteOnClose
        # vì main.py cần giữ reference để cleanup đúng cách
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        self.setGeometry(geometry)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    # --------------------------------------------------
    # EVENTS
    # --------------------------------------------------

    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus()
        self.activateWindow()
        self.raise_()

    def closeEvent(self, event):
        """Override để không bị xóa bất ngờ."""
        # Chỉ cho phép close sau khi signal đã emit xong
        event.accept()

    def paintEvent(self, event):
        """Vẽ screenshot + overlay tối + selection rect."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Background: frozen screenshot
        painter.drawPixmap(0, 0, self._screenshot)

        # 2. Dark overlay toàn màn hình
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

        # 3. Instruction bar
        self._draw_instructions(painter)

        # 4. Selection rectangle (nếu có)
        if self._selection_rect.isValid() and not self._selection_rect.isNull():
            self._draw_selection(painter)

        painter.end()

    def _draw_instructions(self, painter: QPainter):
        """Vẽ thanh hướng dẫn phía trên."""
        bar = QRect(0, 0, self.width(), 40)
        painter.fillRect(bar, QColor(20, 20, 30, 200))

        painter.setPen(QColor(200, 200, 200))
        painter.setFont(QFont("Segoe UI", 11))

        if not self._selection_rect.isValid():
            text = "Kéo để chọn vùng  |  ENTER: Dịch  |  ESC: Huỷ"
        else:
            w = self._selection_rect.normalized().width()
            h = self._selection_rect.normalized().height()
            text = (
                f"Đã chọn: {w}×{h}px  |  "
                "ENTER: Dịch  |  ESC: Huỷ  |  Kéo lại để chọn lại"
            )

        painter.drawText(bar, Qt.AlignmentFlag.AlignCenter, text)

    def _draw_selection(self, painter: QPainter):
        """Vẽ selection rectangle với viền sáng."""
        rect = self._selection_rect.normalized()

        # Xoá overlay tối trong vùng chọn → thấy rõ nội dung gốc
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(rect, QColor(0, 0, 0, 0))

        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        # Redraw screenshot trong vùng chọn
        painter.drawPixmap(rect, self._screenshot, rect)

        # Viền xanh
        painter.setPen(QPen(QColor(100, 180, 255), 2, Qt.PenStyle.SolidLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)

        # Corner handles
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(100, 180, 255)))
        sz = 8
        for corner in [
            rect.topLeft(),
            rect.topRight(),
            rect.bottomLeft(),
            rect.bottomRight(),
        ]:
            painter.drawRect(corner.x() - sz // 2, corner.y() - sz // 2, sz, sz)

    # --------------------------------------------------
    # MOUSE
    # --------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_point = event.position().toPoint()
            self._end_point = self._start_point
            self._selecting = True
            self._selection_rect = QRect(self._start_point, self._end_point)
            self.update()

    def mouseMoveEvent(self, event):
        if self._selecting:
            self._end_point = event.position().toPoint()
            self._selection_rect = QRect(self._start_point, self._end_point)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._selecting:
            self._end_point = event.position().toPoint()
            self._selection_rect = QRect(
                self._start_point, self._end_point
            ).normalized()
            self._selecting = False
            self.update()

    # --------------------------------------------------
    # KEYBOARD
    # --------------------------------------------------

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._confirm_selection()
        elif key == Qt.Key.Key_Escape:
            self._cancel_selection()
        else:
            super().keyPressEvent(event)

    # --------------------------------------------------
    # ACTIONS
    # --------------------------------------------------

    def _confirm_selection(self):
        """Xác nhận vùng chọn."""
        # Chống double-emit
        if self._signal_emitted:
            return

        if not self._selection_rect.isValid():
            return

        rect = self._selection_rect.normalized()

        # Vùng quá nhỏ → bỏ qua
        if rect.width() < 10 or rect.height() < 10:
            return

        self._signal_emitted = True

        # 1. Ẩn window TRƯỚC
        self.hide()

        # 2. Emit signal SAU KHI đã ẩn
        # Dùng QTimer để đảm bảo hide() xử lý xong trước khi signal chạy
        QTimer.singleShot(
            50,  # 50ms delay đủ để Qt xử lý hide event
            lambda: self.region_selected.emit(
                rect.x(), rect.y(), rect.width(), rect.height()
            ),
        )

    def _cancel_selection(self):
        """Huỷ selection."""
        if self._signal_emitted:
            return

        self._signal_emitted = True
        self.hide()

        QTimer.singleShot(50, self.selection_cancelled.emit)


# --------------------------------------------------
# SCREENSHOT UTILITY
# --------------------------------------------------


def take_qt_screenshot() -> QPixmap:
    """
    Chụp toàn bộ virtual screen.

    Returns:
        QPixmap của toàn màn hình
    """
    screen = QApplication.primaryScreen()
    virtual_geo = screen.virtualGeometry()

    pixmap = screen.grabWindow(
        0, virtual_geo.x(), virtual_geo.y(), virtual_geo.width(), virtual_geo.height()
    )
    return pixmap
