# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt


class BaseToolWindow(QWidget):
    """
    🪟 نموذج موحّد لجميع النوافذ (Fusion-style خفيف)
    """

    def __init__(self, title="PROFILE MANAGER", parent=None):
        super().__init__(parent)
        self.setObjectName("BaseToolWindow")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # ✅ تحسين التحكم بالحجم والتمدد
        self.setMinimumSize(520, 700)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # 🟫 الإطار الأساسي (بدون ظل أو radius مبالغ)
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #F1F2F1;
                border: 1px solid #C8C9C8;
                border-radius: 0px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

        inner_layout = QVBoxLayout(container)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(0)

        # 🩶 شريط علوي (Fusion-style)
        header = QFrame()
        header.setFixedHeight(32)
        header.setStyleSheet("""
            QFrame {
                background-color: #F6F6F6;
                border-top: none;
                border-left: none;
                border-right: none;
                border-bottom: 1px solid #C8C9C8;
                padding-left: 6px;
                padding-right: 6px;
            }
        """)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 0, 10, 0)
        header_layout.setSpacing(8)

        # 🔸 النقطة الكبيرة
        dot_label = QLabel("•")
        dot_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 18px;
                font-weight: 900;
                margin-top: 4px;
                background-color: #F6F6F6;
            }
        """)

        # 🧱 العنوان
        self.title_label = QLabel(title.upper())
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #333;
                font-family: "Roboto";
                font-size: 11.5px;
                font-weight: 600;
                letter-spacing: 0.5px;
                border: none;
            }
        """)

        # ➤ السهم في النهاية
        arrow_label = QLabel("«")
        arrow_label.setStyleSheet("""
            QLabel {
                color: #444;
                font-size: 13px;
                font-weight: 600;
                background-color: #F6F6F6;
            }
        """)

        header_layout.addWidget(dot_label)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(arrow_label)
        inner_layout.addWidget(header)

        # 🧱 منطقة المحتوى
        self.content_area = QFrame()
        self.content_area.setStyleSheet("""
            QFrame {
                background-color: #F1F2F1;
                border: none;
                border-radius: 0px;
            }
        """)
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        inner_layout.addWidget(self.content_area, 1)

        # 🔘 الخط الفاصل فوق الأزرار
        footer_line = QFrame()
        footer_line.setFrameShape(QFrame.HLine)
        footer_line.setFrameShadow(QFrame.Plain)
        footer_line.setStyleSheet("""
            QFrame {
                background-color: #C8C9C8;
                height: 1px;
                max-height: 1px;
                border: none;
            }
        """)
        inner_layout.addWidget(footer_line)

        # 🔘 الأزرار السفلية
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(10, 8, 10, 8)
        btn_layout.setSpacing(8)
        btn_layout.setAlignment(Qt.AlignRight)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFixedHeight(30)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #D0D0D0;
                color: #333;
                border-radius: 3px;
                padding: 4px 16px;
                font-weight: 500;
                border: none;
            }
            QPushButton:hover { background-color: #BDBDBD; }
        """)
        self.btn_cancel.clicked.connect(self.close)

        self.btn_ok = QPushButton("OK")
        self.btn_ok.setFixedHeight(30)
        self.btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border-radius: 3px;
                padding: 4px 16px;
                font-weight: 600;
                border: none;
            }
            QPushButton:hover { background-color: #2ECC71; }
        """)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        inner_layout.addLayout(btn_layout)

        # ⚙️ ضبط الحجم النهائي ديناميكياً
        self.adjustSize()
    # --------------------------------------------------------------
    # 🧩 دالة عامة لعرض الرسائل الموحدة (تحذير / خطأ / نجاح / معلومة)
    # --------------------------------------------------------------
    def show_message(self, title, text, level="info"):
        """إظهار مربع رسالة موحّد بالستايل العام"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)

        # 🎨 تحديد اللون حسب نوع الرسالة
        if level == "error":
            color = "#C0392B"  # أحمر ناعم
        elif level == "warn":
            color = "#E67E22"  # برتقالي
        elif level == "success":
            color = "#27AE60"  # أخضر
        else:
            color = "#3498DB"  # أزرق للمعلومات

        msg.setIcon({
                        "error": QMessageBox.Critical,
                        "warn": QMessageBox.Warning,
                        "success": QMessageBox.Information,
                        "info": QMessageBox.Information
                    }[level])

        # ⚙️ ستايل واضح على الخلفية الفاتحة
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: #F1F2F1;
                color: #333333;                 /* ← نص داكن */
                font-family: "Roboto";
                font-size: 12.5px;
            }}
            QLabel {{
                color: #333333;                 /* ← يضمن وضوح النص */
            }}
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 18px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #F39C12;
            }}
        """)

        msg.exec()

    # --------------------------------------------------------------
    # 🧩 دالة تأكيد موحدة (Confirm Dialog)
    # --------------------------------------------------------------
    def ask_confirm(self, title: str, text: str) -> bool:
        """عرض مربع تأكيد Yes/No موحّد بنفس ستايل البرنامج"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.Question)

        yes_btn = msg.addButton("OK", QMessageBox.AcceptRole)
        no_btn = msg.addButton("Cancel", QMessageBox.RejectRole)

        msg.setStyleSheet("""
            QMessageBox {
                background-color: #F1F2F1;
                color: #333;
                font-family: "Roboto";
                font-size: 12.5px;
            }
            QPushButton {
                border: none;
                border-radius: 4px;
                padding: 5px 18px;
                font-weight: 500;
                font-family: "Roboto";
            }
            QPushButton:nth-child(1) { /* OK button */
                background-color: #27AE60;
                color: white;
            }
            QPushButton:nth-child(1):hover {
                background-color: #2ECC71;
            }
            QPushButton:nth-child(2) { /* Cancel button */
                background-color: #D0D0D0;
                color: #333;
            }
            QPushButton:nth-child(2):hover {
                background-color: #BDBDBD;
            }
        """)

        msg.exec()
        return msg.clickedButton() == yes_btn

    # --------------------------------------------------------------
    # 🧩 دالة لتعيين محتوى النافذة (Fusion-style)
    # --------------------------------------------------------------
    def set_content_widget(self, widget: QWidget):
        """تعيين محتوى النافذة داخل منطقة content_area"""
        # إذا ما كان للـ content_area تخطيط، أنشئ واحد
        if not self.content_area.layout():
            layout = QVBoxLayout(self.content_area)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
        else:
            layout = self.content_area.layout()

        # حذف أي عناصر سابقة
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # إضافة المحتوى الجديد
        layout.addWidget(widget)



