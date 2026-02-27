# from PyQt6.QtWidgets import QWidget, QApplication
# from PyQt6.QtCore import Qt, QSize, QPoint
# from PyQt6.QtGui import QPainter, QColor, QBrush

# from apps.desktop.suvi.ui.action_ring.ring_state import RingState, RingVisualState

# class RingWindow(QWidget):
#     def __init__(self):
#         super().__init__()
        
#         self.state = RingState.IDLE
#         self.vs = RingVisualState()
        
#         # Configure frameless, transparent, always-on-top window
#         self.setWindowFlags(
#             Qt.WindowType.FramelessWindowHint | 
#             Qt.WindowType.WindowStaysOnTopHint | 
#             Qt.WindowType.Tool |
#             Qt.WindowType.NoDropShadowWindowHint
#         )
#         self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
#         self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        
#         self.setFixedSize(QSize(340, 340))
#         self._place_at_corner()
        
#         # Idle ring is invisible to mouse - desktop usable underneath
#         self._set_click_through(True)

#     def _set_click_through(self, enabled: bool):
#         self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, enabled)

#     def _place_at_corner(self):
#         screen = QApplication.primaryScreen().geometry()
#         x = screen.right() - self.width() - 24
#         y = screen.bottom() - self.height() - 60
#         self.move(QPoint(x, y))

#     def paintEvent(self, event):
#         # We will move this to ring_painter.py later, but let's draw the basic IDLE orb first!
#         painter = QPainter(self)
#         painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
#         cx, cy = self.width() / 2, self.height() / 2
        
#         # Draw the SUVI indigo orb
#         painter.setBrush(QBrush(QColor(79, 70, 229, int(255 * self.vs.ring_opacity)))) 
#         painter.setPen(Qt.PenStyle.NoPen)
#         painter.drawEllipse(QPoint(int(cx), int(cy)), int(self.vs.ring_radius), int(self.vs.ring_radius))


from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QSize, QPoint
from PyQt6.QtGui import QPainter

from apps.desktop.suvi.ui.action_ring.ring_state import RingState, RingVisualState
from apps.desktop.suvi.ui.action_ring.ring_painter import paint_ring

class RingWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        # TEMPORARILY FORCE LISTENING STATE TO SEE THE UI
        self.state = RingState.LISTENING
        self.vs = RingVisualState(ring_radius=150.0, ring_opacity=1.0)
        
        # Configure frameless, transparent, always-on-top window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        
        self.setFixedSize(QSize(340, 340))
        self._place_at_corner()
        self._set_click_through(False) # Turn off click-through so we can click it later

    def _set_click_through(self, enabled: bool):
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, enabled)

    def _place_at_corner(self):
        screen = QApplication.primaryScreen().geometry()
        x = screen.right() - self.width() - 24
        y = screen.bottom() - self.height() - 60
        self.move(QPoint(x, y))

    def paintEvent(self, event):
        # Delegate all drawing to our custom painter
        painter = QPainter(self)
        paint_ring(painter, self.vs, self.state, self.width(), self.height())