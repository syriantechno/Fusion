# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont


class BaseToolWindow(QWidget):
    """
    🪟 نافذة أساسية موحّدة لجميع النوافذ في النظام
    (ProfileWindow, ToolManagerWindow, ExtrudeWindow, ...)
    """

    def __init__(self, title="نافذة", parent=None):
        super().__init__(parent)
        self.setObjectName("BaseToolWindow")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(520, 460)

        # 🟫 الإطار الأساسي
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #F1F2F1;
                border-radius: 10px;
                border: 1px solid #C8C9C8;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.addWidget(container)

        # 🔸 محتوى النافذة
        inner_layout = QVBoxLayout(container)
        inner_layout.setContentsMargins(20, 20, 20, 20)
        inner_layout.setSpacing(15)

        # 🟧 العنوان
        title_label = QLabel(title)
        title_label.setFont(QFont("Roboto", 15, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #333333;")
        inner_layout.addWidget(title_label)

        # 🧱 المساحة الداخلية (يملؤها subclass)
        self.content_area = QFrame()
        self.content_area.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 8px;
                border: 1px solid #D0D0D0;
            }
        """)
        inner_layout.addWidget(self.content_area, 1)

        # 🔘 الأزرار (OK / Cancel)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setAlignment(Qt.AlignRight)

        self.btn_cancel = QPushButton("إلغاء")
        self.btn_cancel.setFixedHeight(36)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border-radius: 6px;
                padding: 6px 20px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #FF6B5B; }
        """)
        self.btn_cancel.clicked.connect(self.close)

        self.btn_ok = QPushButton("موافق")
        self.btn_ok.setFixedHeight(36)
        self.btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border-radius: 6px;
                padding: 6px 20px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2ECC71; }
        """)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        inner_layout.addLayout(btn_layout)
