# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFrame
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize, Signal


class SketchToolsPanel(QWidget):
    """🎨 لوحة أدوات الرسم (Sketch Tools) - Fusion Style"""
    tool_selected = Signal(str)

    def __init__(self, vtk_viewer=None, parent=None):
        super().__init__(parent)
        self.vtk_viewer = vtk_viewer
        self.active_tool = None
        self.buttons = {}

        # 🔹 أدوات الرسم الأساسية
        draw_tools = [
            ("select.png", "تحديد (Select)", "select"),
            ("line.png", "خط", "line"),
            ("circle.png", "دائرة", "circle"),
            ("rect.png", "مستطيل", "rect"),
            ("arc.png", "قوس", "arc"),
        ]

        # 🔹 أدوات التعديل (مثل Fusion)
        modify_tools = [
            ("trim.png", "قص (Trim)", "trim"),
            ("offset.png", "إزاحة (Offset)", "offset"),
            ("mirror.png", "انعكاس (Mirror)", "mirror"),
            ("fillet.png", "تدوير الزاوية (Fillet)", "fillet"),
        ]

        # 🔹 أداة الحذف
        extra_tools = [
            ("delete.png", "إلغاء", "none")
        ]

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

        # 🎨 إضافة أدوات الرسم
        for icon_file, label, tool_id in draw_tools:
            btn = self._make_button(icon_file, label, tool_id)
            layout.addWidget(btn)

        # ┇ فاصل عمودي فاتح مثل Fusion
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #C8C9C8; margin: 0 10px;")
        separator.setFixedHeight(40)
        layout.addWidget(separator)

        # ✂️ إضافة أدوات التعديل
        for icon_file, label, tool_id in modify_tools:
            btn = self._make_button(icon_file, label, tool_id)
            layout.addWidget(btn)

        # فاصل صغير قبل أداة الحذف
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

    # 🧱 إنشاء زر قياسي
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

    # 🔸 تفعيل أداة معينة
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
        print(f"🟢 [SketchTools] Active tool = {self.active_tool or 'None'}")

        if self.vtk_viewer:
            self.vtk_viewer.set_active_tool(self.active_tool)
        self.tool_selected.emit(self.active_tool or "")
