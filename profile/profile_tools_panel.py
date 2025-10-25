# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFrame
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize, Signal


class ProfileToolsPanel(QWidget):
    """🧩 لوحة أدوات البروفايل (Profile Tools) — نسخة من SketchToolsPanel"""
    tool_selected = Signal(str)

    def __init__(self, vtk_viewer=None, parent=None):
        super().__init__(parent)
        self.vtk_viewer = vtk_viewer
        self.active_tool = None
        self.buttons = {}

        # 🔹 أدوات البروفايل الأساسية (بدل أدوات الرسم)
        profile_tools = [
            ("select.png", "تحديد بروفايل", "select"),
            ("add_profile.png", "إضافة بروفايل", "add_profile"),
            ("edit_profile.png", "تعديل بروفايل", "edit_profile"),
            ("import.png", "استيراد DXF", "import_dxf"),
        ]

        # 🔹 أدوات مكتبة البروفايلات (بدل أدوات التعديل)
        library_tools = [
            ("library.png", "مكتبة البروفايلات", "library"),
            ("save.png", "حفظ", "save_profile"),
            ("delete.png", "حذف", "delete_profile"),
        ]

        # 🔹 أداة الخروج أو إلغاء التحديد
        extra_tools = [
            ("cancel.png", "إلغاء", "none")
        ]

        # 🎨 نفس تنسيق Sketch
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

        # 🔸 إضافة أدوات البروفايل
        for icon_file, label, tool_id in profile_tools:
            btn = self._make_button(icon_file, label, tool_id)
            layout.addWidget(btn)

        # ┇ فاصل مثل Fusion
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #C8C9C8; margin: 0 10px;")
        separator.setFixedHeight(40)
        layout.addWidget(separator)

        # 📚 أدوات المكتبة
        for icon_file, label, tool_id in library_tools:
            btn = self._make_button(icon_file, label, tool_id)
            layout.addWidget(btn)

        # ┇ فاصل صغير قبل الإلغاء
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setStyleSheet("color: #C8C9C8; margin: 0 8px;")
        separator2.setFixedHeight(36)
        layout.addWidget(separator2)

        # ❌ زر الإلغاء
        for icon_file, label, tool_id in extra_tools:
            btn = self._make_button(icon_file, label, tool_id)
            layout.addWidget(btn)

        layout.addStretch()

    # 🔸 إنشاء زر قياسي
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

    # 🔹 تفعيل أداة معينة
    def activate_tool(self, tool_name):
        """تفعيل أداة وتحديث المظهر"""
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

        if self.vtk_viewer:
            self.vtk_viewer.set_active_tool(self.active_tool)
        self.tool_selected.emit(self.active_tool or "")
