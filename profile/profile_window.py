# -*- coding: utf-8 -*-
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QFrame, QLineEdit, QMessageBox
)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt
from profile.add_profile_window import AddProfileWindow
from profile.profiles_db import add_profile, get_all_profiles, init_db


class ProfileWindow(QWidget):
    """📘 مكتبة البروفايلات - النسخة المستقرة الأصلية"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #F1F2F1;")
        self.setMinimumSize(1000, 600)

        init_db()

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # ======= القائمة اليسرى =======
        left_panel = QVBoxLayout()
        left_panel.setSpacing(8)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 بحث عن بروفايل...")
        self.search_box.textChanged.connect(self.filter_profiles)
        self.search_box.setFixedHeight(34)

        self.profile_list = QListWidget()
        self.profile_list.setStyleSheet("""
            QListWidget {
                background: #FFFFFF;
                border: 1px solid #C8C9C8;
                border-radius: 6px;
            }
            QListWidget::item {
                padding: 8px;
                margin: 4px;
                border-radius: 6px;
            }
            QListWidget::item:selected {
                background-color: rgba(230, 126, 34, 100);
                color: white;
            }
        """)
        self.profile_list.itemSelectionChanged.connect(self.show_profile_details)

        self.btn_add = QPushButton("📂 استيراد بروفايل جديد")
        self.btn_add.setFixedHeight(36)
        self.btn_add.clicked.connect(self.open_add_profile_dialog)

        left_panel.addWidget(self.search_box)
        left_panel.addWidget(self.profile_list, 1)
        left_panel.addWidget(self.btn_add)

        # ======= البطاقة اليمنى =======
        right_panel = QVBoxLayout()
        right_panel.setContentsMargins(10, 10, 10, 10)

        self.detail_card = QFrame()
        self.detail_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #C8C9C8;
                border-radius: 10px;
            }
        """)
        card_layout = QVBoxLayout(self.detail_card)
        card_layout.setContentsMargins(15, 15, 15, 15)

        self.preview_label = QLabel()
        self.preview_label.setFixedSize(240, 240)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background:#F8F8F8;border:1px solid #DDD;border-radius:8px;")
        card_layout.addWidget(self.preview_label, alignment=Qt.AlignCenter)

        self.lbl_name = QLabel("الاسم: -")
        self.lbl_code = QLabel("الكود: -")
        self.lbl_company = QLabel("الشركة: -")
        self.lbl_size = QLabel("الأبعاد: -")
        self.lbl_date = QLabel("📅 تاريخ الإضافة: -")

        for lbl in (self.lbl_name, self.lbl_code, self.lbl_company, self.lbl_size, self.lbl_date):
            lbl.setStyleSheet("font-family: Roboto; color: #333; font-size: 11pt;")
            card_layout.addWidget(lbl)

        card_layout.addStretch(1)

        self.btn_load = QPushButton("🟢 تحميل في العارض")
        self.btn_delete = QPushButton("🗑️ حذف من المكتبة")

        self.btn_load.clicked.connect(self.load_in_viewer)
        self.btn_delete.clicked.connect(self.delete_selected_profile)

        btns = QHBoxLayout()
        btns.addWidget(self.btn_load)
        btns.addWidget(self.btn_delete)
        card_layout.addLayout(btns)

        # رسالة ترحيب افتراضية
        self.placeholder_label = QLabel("👋 اختر بروفايل من القائمة لعرض التفاصيل")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("color: #888; font-family: Roboto; font-size: 11pt;")

        self.placeholder_frame = QFrame()
        ph_layout = QVBoxLayout(self.placeholder_frame)
        ph_layout.addStretch(1)
        ph_layout.addWidget(self.placeholder_label, alignment=Qt.AlignCenter)
        ph_layout.addStretch(1)

        right_panel.addWidget(self.placeholder_frame, 1)
        right_panel.addWidget(self.detail_card, 1)
        self.detail_card.hide()

        main_layout.addLayout(left_panel, 0)
        main_layout.addLayout(right_panel, 1)

        self.load_profiles()

    def load_profiles(self):
        self.profile_list.clear()
        for row in get_all_profiles():
            pid, name, code, company, size, fpath, thumb, src, date = row
            item = QListWidgetItem(f"{name}\n{company} — {size}")
            icon_path = thumb if thumb and os.path.exists(thumb) else "assets/icons/dxf.png"
            item.setIcon(QIcon(icon_path))
            item.setData(Qt.UserRole, row)
            self.profile_list.addItem(item)

    def filter_profiles(self, text):
        for i in range(self.profile_list.count()):
            item = self.profile_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def show_profile_details(self):
        selected = self.profile_list.currentItem()
        if not selected:
            self.detail_card.hide()
            self.placeholder_frame.show()
            return

        self.placeholder_frame.hide()
        self.detail_card.show()
        pid, name, code, company, size, fpath, thumb, src, date = selected.data(Qt.UserRole)
        self.lbl_name.setText(f"الاسم: {name}")
        self.lbl_code.setText(f"الكود: {code}")
        self.lbl_company.setText(f"الشركة: {company}")
        self.lbl_size.setText(f"الأبعاد: {size}")
        self.lbl_date.setText(f"📅 تاريخ الإضافة: {date}")

        if thumb and os.path.exists(thumb):
            self.preview_label.setPixmap(QPixmap(thumb).scaled(240, 240, Qt.KeepAspectRatio))
        else:
            self.preview_label.setPixmap(QPixmap("assets/icons/dxf.png").scaled(240, 240, Qt.KeepAspectRatio))

    def load_in_viewer(self):
        selected = self.profile_list.currentItem()
        if selected:
            name = selected.text().split("\n")[0]
            QMessageBox.information(self, "تحميل", f"سيتم لاحقاً تحميل البروفايل '{name}' في العارض.")

    def delete_selected_profile(self):
        selected = self.profile_list.currentItem()
        if not selected:
            return
        reply = QMessageBox.question(self, "تأكيد", "هل تريد حذف هذا البروفايل؟", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            pid, name, *_ = selected.data(Qt.UserRole)
            import sqlite3
            from profile.profiles_db import DB_PATH
            conn = sqlite3.connect(DB_PATH)
            conn.execute("DELETE FROM profiles WHERE id=?", (pid,))
            conn.commit()
            conn.close()
            self.load_profiles()
            self.detail_card.hide()
            self.placeholder_frame.show()
            QMessageBox.information(self, "تم الحذف", f"🗑️ تم حذف '{name}' من المكتبة.")

    def open_add_profile_dialog(self):
        dlg = AddProfileWindow(self)
        dlg.profile_ready.connect(self._on_profile_added)
        dlg.show()
        self._dlg_ref = dlg

    def _on_profile_added(self, data):
        add_profile(data)
        self.load_profiles()
        QMessageBox.information(self, "تم الحفظ", f"✅ تم إضافة '{data['name']}' إلى المكتبة.")
