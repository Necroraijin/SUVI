import os
import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QHBoxLayout, QFrame, QStackedWidget,
                             QMessageBox, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QColor, QFont, QIcon

class LoginWindow(QWidget):
    """
    The main desktop application window for SUVI.
    Handles user authentication and configuration (API keys, themes, etc.).
    """
    # Signal emitted when setup is complete and user clicks 'Start SUVI'
    ready_to_start = pyqtSignal(dict) # carries settings dict
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SUVI - Configuration & Login")
        self.setFixedSize(500, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._drag_pos = QPoint()
        self.init_ui()
        
    def init_ui(self):
        # Background container with rounded corners
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
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #888888;
                font-size: 18px;
                border: none;
            }
            QPushButton:hover { color: #FF5252; }
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        tagline = QLabel("Hands for the handless. Vision for the blind.")
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
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
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
        
        # --- Content Area (Stacked Widget) ---
        self.pages = QStackedWidget()
        
        # Page 0: Login
        login_page = QWidget()
        login_layout = QVBoxLayout(login_page)
        login_layout.setContentsMargins(0, 0, 0, 0)
        
        login_layout.addWidget(QLabel("Email"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        self.email_input.setStyleSheet(self._get_input_style())
        login_layout.addWidget(self.email_input)
        
        login_layout.addSpacing(15)
        
        login_layout.addWidget(QLabel("Password"))
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setPlaceholderText("Enter your password")
        self.pass_input.setStyleSheet(self._get_input_style())
        login_layout.addWidget(self.pass_input)
        
        login_layout.addSpacing(30)
        
        self.login_btn = QPushButton("Log In")
        self.login_btn.setFixedHeight(45)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #03DAC6;
                color: #000000;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover { background-color: #018786; }
        """)
        login_layout.addWidget(self.login_btn)
        login_layout.addStretch()

        # Page 1: Sign Up (Mock)
        signup_page = QWidget()
        signup_layout = QVBoxLayout(signup_page)
        signup_layout.setContentsMargins(0, 0, 0, 0)
        signup_layout.addWidget(QLabel("Full Name"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Your Name")
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
        signup_layout.addWidget(self.signup_btn)
        signup_layout.addStretch()
        
        # Page 2: Settings
        settings_page = QWidget()
        settings_layout = QVBoxLayout(settings_page)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        
        settings_layout.addWidget(QLabel("Gemini API Key"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("AIza...")
        self.api_key_input.setStyleSheet(self._get_input_style())
        settings_layout.addWidget(self.api_key_input)
        
        settings_layout.addSpacing(15)
        
        settings_layout.addWidget(QLabel("Porcupine Access Key"))
        self.porc_key_input = QLineEdit()
        self.porc_key_input.setPlaceholderText("Optional for wake word")
        self.porc_key_input.setStyleSheet(self._get_input_style())
        settings_layout.addWidget(self.porc_key_input)
        
        settings_layout.addSpacing(15)
        
        settings_layout.addWidget(QLabel("GCP Project ID"))
        self.project_id_input = QLineEdit()
        self.project_id_input.setPlaceholderText("your-project-id")
        self.project_id_input.setStyleSheet(self._get_input_style())
        settings_layout.addWidget(self.project_id_input)
        
        settings_layout.addStretch()
        
        self.pages.addWidget(login_page)
        self.pages.addWidget(signup_page)
        self.pages.addWidget(settings_page)
        
        layout.addWidget(self.pages)
        
        # --- Footer ---
        self.start_btn = QPushButton("LAUNCH SUVI")
        self.start_btn.setFixedHeight(55)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #BB86FC;
                color: #000000;
                font-size: 16px;
                font-weight: bold;
                border-radius: 15px;
            }
            QPushButton:hover { background-color: #9965f4; }
        """)
        self.start_btn.clicked.connect(self._handle_launch)
        layout.addWidget(self.start_btn)
        
        # Load existing env values if present
        self._load_current_settings()

    def _get_nav_style(self, active):
        if active:
            return "QPushButton { background-color: #333338; color: #BB86FC; border-radius: 10px; border: 1px solid #BB86FC; font-weight: bold; }"
        return "QPushButton { background-color: transparent; color: #888888; border: none; }"

    def _get_input_style(self):
        return """
            QLineEdit {
                background-color: #2C2C31;
                border: 1px solid #3D3D42;
                border-radius: 8px;
                padding: 10px;
                color: white;
            }
            QLineEdit:focus { border: 1px solid #BB86FC; }
        """

    def _switch_page(self, index):
        self.pages.setCurrentIndex(index)
        self.btn_login.setChecked(index == 0)
        self.btn_signup.setChecked(index == 1)
        self.btn_settings.setChecked(index == 2)
        self.btn_login.setStyleSheet(self._get_nav_style(index == 0))
        self.btn_signup.setStyleSheet(self._get_nav_style(index == 1))
        self.btn_settings.setStyleSheet(self._get_nav_style(index == 2))

    def _load_current_settings(self):
        from dotenv import load_dotenv
        load_dotenv()
        self.api_key_input.setText(os.getenv("GEMINI_API_KEY", ""))
        self.porc_key_input.setText(os.getenv("PORCUPINE_ACCESS_KEY", ""))
        self.project_id_input.setText(os.getenv("GCP_PROJECT_ID", ""))

    def _handle_launch(self):
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.critical(self, "Error", "Gemini API Key is required to launch SUVI.")
            return
            
        settings = {
            "GEMINI_API_KEY": api_key,
            "PORCUPINE_ACCESS_KEY": self.porc_key_input.text().strip(),
            "GCP_PROJECT_ID": self.project_id_input.text().strip()
        }
        
        # Update .env file locally
        with open(".env", "w") as f:
            for k, v in settings.items():
                f.write(f"{k}={v}\n")
            f.write("GCP_LOCATION=us-central1\n")
            f.write("GCP_REGION=us-central1\n")
            
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
