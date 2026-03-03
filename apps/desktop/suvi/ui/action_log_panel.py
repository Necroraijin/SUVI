"""Action Log Panel - History display for executed actions."""

from collections import deque
from datetime import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont


class ActionLogPanel(QWidget):
    """Displays history of executed actions (last 50 actions)."""

    # Signal when user clicks on an action to view details
    action_selected = pyqtSignal(str)  # action_id

    def __init__(self, parent=None, max_items: int = 50):
        super().__init__(parent)
        self._max_items = max_items
        self._actions = deque(maxlen=max_items)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(320, 400)

        self._setup_ui()

    def _setup_ui(self):
        """Initialize the UI components."""
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 23, 42, 235);
                border-radius: 12px;
                border: 1px solid #334155;
            }
            QLabel {
                color: #F8FAFC;
                background: transparent;
            }
            QListWidget {
                background: transparent;
                border: none;
                color: #E2E8F0;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #1E293B;
            }
            QListWidget::item:selected {
                background-color: #4F46E5;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header
        header = QLabel("Action History")
        header.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(header)

        # Action list
        self.action_list = QListWidget()
        self.action_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.action_list)

        # Clear button
        clear_btn = QLabel("[ Clear ]")
        clear_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        clear_btn.setStyleSheet("color: #64748B; cursor: pointer;")
        clear_btn.mousePressEvent = lambda e: self.clear()
        layout.addWidget(clear_btn)

    def add_action(self, action_id: str, action_type: str, status: str, result: str = ""):
        """Add an action to the history."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        display_text = f"[{timestamp}] {action_type}: {status}"

        item = QListWidgetItem(display_text)
        item.setData(Qt.ItemDataRole.UserRole, action_id)
        item.setData(Qt.ItemDataRole.ToolTipRole, result)

        # Color based on status
        if status == "completed":
            item.setForeground(QColor("#10B981"))  # Green
        elif status == "failed":
            item.setForeground(QColor("#EF4444"))  # Red
        else:
            item.setForeground(QColor("#F59E0B"))  # Yellow

        self._actions.append({
            "id": action_id,
            "type": action_type,
            "status": status,
            "result": result,
            "timestamp": timestamp
        })

        self.action_list.insertItem(0, item)

    def clear(self):
        """Clear all action history."""
        self._actions.clear()
        self.action_list.clear()

    def _on_item_clicked(self, item):
        """Handle item click."""
        action_id = item.data(Qt.ItemDataRole.UserRole)
        self.action_selected.emit(action_id)

    def get_recent_actions(self) -> list[dict]:
        """Get list of recent actions."""
        return list(self._actions)
