import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
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
        self.init_ui()
        
    def init_ui(self):
        self.resize(380, 140)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Container to hold the styling (rounded corners, dark translucent background)
        self.container = QWidget(self)
        self.container.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 35, 235);
                border-radius: 18px;
                color: white;
            }
        """)
        
        # Add soft drop shadow for floating effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(20, 15, 20, 15)
        
        # --- Top Row: Status ---
        self.status_label = QLabel("🟢 Ready", self.container)
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: #4CAF50; background: transparent;")
        container_layout.addWidget(self.status_label)
        
        # --- Middle Row: Transcript ---
        self.transcript_label = QLabel("Waiting for command...", self.container)
        self.transcript_label.setFont(QFont("Segoe UI", 10))
        self.transcript_label.setWordWrap(True)
        self.transcript_label.setStyleSheet("color: #E0E0E0; background: transparent;")
        container_layout.addWidget(self.transcript_label)
        
        # --- Bottom Row: Controls ---
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 5, 0, 0)
        controls_layout.addStretch() # Push button to the right
        
        self.stop_btn = QPushButton("🛑 Stop", self.container)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(244, 67, 54, 0.8);
                color: white;
                border-radius: 12px;
                padding: 6px 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background-color: rgba(211, 47, 47, 1); }
            QPushButton:pressed { background-color: rgba(183, 28, 28, 1); }
        """)
        # Connect the physical button to our signal
        self.stop_btn.clicked.connect(self.interrupt_requested.emit)
        
        controls_layout.addWidget(self.stop_btn)
        container_layout.addLayout(controls_layout)
        
        layout.addWidget(self.container)
        
        # Position at bottom center of primary screen
        self._center_on_screen()

    def _center_on_screen(self):
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = screen.height() - self.height() - 60 # 60px above taskbar
        self.move(x, y)

    def update_state(self, state: str):
        """Update the visual indicator based on SUVI's current phase."""
        states = {
            "idle": ("🟢 Ready", "#4CAF50"),
            "listening": ("🎙️ Listening...", "#2196F3"), # Blue
            "thinking": ("🧠 Thinking...", "#9C27B0"),  # Purple
            "speaking": ("🔊 Speaking...", "#FF9800"),  # Orange
            "executing": ("⚡ Executing Action...", "#FFEB3B"), # Yellow
            "error": ("❌ Error", "#F44336") # Red
        }
        text, color = states.get(state, ("⚪ Unknown", "#FFFFFF"))
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; background: transparent;")

    def update_transcript(self, text: str):
        """Update the scrolling text being spoken or heard."""
        # Truncate if too long so widget doesn't resize infinitely
        if len(text) > 80:
            text = text[:77] + "..."
        self.transcript_label.setText(text)

    # --- Allow dragging the frameless window ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
