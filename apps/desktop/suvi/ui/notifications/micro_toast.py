from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QBrush, QFont

class MicroToast(QWidget):
    def __init__(self, parent_ring):
        super().__init__(None)  # Must be None so it acts as a floating top-level window
        self._parent_ring = parent_ring
        self._message = ""
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # Default size, will be dynamically positioned
        self.resize(240, 44)

    def show_status(self, message: str, duration_ms: int = 3000):
        self._message = message
        
        # Position exactly 56 pixels above the Action Ring
        ring_geo = self._parent_ring.geometry()
        x = ring_geo.x() + int((ring_geo.width() - self.width()) / 2)
        y = ring_geo.y() - 56
        self.move(x, y)
        
        self.show()
        self.update() # Force repaint with new text
        
        if duration_ms > 0:
            QTimer.singleShot(duration_ms, self.hide)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Navy pill background with 86% opacity
        painter.setBrush(QBrush(QColor(15, 23, 42, 220))) 
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect().adjusted(4, 4, -4, -4), 18, 18)
        
        # Centered white text
        painter.setPen(QColor('#E2E8F0'))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._message)