# -*- coding: utf-8 -*-
"""
Profile Window — قسم البروفايلات الرئيسي
مستقل تماماً مثل draw/sketch_tools_panel.py
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QGridLayout, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon


class ProfileWindow(QWidget):
    """واجهة قسم البروفايلات"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ProfileWindow")
        self.setWindowTitle("Profile Library")
        self.setStyleSheet("""
            QWidget#ProfileWindow {
                background-color: #F1F2F1;
            }
            QLabel#title {
                font-size: 16px;
                font-weight: 700;
                color: #2C3E50;
                padding: 8px;
            }
            QPushButton {
                background-color: #E67E22;
                color: white;
                border-radius: 8px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #D35400;
            }
            QFrame#card {
                background: #FFFFFF;
                border: 1px solid #C8C9C8;
                border-radius: 12px;
            }
            QFrame#card:hover {
                border-color: #E67E22;
            }
        """)

        # 🔹 Layout رئيسي
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # 🔸 العنوان + زر إضافة
        header = QHBoxLayout()
        title = QLabel("📚 مكتبة البروفايلات")
        title.setObjectName("title")
        add_btn = QPushButton("➕ إضافة بروفايل")
        add_btn.clicked.connect(self._on_add_profile)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(add_btn)
        layout.addLayout(header)

        # 🔸 Scroll لعرض البطاقات
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        layout.addWidget(self.scroll)

        content = QWidget()
        self.grid = QGridLayout(content)
        self.grid.setSpacing(12)
        self.scroll.setWidget(content)

        # بطاقات مبدئية مؤقتة
        for i in range(6):
            self.grid.addWidget(self._create_card(f"Profile {i+1}", f"Code-{i+1}"), i//3, i%3)

    # ------------------------------------------------------------
    # 🟠 إنشاء بطاقة بسيطة
    # ------------------------------------------------------------
    def _create_card(self, name, code):
        card = QFrame()
        card.setObjectName("card")
        lay = QVBoxLayout(card)
        lbl = QLabel(f"{name}\n{code}")
        lbl.setAlignment(Qt.AlignCenter)
        btn = QPushButton("تحميل")
        btn.setIcon(QIcon("assets/icons/open.png"))
        btn.clicked.connect(lambda: self._on_load_profile(name))
        lay.addWidget(lbl)
        lay.addStretch()
        lay.addWidget(btn)
        return card

    # ------------------------------------------------------------
    # 🔹 الدوال الوظيفية
    # ------------------------------------------------------------
    def _on_add_profile(self):
        print("🟢 [Profile] إضافة بروفايل جديد...")

    def _on_load_profile(self, name):
        print(f"🟠 [Profile] تحميل البروفايل: {name}")
