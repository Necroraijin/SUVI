from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal

class ConfirmDialog(QWidget):
    # Emit True if approved, False if rejected
    decision_made = pyqtSignal(bool)

    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(350, 180)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 23, 42, 245);
                border-radius: 12px;
                border: 2px solid #DC2626; /* Red border for danger */
                color: #F8FAFC;
                font-family: 'Segoe UI';
            }
            QPushButton { border-radius: 6px; padding: 8px 16px; font-weight: bold; }
        """)
        
        self.lbl_warning = QLabel("⚠️ High-Risk Action Detected")
        self.lbl_warning.setStyleSheet("font-size: 14px; font-weight: bold; color: #FCA5A5; border: none; background: transparent;")
        
        self.lbl_action = QLabel("")
        self.lbl_action.setWordWrap(True)
        self.lbl_action.setStyleSheet("font-size: 12px; border: none; background: transparent; margin: 10px 0px;")
        
        btn_layout = QHBoxLayout()
        self.btn_reject = QPushButton("Reject")
        self.btn_reject.setStyleSheet("background-color: #334155; color: white;")
        self.btn_reject.clicked.connect(lambda: self._finish(False))
        
        self.btn_approve = QPushButton("Approve")
        self.btn_approve.setStyleSheet("background-color: #DC2626; color: white;")
        self.btn_approve.clicked.connect(lambda: self._finish(True))
        
        btn_layout.addWidget(self.btn_reject)
        btn_layout.addWidget(self.btn_approve)
        
        layout.addWidget(self.lbl_warning)
        layout.addWidget(self.lbl_action)
        layout.addLayout(btn_layout)

    def prompt_user(self, action_description: str):
        self.lbl_action.setText(f"SUVI wants to:\n{action_description}")
        # Center on screen
        screen = self.screen().geometry()
        self.move(int((screen.width() - self.width()) / 2), int((screen.height() - self.height()) / 2))
        self.show()

    def _finish(self, approved: bool):
        self.hide()
        self.decision_made.emit(approved)