import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QGraphicsDropShadowEffect, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QSize
from PyQt6.QtGui import QColor, QFont

class ChatWidget(QWidget):
    """
    The main floating, always-on-top UI for SUVI.
    Provides visual feedback on state, shows transcripts, and offers a Smart Interrupt button.
    """
    # Signal emitted when user clicks the Stop button
    interrupt_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        # Frameless, always on top, and doesn't show in the Alt+Tab task switcher
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._drag_pos = QPoint()
        self.setMinimumSize(400, 160)
        self.init_ui()
        
    def init_ui(self):
        # Main layout for the widget itself
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Container QFrame to hold the styling (rounded corners, dark translucent background)
        self.container = QFrame(self)
        self.container.setObjectName("MainContainer")
        self.container.setStyleSheet("""
            #MainContainer {
                background-color: rgba(25, 25, 30, 245);
                border-radius: 20px;
                border: 1px solid rgba(187, 134, 252, 0.3);
            }
        """)
        
        # Add soft drop shadow for floating effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 10)
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(25, 20, 25, 20)
        
        # --- Top Row: Status ---
        self.status_label = QLabel("🟢 SUVI ACTIVE", self.container)
        self.status_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: #BB86FC; background: transparent;")
        container_layout.addWidget(self.status_label)
        
        # --- Middle Row: Transcript ---
        self.transcript_label = QLabel("Ready for your voice command...", self.container)
        self.transcript_label.setFont(QFont("Segoe UI", 10))
        self.transcript_label.setWordWrap(True)
        self.transcript_label.setMinimumHeight(45)
        self.transcript_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        self.transcript_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        container_layout.addWidget(self.transcript_label)
        
        # --- Bottom Row: Controls ---
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 10, 0, 0)
        
        # Autopilot Toggle
        self.autopilot_btn = QPushButton("✈️ Autopilot: OFF", self.container)
        self.autopilot_btn.setCheckable(True)
        self.autopilot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.autopilot_btn.setFixedSize(140, 32)
        self.autopilot_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(60, 60, 65, 0.8);
                color: #BBBBBB;
                border-radius: 10px;
                font-size: 9pt;
                font-weight: bold;
                border: 1px solid #444;
            }
            QPushButton:checked {
                background-color: rgba(3, 218, 198, 0.2);
                color: #03DAC6;
                border: 1px solid #03DAC6;
            }
        """)
        self.autopilot_btn.clicked.connect(self._toggle_autopilot)
        
        controls_layout.addWidget(self.autopilot_btn)
        controls_layout.addStretch() 
        
        self.stop_btn = QPushButton("🛑 Stop", self.container)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.setFixedSize(90, 32)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #CF6679;
                color: #000000;
                border-radius: 10px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background-color: #ff798d; }
        """)
        self.stop_btn.clicked.connect(self.interrupt_requested.emit)
        controls_layout.addWidget(self.stop_btn)
        
        container_layout.addLayout(controls_layout)
        layout.addWidget(self.container)
        
        self._center_on_screen()

    def _toggle_autopilot(self, checked):
        if checked:
            self.autopilot_btn.setText("✈️ Autopilot: ON")
        else:
            self.autopilot_btn.setText("✈️ Autopilot: OFF")

    def _center_on_screen(self):
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = screen.height() - self.height() - 80 
        self.move(x, y)

    def update_state(self, state: str):
        """Update the visual indicator based on SUVI's current phase."""
        states = {
            "idle": ("🟢 SUVI READY", "#03DAC6"),
            "listening": ("🎙️ LISTENING...", "#BB86FC"), 
            "thinking": ("🧠 THINKING...", "#BB86FC"),  
            "speaking": ("🔊 SPEAKING...", "#03DAC6"),  
            "executing": ("⚡ EXECUTING...", "#F4D03F"), 
            "error": ("❌ ERROR", "#CF6679") 
        }
        text, color = states.get(state, ("⚪ BUSY", "#FFFFFF"))
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; background: transparent;")

    def update_transcript(self, text: str):
        """Update the scrolling text being spoken or heard."""
        if len(text) > 120:
            text = text[:117] + "..."
        self.transcript_label.setText(text)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
