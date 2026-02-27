from PyQt6.QtCore import QObject, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QAbstractAnimation
from apps.desktop.suvi.ui.action_ring.ring_state import RingState

class RingAnimator(QObject):
    """Owns all QPropertyAnimations for the ring visual state"""

    def __init__(self, ring_widget):
        super().__init__(ring_widget)
        self._ring = ring_widget
        
        # Animate ring_radius: 24 (idle) <-> 150 (expanded)
        self._radius_anim = QPropertyAnimation(self._ring, b"ring_radius")
        self._radius_anim.setDuration(400) # 400 milliseconds
        self._radius_anim.setEasingCurve(QEasingCurve.Type.OutBack) # Overshoot spring effect
        
        # Animate opacity: 0.7 <-> 1.0
        self._opacity_anim = QPropertyAnimation(self._ring, b"ring_opacity")
        self._opacity_anim.setDuration(250)
        self._opacity_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def transition_to(self, state: RingState):
        group = QParallelAnimationGroup(self)
        
        if state == RingState.LISTENING:
            self._radius_anim.setEndValue(150.0)
            self._opacity_anim.setEndValue(1.0)
        elif state == RingState.IDLE:
            self._radius_anim.setEndValue(24.0)
            self._opacity_anim.setEndValue(0.7)
            
        group.addAnimation(self._radius_anim)
        group.addAnimation(self._opacity_anim)
        group.start(QAbstractAnimation.DeletionPolicy.KeepWhenStopped)