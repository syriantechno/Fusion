# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFrame
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize, Signal

from profile.profile_manager_window import ProfileManagerWindow
from profile.add_profile_window import AddProfileWindow


class ProfileToolsPanel(QWidget):
    """🧩 لوحة أدوات البروفايل (Profile Tools) — نسخة Fusion Style"""

    tool_selected = Signal(str)

    def __init__(self, vtk_viewer=None, parent=None):
        super().__init__(parent)
        self.vtk_viewer = vtk_viewer
        self.active_tool = None
        self.buttons = {}

        # 🔹 الأدوات الأساسية
        profile_tools = [
            ("select.png", "تحديد بروفايل", "select"),
            ("add_profile.png", "إضافة بروفايل", "add_profile"),
            ("edit_profile.png", "تعديل بروفايل", "edit_profile"),
            ("library.png", "مكتبة البروفايلات", "library"),  # ← فتح النافذة
        ]

        # 🔹 أدوات إضافية
        extra_tools = [
            ("cancel.png", "إلغاء", "none")
        ]

        # 🎨 ستايل عام
        self.setStyleSheet("""
            QWidget {
                background-color: #F1F2F1;
                border-bottom: 1px solid #C8C9C8;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 6px;
                margin: 4px;
            }
            QPushButton:hover {
                background-color: rgba(230, 126, 34, 0.1);
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # 🧱 أزرار الأدوات
        for icon_file, label, tool_id in profile_tools:
            btn = self._make_button(icon_file, label, tool_id)
            layout.addWidget(btn)

        layout.addWidget(self._make_separator())

        # ❌ زر الإلغاء
        for icon_file, label, tool_id in extra_tools:
            btn = self._make_button(icon_file, label, tool_id)
            layout.addWidget(btn)

        layout.addStretch()

    # ------------------------------------------------------------
    # 🔹 زر موحد
    # ------------------------------------------------------------
    def _make_button(self, icon_file, label, tool_id):
        btn = QPushButton()
        btn.setIcon(QIcon(f"assets/icons/{icon_file}"))
        btn.setToolTip(label)
        btn.setCheckable(True)
        btn.setIconSize(QSize(36, 36))
        btn.setFixedSize(52, 52)
        btn.clicked.connect(lambda checked, t=tool_id: self.activate_tool(t))
        self.buttons[tool_id] = btn
        return btn

    # ------------------------------------------------------------
    # 🔹 فاصل رأسي
    # ------------------------------------------------------------
    def _make_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("color: #C8C9C8; margin: 0 10px;")
        sep.setFixedHeight(40)
        return sep

    # ------------------------------------------------------------
    # 🔹 تفعيل الأداة
    # ------------------------------------------------------------
    def activate_tool(self, tool_name):
        """تفعيل أداة معينة"""
        for name, btn in self.buttons.items():
            btn.setChecked(name == tool_name)
            if name == tool_name and tool_name != "none":
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(230, 126, 34, 0.2);
                        border-radius: 6px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border: none;
                    }
                    QPushButton:hover {
                        background-color: rgba(230, 126, 34, 0.1);
                    }
                """)

        self.active_tool = None if tool_name == "none" else tool_name
        print(f"🟢 [ProfileTools] Active tool = {self.active_tool or 'None'}")

        # 🪟 فتح نافذة إدارة البروفايلات عند الضغط على library
        if tool_name == "library":
            self.open_profile_manager()

            # 🧩 فتح نافذة إضافة بروفايل جديد
        if tool_name == "add_profile":
            self.open_add_profile_window()

        if self.vtk_viewer:
            self.vtk_viewer.set_active_tool(self.active_tool)

        self.tool_selected.emit(self.active_tool or "")

    # ------------------------------------------------------------
    # 🔹 فتح نافذة إدارة البروفايلات
    # ------------------------------------------------------------

    def open_profile_manager(self):
        """فتح نافذة مكتبة البروفايلات الجديدة"""
        print("📂 فتح نافذة مكتبة البروفايلات (الإصدار الجديد)...")
        try:
            self.profile_window = ProfileManagerWindow(parent=self)
            self.profile_window.show()
            print("🟢 [UI] تم فتح نافذة مكتبة البروفايلات الجديدة بنجاح.")
        except Exception as e:
            print("🔥 [Error] فشل في فتح مكتبة البروفايلات:", e)

    def open_add_profile_window(self):
        """فتح نافذة إضافة بروفايل جديد"""
        print("📂 فتح نافذة إضافة بروفايل جديد...")
        try:
            self.add_window = AddProfileWindow(parent=self)
            self.add_window.show()
            print("🟢 [UI] تم فتح نافذة الإضافة بنجاح.")
        except Exception as e:
            print("🔥 [Error] فشل في فتح نافذة الإضافة:", e)
