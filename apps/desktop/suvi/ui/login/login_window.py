import os
import sys
import asyncio
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QHBoxLayout, QFrame, QStackedWidget,
                             QMessageBox, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon
from dotenv import load_dotenv

from apps.desktop.suvi.services.auth_service import AuthService

class LoginWindow(QWidget):
    """
    The main desktop application window for SUVI.
    Handles user authentication and configuration.
    """
    ready_to_start = pyqtSignal(dict) # carries settings dict
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SUVI - Production Login")
        self.setFixedSize(500, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._drag_pos = QPoint()
        self.auth_service = AuthService()
        self.init_ui()
        
    def init_ui(self):
        self.main_container = QFrame(self)
        self.main_container.setGeometry(10, 10, 480, 580)
        self.main_container.setStyleSheet("""
            QFrame {
                background-color: #1E1E22;
                border-radius: 20px;
                color: #FFFFFF;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.main_container.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self.main_container)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # --- Header ---
        header_layout = QHBoxLayout()
        title_label = QLabel("SUVI")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #BB86FC; background: transparent;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("background: transparent; color: #888; font-size: 18px; border: none;")
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        layout.addLayout(header_layout)
        
        tagline = QLabel("Production-grade Accessibility Interface")
        tagline.setFont(QFont("Segoe UI", 10))
        tagline.setStyleSheet("color: #AAAAAA; background: transparent;")
        layout.addWidget(tagline)
        layout.addSpacing(30)
        
        # --- Navigation ---
        nav_layout = QHBoxLayout()
        self.btn_login = QPushButton("Login")
        self.btn_signup = QPushButton("Sign Up")
        self.btn_settings = QPushButton("Settings")
        
        for btn in [self.btn_login, self.btn_signup, self.btn_settings]:
            btn.setCheckable(True)
            btn.setFixedSize(100, 35)
            nav_layout.addWidget(btn)
            
        self.btn_login.setChecked(True)
        self.btn_login.setStyleSheet(self._get_nav_style(True))
        self.btn_signup.setStyleSheet(self._get_nav_style(False))
        self.btn_settings.setStyleSheet(self._get_nav_style(False))
        
        self.btn_login.clicked.connect(lambda: self._switch_page(0))
        self.btn_signup.clicked.connect(lambda: self._switch_page(1))
        self.btn_settings.clicked.connect(lambda: self._switch_page(2))
        layout.addLayout(nav_layout)
        layout.addSpacing(20)
        
        # --- Pages ---
        self.pages = QStackedWidget()
        
        # Page 0: Login
        login_page = QWidget()
        login_layout = QVBoxLayout(login_page)
        login_layout.setContentsMargins(0, 0, 0, 0)
        login_layout.addWidget(QLabel("Email"))
        self.email_input = QLineEdit()
        self.email_input.setStyleSheet(self._get_input_style())
        login_layout.addWidget(self.email_input)
        login_layout.addSpacing(15)
        login_layout.addWidget(QLabel("Password"))
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setStyleSheet(self._get_input_style())
        login_layout.addWidget(self.pass_input)
        login_layout.addSpacing(30)
        self.login_btn = QPushButton("Log In")
        self.login_btn.setFixedHeight(45)
        self.login_btn.setStyleSheet("background-color: #03DAC6; color: #000; font-weight: bold; border-radius: 10px;")
        self.login_btn.clicked.connect(lambda: asyncio.ensure_future(self._handle_login()))
        login_layout.addWidget(self.login_btn)
        login_layout.addStretch()

        # Page 1: Sign Up
        signup_page = QWidget()
        signup_layout = QVBoxLayout(signup_page)
        signup_layout.setContentsMargins(0, 0, 0, 0)
        signup_layout.addWidget(QLabel("Full Name"))
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(self._get_input_style())
        signup_layout.addWidget(self.name_input)
        signup_layout.addSpacing(10)
        signup_layout.addWidget(QLabel("Email"))
        self.signup_email = QLineEdit()
        self.signup_email.setStyleSheet(self._get_input_style())
        signup_layout.addWidget(self.signup_email)
        signup_layout.addSpacing(10)
        signup_layout.addWidget(QLabel("Password"))
        self.signup_pass = QLineEdit()
        self.signup_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.signup_pass.setStyleSheet(self._get_input_style())
        signup_layout.addWidget(self.signup_pass)
        signup_layout.addSpacing(20)
        self.signup_btn = QPushButton("Create Account")
        self.signup_btn.setFixedHeight(45)
        self.signup_btn.setStyleSheet("background-color: #CF6679; color: black; font-weight: bold; border-radius: 10px;")
        self.signup_btn.clicked.connect(lambda: asyncio.ensure_future(self._handle_signup()))
        signup_layout.addWidget(self.signup_btn)
        signup_layout.addStretch()
        
        # Page 2: Settings
        settings_page = QWidget()
        settings_layout = QVBoxLayout(settings_page)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.addWidget(QLabel("Gemini API Key"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setStyleSheet(self._get_input_style())
        settings_layout.addWidget(self.api_key_input)
        settings_layout.addSpacing(15)
        settings_layout.addWidget(QLabel("GCP Project ID"))
        self.project_id_input = QLineEdit()
        self.project_id_input.setStyleSheet(self._get_input_style())
        settings_layout.addWidget(self.project_id_input)
        settings_layout.addStretch()
        
        self.pages.addWidget(login_page)
        self.pages.addWidget(signup_page)
        self.pages.addWidget(settings_page)
        layout.addWidget(self.pages)
        
        # Footer
        self.start_btn = QPushButton("LOGIN TO LAUNCH")
        self.start_btn.setEnabled(False)
        self.start_btn.setFixedHeight(55)
        self.start_btn.setStyleSheet("background-color: #555; color: #888; font-size: 16px; font-weight: bold; border-radius: 15px;")
        self.start_btn.clicked.connect(self._handle_launch)
        layout.addWidget(self.start_btn)
        
        # Show the window by default
        self.show()
        
        # Use a QTimer to allow the window to render completely before checking auto-login
        QTimer.singleShot(100, self._load_current_settings)

    def _get_nav_style(self, active):
        if active:
            return "QPushButton { background-color: #333; color: #BB86FC; border-radius: 10px; border: 1px solid #BB86FC; font-weight: bold; }"
        return "QPushButton { background-color: transparent; color: #888; border: none; }"

    def _get_input_style(self):
        return "QLineEdit { background-color: #2C2C31; border: 1px solid #3D3D42; border-radius: 8px; padding: 10px; color: white; }"

    def _switch_page(self, index):
        self.pages.setCurrentIndex(index)
        for i, btn in enumerate([self.btn_login, self.btn_signup, self.btn_settings]):
            btn.setChecked(i == index)
            btn.setStyleSheet(self._get_nav_style(i == index))

    def _load_current_settings(self):
        load_dotenv()
        self.api_key_input.setText(os.getenv("GEMINI_API_KEY", ""))
        self.project_id_input.setText(os.getenv("GCP_PROJECT_ID", ""))
        
        # Auto-login check
        saved_token = os.getenv("ID_TOKEN")
        saved_user_id = os.getenv("USER_ID")
        saved_name = os.getenv("USER_NAME", "User")
        
        if saved_token and saved_user_id and saved_token != "mock_token":
            print("🔄 Auto-login triggered based on saved .env credentials.")
            settings = {
                "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
                "PORCUPINE_ACCESS_KEY": os.getenv("PORCUPINE_ACCESS_KEY", ""),
                "GCP_PROJECT_ID": os.getenv("GCP_PROJECT_ID", ""),
                "USER_ID": saved_user_id,
                "USER_NAME": saved_name,
                "ID_TOKEN": saved_token
            }
            # Instead of QTimer, we just emit immediately. The App handles the hide/show logic.
            # We delay slightly to allow __main__ to hook up the signal.
            asyncio.get_event_loop().call_later(0.5, lambda: self.ready_to_start.emit(settings))
            asyncio.get_event_loop().call_later(0.5, self.hide)
        else:
            self.show()

    async def _handle_login(self):
        email, password = self.email_input.text().strip(), self.pass_input.text().strip()
        if not email or not password: return
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Authenticating...")
        res = await self.auth_service.login(email, password)
        if res["success"]:
            self.login_btn.setText("Logged In ✅")
            self.start_btn.setEnabled(True)
            self.start_btn.setText("LAUNCH SUVI")
            self.start_btn.setStyleSheet("background-color: #BB86FC; color: #000; font-size: 16px; font-weight: bold; border-radius: 15px;")
        else:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Log In")
            QMessageBox.critical(self, "Auth Failed", res["error"])

    async def _handle_signup(self):
        email, password, name = self.signup_email.text().strip(), self.signup_pass.text().strip(), self.name_input.text().strip()
        if not email or not password or not name: return
        self.signup_btn.setEnabled(False)
        res = await self.auth_service.sign_up(email, password, name)
        if res["success"]:
            QMessageBox.information(self, "Success", "Account created. Please log in.")
            self._switch_page(0)
        else:
            self.signup_btn.setEnabled(True)
            QMessageBox.critical(self, "Signup Failed", res["error"])

    def _handle_launch(self):
        settings = {
            "GEMINI_API_KEY": self.api_key_input.text().strip(),
            "GCP_PROJECT_ID": self.project_id_input.text().strip(),
            "USER_ID": self.auth_service.get_current_user_id(),
            "ID_TOKEN": self.auth_service.get_id_token()
        }
        self.ready_to_start.emit(settings)
        self.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
