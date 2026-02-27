from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QApplication
from PyQt6.QtCore import Qt

class ResultCard(QWidget):
    def __init__(self, parent_ring):
        super().__init__(None)
        self._parent_ring = parent_ring
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.resize(300, 150)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Simple stylesheet for a dark, rounded card
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 23, 42, 240);
                border-radius: 12px;
                border: 1px solid #334155;
                color: #F8FAFC;
                font-family: 'Segoe UI';
            }
            QPushButton {
                background-color: #4F46E5;
                border-radius: 6px;
                padding: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #4338CA; }
        """)
        
        self.lbl_title = QLabel("Result")
        self.lbl_title.setStyleSheet("font-weight: bold; color: #94A3B8; border: none; background: transparent;")
        
        self.lbl_content = QLabel("")
        self.lbl_content.setWordWrap(True)
        self.lbl_content.setStyleSheet("border: none; background: transparent; margin-top: 5px; margin-bottom: 5px;")
        
        self.btn_copy = QPushButton("Copy to Clipboard")
        self.btn_copy.clicked.connect(self._copy_to_clipboard)
        
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_content)
        layout.addWidget(self.btn_copy)

    def show_result(self, title: str, content: str):
        self.lbl_title.setText(title)
        # Truncate content if it's too long for the preview card
        display_text = content if len(content) < 150 else content[:147] + "..."
        self.lbl_content.setText(display_text)
        self._full_content = content
        
        # Position to the left of the ring
        ring_geo = self._parent_ring.geometry()
        self.move(ring_geo.x() - self.width() - 20, ring_geo.y() + 50)
        self.show()

    def _copy_to_clipboard(self):
        QApplication.clipboard().setText(self._full_content)
        self.btn_copy.setText("Copied!")