from PyQt6.QtGui import QPainter, QPainterPath, QColor, QBrush, QFont, QRadialGradient, QPen
from PyQt6.QtCore import QRectF, Qt
from apps.desktop.suvi.ui.action_ring.ring_state import RingState, RingVisualState
from apps.desktop.suvi.ui.action_ring.segment_config import SEGMENTS
import math

def paint_ring(painter: QPainter, vs: RingVisualState, state: RingState, width: int, height: int):
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    cx, cy = width / 2, height / 2
    
    # --- 1. Outer Glow Halo (Dynamic based on mic amplitude) ---
    if vs.orb_glow > 0.01:
        glow_r = (vs.ring_radius if vs.ring_radius > 40 else 24) + (vs.orb_glow * 20)
        gradient = QRadialGradient(cx, cy, glow_r)
        glow_color = QColor(79, 70, 229, int(150 * vs.orb_glow)) # Indigo with variable opacity
        gradient.setColorAt(0.0, glow_color)
        gradient.setColorAt(1.0, QColor(79, 70, 229, 0)) # Transparent at edges
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - glow_r, cy - glow_r, glow_r*2, glow_r*2))

    # --- 2. Draw Ring Segments (Only if radius is expanded) ---
    if vs.ring_radius > 40:
        r_outer = vs.ring_radius
        r_inner = vs.ring_radius * 0.55
        arc_span = 40.0 # 40 deg colored, 5 deg gap
        
        for i, seg in enumerate(SEGMENTS):
            # Rotate if in THINKING state
            offset = vs.rotation_angle if state == RingState.THINKING else 0
            start_angle = seg['angle_start'] + offset
            
            color = QColor(seg['color'])
            if i == vs.active_segment:
                color = color.lighter(130)
                
            path = QPainterPath()
            path.arcMoveTo(QRectF(cx - r_outer, cy - r_outer, r_outer*2, r_outer*2), start_angle)
            path.arcTo(QRectF(cx - r_outer, cy - r_outer, r_outer*2, r_outer*2), start_angle, arc_span)
            path.arcTo(QRectF(cx - r_inner, cy - r_inner, r_inner*2, r_inner*2), start_angle + arc_span, -arc_span)
            path.closeSubpath()
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.fillPath(path, QBrush(color))
            
            # Labels (Only if not rotating too fast)
            if state != RingState.THINKING:
                text_angle_rad = math.radians(start_angle + (arc_span / 2))
                text_r = r_inner + ((r_outer - r_inner) / 2)
                tx = cx + (text_r * math.cos(text_angle_rad))
                ty = cy - (text_r * math.sin(text_angle_rad))
                
                painter.setPen(QColor("#FFFFFF"))
                painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                text_rect = QRectF(tx - 30, ty - 10, 60, 20)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, seg['label'])

    # --- 3. Draw Center Orb (Always visible) ---
    orb_color = QColor(79, 70, 229, int(255 * vs.ring_opacity))
    if state == RingState.ERROR:
        orb_color = QColor(220, 38, 38) # Red for error
    elif state == RingState.DONE:
        orb_color = QColor(16, 185, 129) # Green for success

    painter.setBrush(QBrush(orb_color))
    painter.setPen(Qt.PenStyle.NoPen)
    
    # Pulse the orb slightly with the mic
    pulse_size = vs.orb_glow * 5
    orb_r = (24.0 if vs.ring_radius > 40 else vs.ring_radius) + pulse_size
    painter.drawEllipse(QRectF(cx - orb_r, cy - orb_r, orb_r*2, orb_r*2))

    # --- 4. Rotating Arc (THINKING State) ---
    if state == RingState.THINKING:
        painter.setPen(QPen(QColor("#FFFFFF"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(QRectF(cx - r_outer - 5, cy - r_outer - 5, (r_outer+5)*2, (r_outer+5)*2), 
                        int(vs.rotation_angle * 16), 60 * 16)
