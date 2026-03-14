import os
import sys
import asyncio
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QHBoxLayout, QFrame, QStackedWidget,
                             QMessageBox, QGraphicsDropShadowEffect, QTextEdit,
                             QTabWidget, QTableWidget, QTableWidgetItem, QScrollArea,
                             QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer, QPropertyAnimation, QEasingCurve, QSize, QByteArray
from PyQt6.QtGui import QColor, QFont, QIcon, QPalette, QBrush, QLinearGradient, QPainter, QPen
from dotenv import load_dotenv

from apps.desktop.suvi.services.auth_service import AuthService
from apps.desktop.suvi.services.memory_service import MemoryService

class SUVIPanel(QWidget):
    """
    The main SUVI Panel - a comprehensive interface for settings, chat history, and about.
    Can be shown/hidden via voice command or double-click on tray icon.
    """
    ready_to_start = pyqtSignal(dict)  # carries settings dict
    panel_shown = pyqtSignal()  # emitted when panel is shown
    panel_hidden = pyqtSignal()  # emitted when panel is hidden

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SUVI Panel")
        self.setFixedSize(600, 700)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._drag_pos = QPoint()
        self.auth_service = AuthService()
        self.memory_service = None  # Initialized when needed
        self._is_visible = True

        # Startup animation state
        self._startup_opacity = 0
        self._startup_shown = False

        self.init_ui()

        # Center on screen
        self._center_on_screen()

    def _center_on_screen(self):
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def init_ui(self):
        self.main_container = QFrame(self)
        self.main_container.setGeometry(10, 10, 580, 680)
        self.main_container.setStyleSheet("""
            QFrame {
                background-color: #1E1E22;
                border-radius: 20px;
                color: #FFFFFF;
            }
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: transparent;
                color: #888;
                padding: 10px 20px;
                border: none;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                color: #BB86FC;
                border-bottom: 2px solid #BB86FC;
            }
            QTabBar::tab:hover {
                color: #BBB;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.main_container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.main_container)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- Header ---
        header_layout = QHBoxLayout()

        # Logo/Title with animation potential
        self.title_label = QLabel("SUVI")
        self.title_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #BB86FC; background: transparent;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # Minimize button
        min_btn = QPushButton("─")
        min_btn.setFixedSize(30, 30)
        min_btn.setStyleSheet("background: transparent; color: #888; font-size: 18px; border: none;")
        min_btn.clicked.connect(self.hide_panel)
        header_layout.addWidget(min_btn)

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("background: transparent; color: #CF6679; font-size: 18px; border: none;")
        close_btn.clicked.connect(self._quit_app)
        header_layout.addWidget(close_btn)

        layout.addLayout(header_layout)

        tagline = QLabel("Superintelligent Unified Voice Interface")
        tagline.setFont(QFont("Segoe UI", 10))
        tagline.setStyleSheet("color: #AAAAAA; background: transparent;")
        layout.addWidget(tagline)
        layout.addSpacing(10)

        # --- Tab Widget ---
        self.tabs = QTabWidget()

        # Tab 1: Login
        login_tab = self._create_login_tab()
        self.tabs.addTab(login_tab, "Login")

        # Tab 2: Settings
        settings_tab = self._create_settings_tab()
        self.tabs.addTab(settings_tab, "Settings")

        # Tab 3: Chat History
        history_tab = self._create_history_tab()
        self.tabs.addTab(history_tab, "Chat History")

        # Tab 4: About
        about_tab = self._create_about_tab()
        self.tabs.addTab(about_tab, "About")

        layout.addWidget(self.tabs)

        # Show the window by default
        self.show()

        # Load settings after window is shown
        QTimer.singleShot(100, self._load_current_settings)

    def _create_login_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)

        # Login form
        layout.addWidget(QLabel("Email"))
        self.email_input = QLineEdit()
        self.email_input.setStyleSheet(self._get_input_style())
        layout.addWidget(self.email_input)
        layout.addSpacing(10)

        layout.addWidget(QLabel("Password"))
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setStyleSheet(self._get_input_style())
        layout.addWidget(self.pass_input)
        layout.addSpacing(20)

        self.login_btn = QPushButton("Log In")
        self.login_btn.setFixedHeight(45)
        self.login_btn.setStyleSheet("background-color: #03DAC6; color: #000; font-weight: bold; border-radius: 10px;")
        self.login_btn.clicked.connect(lambda: asyncio.ensure_future(self._handle_login()))
        layout.addWidget(self.login_btn)

        layout.addSpacing(10)

        # Sign up section
        layout.addWidget(QLabel("New here? Create an account:"))
        layout.addWidget(QLabel("Full Name"))
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(self._get_input_style())
        layout.addWidget(self.name_input)
        layout.addSpacing(5)

        layout.addWidget(QLabel("Email"))
        self.signup_email = QLineEdit()
        self.signup_email.setStyleSheet(self._get_input_style())
        layout.addWidget(self.signup_email)
        layout.addSpacing(5)

        layout.addWidget(QLabel("Password"))
        self.signup_pass = QLineEdit()
        self.signup_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.signup_pass.setStyleSheet(self._get_input_style())
        layout.addWidget(self.signup_pass)
        layout.addSpacing(10)

        self.signup_btn = QPushButton("Create Account")
        self.signup_btn.setFixedHeight(40)
        self.signup_btn.setStyleSheet("background-color: #CF6679; color: black; font-weight: bold; border-radius: 10px;")
        self.signup_btn.clicked.connect(lambda: asyncio.ensure_future(self._handle_signup()))
        layout.addWidget(self.signup_btn)

        layout.addStretch()

        return tab

    def _create_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)

        # User Info Section
        user_section = QLabel("👤 User Information")
        user_section.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        user_section.setStyleSheet("color: #BB86FC;")
        layout.addWidget(user_section)

        self.user_name_label = QLabel("Name: Not logged in")
        self.user_name_label.setStyleSheet("color: #CCC;")
        layout.addWidget(self.user_name_label)

        self.user_email_label = QLabel("Email: Not logged in")
        self.user_email_label.setStyleSheet("color: #CCC;")
        layout.addWidget(self.user_email_label)

        self.user_id_label = QLabel("User ID: -")
        self.user_id_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.user_id_label)

        layout.addSpacing(20)

        # API Settings Section
        api_section = QLabel("🔑 API Configuration")
        api_section.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        api_section.setStyleSheet("color: #BB86FC;")
        layout.addWidget(api_section)

        layout.addWidget(QLabel("Gemini API Key"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setStyleSheet(self._get_input_style())
        layout.addWidget(self.api_key_input)

        layout.addWidget(QLabel("GCP Project ID"))
        self.project_id_input = QLineEdit()
        self.project_id_input.setStyleSheet(self._get_input_style())
        layout.addWidget(self.project_id_input)

        layout.addSpacing(20)

        # Launch Button
        self.start_btn = QPushButton("LOGIN TO LAUNCH")
        self.start_btn.setEnabled(False)
        self.start_btn.setFixedHeight(50)
        self.start_btn.setStyleSheet("background-color: #555; color: #888; font-size: 14px; font-weight: bold; border-radius: 12px;")
        self.start_btn.clicked.connect(self._handle_launch)
        layout.addWidget(self.start_btn)

        layout.addStretch()

        return tab

    def _create_history_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)

        header = QLabel("📜 Chat History")
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #BB86FC;")
        layout.addWidget(header)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setFixedSize(100, 30)
        refresh_btn.setStyleSheet("background: #333; color: #CCC; border-radius: 5px;")
        refresh_btn.clicked.connect(self._load_chat_history)
        layout.addWidget(refresh_btn)

        layout.addSpacing(5)

        # Chat history list
        self.chat_history_list = QListWidget()
        self.chat_history_list.setStyleSheet("""
            QListWidget {
                background-color: #252529;
                border: 1px solid #3D3D42;
                border-radius: 8px;
                color: #CCC;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:selected {
                background-color: #333;
                color: #BB86FC;
            }
        """)
        layout.addWidget(self.chat_history_list)

        return tab

    def _create_about_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        # Logo
        logo_label = QLabel("SUVI")
        logo_label.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        logo_label.setStyleSheet("color: #BB86FC;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        tagline = QLabel("Superintelligent Unified Voice Interface")
        tagline.setFont(QFont("Segoe UI", 12))
        tagline.setStyleSheet("color: #888;")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tagline)

        layout.addSpacing(20)

        # Version
        version = QLabel("Version 1.0.0")
        version.setStyleSheet("color: #666;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        layout.addSpacing(20)

        # Description
        desc = QLabel(
            "SUVI is a production-grade AI desktop assistant that uses "
            "Gemini Live API for voice interaction and Gemini Computer Use "
            "for visual desktop control. Built for accessibility and ease of use."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #AAA; line-height: 1.5;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        layout.addSpacing(20)

        # Features
        features_label = QLabel("Key Features:")
        features_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        features_label.setStyleSheet("color: #03DAC6;")
        layout.addWidget(features_label)

        features = [
            "🎙️ Voice-controlled desktop automation",
            "👁️ Visual screen understanding with Gemini",
            "🔄 Real-time interrupt capability",
            "☁️ Cloud-hosted with GCP integration",
            "♿ Built for accessibility"
        ]

        for feature in features:
            f_label = QLabel(feature)
            f_label.setStyleSheet("color: #CCC; padding: 5px;")
            layout.addWidget(f_label)

        layout.addStretch()

        # Hackathon info
        hackathon = QLabel("🏆 Gemini Live Agent Challenge 2026")
        hackathon.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        hackathon.setStyleSheet("color: #F4D03F; padding: 10px;")
        hackathon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hackathon)

        return tab

    def _get_input_style(self):
        return "QLineEdit { background-color: #2C2C31; border: 1px solid #3D3D42; border-radius: 8px; padding: 10px; color: white; }"

    def _load_current_settings(self):
        load_dotenv()
        self.api_key_input.setText(os.getenv("GEMINI_API_KEY", ""))
        self.project_id_input.setText(os.getenv("GCP_PROJECT_ID", ""))

        # Auto-login check
        saved_token = os.getenv("ID_TOKEN")
        saved_user_id = os.getenv("USER_ID")
        saved_name = os.getenv("USER_NAME", "User")
        saved_email = os.getenv("USER_EMAIL", "")

        if saved_token and saved_user_id and saved_token != "mock_token":
            print("🔄 Auto-login triggered based on saved .env credentials.")
            self._update_user_info(saved_name, saved_email, saved_user_id)

            settings = {
                "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
                "PORCUPINE_ACCESS_KEY": os.getenv("PORCUPINE_ACCESS_KEY", ""),
                "GCP_PROJECT_ID": os.getenv("GCP_PROJECT_ID", ""),
                "USER_ID": saved_user_id,
                "USER_NAME": saved_name,
                "ID_TOKEN": saved_token
            }
            asyncio.get_event_loop().call_later(0.5, lambda: self.ready_to_start.emit(settings))
        else:
            self.show()

    def _update_user_info(self, name, email, user_id):
        self.user_name_label.setText(f"Name: {name}")
        self.user_email_label.setText(f"Email: {email}")
        self.user_id_label.setText(f"User ID: {user_id[:20]}...")
        self.start_btn.setEnabled(True)
        self.start_btn.setText("LAUNCH SUVI")
        self.start_btn.setStyleSheet("background-color: #BB86FC; color: #000; font-size: 14px; font-weight: bold; border-radius: 12px;")

    def _load_chat_history(self):
        """Load chat history from memory service"""
        self.chat_history_list.clear()

        if not self.memory_service:
            try:
                # Initialize memory service
                project_id = os.getenv("GCP_PROJECT_ID", "project-0d0747b3-f100-478f-9b6")
                self.memory_service = MemoryService(project_id)
            except Exception as e:
                item = QListWidgetItem(f"⚠️ Could not load history: {str(e)[:50]}")
                self.chat_history_list.addItem(item)
                return

        try:
            # Get recent sessions
            # This is a simplified version - the actual implementation depends on MemoryService
            item = QListWidgetItem("📝 Chat history loading...")
            item.setForeground(QColor("#888"))
            self.chat_history_list.addItem(item)
        except Exception as e:
            item = QListWidgetItem(f"⚠️ Error: {str(e)[:50]}")
            self.chat_history_list.addItem(item)

    async def _handle_login(self):
        email, password = self.email_input.text().strip(), self.pass_input.text().strip()
        if not email or not password:
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Authenticating...")
        res = await self.auth_service.login(email, password)

        if res["success"]:
            self.login_btn.setText("Logged In ✅")

            # Update user info
            user_id = self.auth_service.get_current_user_id()
            self._update_user_info("User", email, user_id)

            self.tabs.setCurrentIndex(1)  # Switch to settings tab
        else:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Log In")
            QMessageBox.critical(self, "Auth Failed", res.get("error", "Unknown error"))

    async def _handle_signup(self):
        email, password, name = self.signup_email.text().strip(), self.signup_pass.text().strip(), self.name_input.text().strip()
        if not email or not password or not name:
            return

        self.signup_btn.setEnabled(False)
        res = await self.auth_service.sign_up(email, password, name)

        if res["success"]:
            QMessageBox.information(self, "Success", "Account created. Please log in.")
            self.email_input.setText(email)
            self.pass_input.setFocus()
        else:
            self.signup_btn.setEnabled(True)
            QMessageBox.critical(self, "Signup Failed", res.get("error", "Unknown error"))

    def _handle_launch(self):
        settings = {
            "GEMINI_API_KEY": self.api_key_input.text().strip(),
            "GCP_PROJECT_ID": self.project_id_input.text().strip(),
            "USER_ID": self.auth_service.get_current_user_id(),
            "USER_NAME": os.getenv("USER_NAME", "User"),
            "ID_TOKEN": self.auth_service.get_id_token()
        }
        self.ready_to_start.emit(settings)
        self.hide_panel()

    def hide_panel(self):
        """Hide the panel but keep it in memory"""
        self.hide()
        self._is_visible = False
        self.panel_hidden.emit()

    def show_panel(self):
        """Show the panel"""
        self.show()
        self._is_visible = True
        self._center_on_screen()
        self.panel_shown.emit()

    def toggle_panel(self):
        """Toggle panel visibility"""
        if self._is_visible:
            self.hide_panel()
        else:
            self.show_panel()

    def is_panel_visible(self):
        return self._is_visible

    def _quit_app(self):
        """Quit the entire application"""
        reply = QMessageBox.question(
            self, 'Quit SUVI',
            'Are you sure you want to quit SUVI?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            QApplication.quit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()


# Keep old name for compatibility
LoginWindow = SUVIPanel