from PyQt6.QtGui import QPainter, QPainterPath, QColor, QBrush, QFont
from PyQt6.QtCore import QRectF, Qt
from apps.desktop.suvi.ui.action_ring.ring_state import RingState, RingVisualState
from apps.desktop.suvi.ui.action_ring.segment_config import SEGMENTS

def paint_ring(painter: QPainter, vs: RingVisualState, state: RingState, width: int, height: int):
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    cx, cy = width / 2, height / 2
    
    # 1. Draw Ring Segments (Only if radius is expanded)
    if vs.ring_radius > 40:
        r_outer = vs.ring_radius
        r_inner = vs.ring_radius * 0.55  # Creates the donut hole
        arc_span = 40.0                  # 40 deg colored, 5 deg gap between segments
        
        for i, seg in enumerate(SEGMENTS):
            start_angle = seg['angle_start']
            color = QColor(seg['color'])
            
            # Highlight if it's the active agent
            if i == vs.active_segment:
                color = color.lighter(130)
                
            path = QPainterPath()
            path.arcMoveTo(QRectF(cx - r_outer, cy - r_outer, r_outer*2, r_outer*2), start_angle)
            path.arcTo(QRectF(cx - r_outer, cy - r_outer, r_outer*2, r_outer*2), start_angle, arc_span)
            path.arcTo(QRectF(cx - r_inner, cy - r_inner, r_inner*2, r_inner*2), start_angle + arc_span, -arc_span)
            path.closeSubpath()
            
            # Fill the segment
            painter.setPen(Qt.PenStyle.NoPen)
            painter.fillPath(path, QBrush(color))
            
            # Draw the label text (Math to find the center of the segment)
            import math
            text_angle_rad = math.radians(start_angle + (arc_span / 2))
            text_r = r_inner + ((r_outer - r_inner) / 2)
            tx = cx + (text_r * math.cos(text_angle_rad))
            ty = cy - (text_r * math.sin(text_angle_rad)) # Qt y-axis is inverted
            
            painter.setPen(QColor("#FFFFFF"))
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            
            # Draw text centered on the calculated point
            text_rect = QRectF(tx - 30, ty - 10, 60, 20)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, seg['label'])

    # 2. Draw Center Orb (Always visible)
    painter.setBrush(QBrush(QColor(79, 70, 229, int(255 * vs.ring_opacity)))) # Indigo
    painter.setPen(Qt.PenStyle.NoPen)
    
    # If expanded, center orb stays small. If idle, it uses the ring_radius.
    orb_r = 24.0 if vs.ring_radius > 40 else vs.ring_radius
    painter.drawEllipse(QRectF(cx - orb_r, cy - orb_r, orb_r*2, orb_r*2))