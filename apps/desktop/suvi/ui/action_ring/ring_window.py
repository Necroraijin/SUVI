from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QSize, QPoint, pyqtProperty
from PyQt6.QtGui import QPainter

from apps.desktop.suvi.ui.action_ring.ring_state import RingState, RingVisualState
from apps.desktop.suvi.ui.action_ring.ring_painter import paint_ring
from apps.desktop.suvi.ui.action_ring.ring_animator import RingAnimator
from apps.desktop.suvi.ui.action_ring.drag_handler import DragHandler

class RingWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        self.state = RingState.IDLE
        self.vs = RingVisualState() # Starts at 24.0 radius (Idle)
        
        # Initialize the animation engine
        self.animator = RingAnimator(self)

        # Initialize the drag handler
        self.drag_handler = DragHandler(self)
        self.drag_handler.clicked.connect(self._on_ring_clicked)
        
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
        self._set_click_through(False) # Kept false so we can click it to test!

    def _set_click_through(self, enabled: bool):
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, enabled)

    def _place_at_corner(self):
        screen = QApplication.primaryScreen().geometry()
        x = screen.right() - self.width() - 24
        y = screen.bottom() - self.height() - 60
        self.move(QPoint(x, y))

    # --- Qt Properties for the Animation Engine ---
    
    @pyqtProperty(float)
    def ring_radius(self):
        return self.vs.ring_radius

    @ring_radius.setter
    def ring_radius(self, val):
        self.vs.ring_radius = val
        self.update() # Forces a repaint every single frame of the animation

    @pyqtProperty(float)
    def ring_opacity(self):
        return self.vs.ring_opacity

    @ring_opacity.setter
    def ring_opacity(self, val):
        self.vs.ring_opacity = val
        self.update()

    # --- Interaction & Drawing ---

    def _on_ring_clicked(self):
        # Triggered by the DragHandler if it was a clean tap
        if self.state == RingState.IDLE:
            self.state = RingState.LISTENING
        else:
            self.state = RingState.IDLE
            
        self.animator.transition_to(self.state)

    def paintEvent(self, event):
        painter = QPainter(self)
        paint_ring(painter, self.vs, self.state, self.width(), self.height())