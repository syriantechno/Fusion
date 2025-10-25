# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from profile.profiles_db import update_profile


class EditProfileWindow(QWidget):
    """🟠 نافذة تعديل بيانات البروفايل"""
    profile_updated = Signal(int)

    def __init__(self, pid, name, code, company, size, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تعديل بيانات البروفايل")
        self.setFixedSize(400, 320)
        self.setStyleSheet("""
            QWidget {
                background-color: #F1F2F1;
                font-family: Roboto;
                font-size: 10pt;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #C8C9C8;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton {
                color: white;
                border-radius: 6px;
                height: 32px;
                font-weight: bold;
            }
        """)

        self.pid = pid

        # التخطيط العام
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # الحقول
        self.name_input = self._create_input("اسم البروفايل", name)
        self.code_input = self._create_input("الكود", code)
        self.company_input = self._create_input("الشركة", company)
        self.size_input = self._create_input("الأبعاد (mm)", size)

        # الأزرار
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("💾 حفظ التعديلات")
        self.btn_cancel = QPushButton("إلغاء")

        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
            }
            QPushButton:hover { background-color: #2ECC71; }
        """)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
            }
            QPushButton:hover { background-color: #EC7063; }
        """)

        self.btn_save.clicked.connect(self.save_changes)
        self.btn_cancel.clicked.connect(self.close)

        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    # ===========================
    # دالة إنشاء الحقول
    # ===========================
    def _create_input(self, label_text, value):
        lbl = QLabel(label_text)
        lbl.setAlignment(Qt.AlignRight)
        inp = QLineEdit(value)
        inp.setFixedHeight(32)

        container = QVBoxLayout()
        container.addWidget(lbl)
        container.addWidget(inp)

        self.layout().addLayout(container)
        return inp

    # ===========================
    # حفظ التعديلات
    # ===========================
    def save_changes(self):
        name = self.name_input.text().strip()
        code = self.code_input.text().strip()
        company = self.company_input.text().strip()
        size = self.size_input.text().strip()

        if not name:
            QMessageBox.warning(self, "تنبيه", "يجب إدخال اسم البروفايل.")
            return

        # تحديث البيانات في قاعدة البيانات
        update_profile(self.pid, name, code, company, size)

        QMessageBox.information(self, "تم الحفظ", "✅ تم تعديل بيانات البروفايل بنجاح.")
        self.profile_updated.emit(self.pid)
        self.close()
