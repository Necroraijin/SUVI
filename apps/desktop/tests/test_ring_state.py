from apps.desktop.suvi.ui.action_ring.ring_state import RingState, RingVisualState

def test_ring_initial_state():
    vs = RingVisualState()
    assert vs.ring_radius == 24.0
    assert vs.ring_opacity == 0.7
    assert vs.active_segment == -1