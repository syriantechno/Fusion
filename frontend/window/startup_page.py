from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt

class StartupPage(QFrame):
    """صفحة البداية (Startup)"""
    def __init__(self, on_start_callback=None):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("👋 مرحباً بك في AlumProCNC")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; color: #566273; font-weight: bold;")

        start_btn = QPushButton("ابدأ العمل")
        start_btn.setFixedSize(180, 46)
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #E67E22;
                color: white;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F39C12;
            }
        """)
        if on_start_callback:
            start_btn.clicked.connect(on_start_callback)

        layout.addWidget(title)
        layout.addWidget(start_btn, alignment=Qt.AlignCenter)
