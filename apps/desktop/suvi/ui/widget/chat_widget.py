from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QGraphicsDropShadowEffect, QFrame, QLineEdit
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QColor, QFont

class ChatWidget(QWidget):
    """
    The main floating, always-on-top UI for SUVI.
    Provides visual feedback on state, shows transcripts, and offers text chat and session controls.
    """
    
    interrupt_requested = pyqtSignal()
    session_toggle_requested = pyqtSignal(bool) 
    text_submitted = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._drag_pos = QPoint()
        self.setMinimumSize(450, 220)
        self.is_session_active = False
        self.init_ui()
        
    def init_ui(self):
        # Main layout for the widget itself
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        
        self.container = QFrame(self)
        self.container.setObjectName("MainContainer")
        self.container.setStyleSheet("""
            #MainContainer {
                background-color: rgba(25, 25, 30, 245);
                border-radius: 20px;
                border: 1px solid rgba(187, 134, 252, 0.3);
            }
        """)
        
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 10)
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(25, 20, 25, 20)
        
        # --- Top Row: Status & Toggle ---
        header_layout = QHBoxLayout()

        
        self.close_btn = QPushButton("✕", self.container)
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: none;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(207, 102, 121, 0.3);
                color: #CF6679;
            }
        """)
        self.close_btn.clicked.connect(self._on_close_clicked)
        header_layout.addWidget(self.close_btn)

        self.status_label = QLabel("⚪ SUVI IDLE", self.container)
        self.status_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        header_layout.addWidget(self.status_label)

        header_layout.addStretch()
        
        self.toggle_btn = QPushButton("▶ Start", self.container)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setFixedSize(80, 30)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #03DAC6;
                color: #000000;
                border-radius: 10px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background-color: #018786; }
        """)
        self.toggle_btn.clicked.connect(self._on_toggle_clicked)
        header_layout.addWidget(self.toggle_btn)
        container_layout.addLayout(header_layout)
        
        # --- Middle Row: Transcript ---
        self.transcript_label = QLabel("Say 'Hey SUVI' or click Start...", self.container)
        self.transcript_label.setFont(QFont("Segoe UI", 10))
        self.transcript_label.setWordWrap(True)
        self.transcript_label.setMinimumHeight(45)
        self.transcript_label.setStyleSheet("color: #BBBBBB; background: transparent;")
        self.transcript_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        container_layout.addWidget(self.transcript_label)
        
        # --- Text Input Row (For voiceless users) ---
        input_layout = QHBoxLayout()
        self.text_input = QLineEdit(self.container)
        self.text_input.setPlaceholderText("Type a command here...")
        self.text_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(60, 60, 65, 0.8);
                color: white;
                border-radius: 8px;
                padding: 6px 10px;
                border: 1px solid #444;
            }
            QLineEdit:focus { border: 1px solid #BB86FC; }
        """)
        self.text_input.returnPressed.connect(self._submit_text)
        input_layout.addWidget(self.text_input)
        
        self.send_btn = QPushButton("Send", self.container)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setFixedSize(60, 30)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #BB86FC;
                color: #000000;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #9965f4; }
        """)
        self.send_btn.clicked.connect(self._submit_text)
        input_layout.addWidget(self.send_btn)
        container_layout.addLayout(input_layout)
        
        # --- Bottom Row: Controls ---
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 10, 0, 0)
        
        # Autopilot Toggle
        self.autopilot_btn = QPushButton("✈️ Autopilot: OFF", self.container)
        self.autopilot_btn.setCheckable(True)
        self.autopilot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.autopilot_btn.setFixedSize(140, 30)
        self.autopilot_btn.setToolTip("When ON, SUVI will skip voice confirmation for safe/moderate tasks.")
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
        
        container_layout.addLayout(controls_layout)
        layout.addWidget(self.container)
        
        self._center_on_screen()

    def _on_close_clicked(self):
        """Close/hide the overlay"""
        self.hide()
        
        self.interrupt_requested.emit()

    def _on_toggle_clicked(self):
        self.is_session_active = not self.is_session_active
        if self.is_session_active:
            self.toggle_btn.setText("🛑 Stop")
            self.toggle_btn.setStyleSheet("background-color: #CF6679; color: #000; border-radius: 10px; font-weight: bold;")
            self.session_toggle_requested.emit(True)
        else:
            self.toggle_btn.setText("▶ Start")
            self.toggle_btn.setStyleSheet("background-color: #03DAC6; color: #000; border-radius: 10px; font-weight: bold;")
            self.session_toggle_requested.emit(False)
            self.interrupt_requested.emit()

    def _submit_text(self):
        text = self.text_input.text().strip()
        if text:
            
            if not self.is_session_active:
                self._on_toggle_clicked()
            self.text_submitted.emit(text)
            self.text_input.clear()

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
        if state in ["idle", "error"] and self.is_session_active and state != "idle":
            
            self.is_session_active = False
            self.toggle_btn.setText("▶ Start")
            self.toggle_btn.setStyleSheet("background-color: #03DAC6; color: #000; border-radius: 10px; font-weight: bold;")

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
