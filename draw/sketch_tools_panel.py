# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize, Signal


class SketchToolsPanel(QWidget):
    """🎨 لوحة أدوات الرسم (Sketch Tools) - Fusion Style"""
    tool_selected = Signal(str)  # ← إرسال إشارة عند اختيار الأداة

    def __init__(self, vtk_viewer=None, parent=None):
        super().__init__(parent)
        self.vtk_viewer = vtk_viewer
        self.active_tool = None
        self.buttons = {}

        # 🔹 تعريف الأدوات
        self.sketch_tools = [
            ("line.png", "خط", "line"),
            ("circle.png", "دائرة", "circle"),
            ("rect.png", "مستطيل", "rect"),
            ("arc.png", "قوس", "arc"),
            ("delete.png", "إلغاء", "none")
        ]

        # 🔹 تنسيق عام
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

        # 🔹 إنشاء الأزرار
        for icon_file, label, tool_id in self.sketch_tools:
            btn = QPushButton()
            btn.setIcon(QIcon(f"assets/icons/{icon_file}"))
            btn.setToolTip(label)
            btn.setCheckable(True)
            btn.setIconSize(QSize(36, 36))
            btn.setFixedSize(52, 52)
            btn.clicked.connect(lambda checked, t=tool_id: self.activate_tool(t))
            layout.addWidget(btn)
            self.buttons[tool_id] = btn

        layout.addStretch()

    # 🔸 تفعيل أداة معينة
    def activate_tool(self, tool_name):
        """يُفعّل أداة محددة ويحدث المظهر"""
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

        # 🔹 حفظ الحالة الحالية
        self.active_tool = None if tool_name == "none" else tool_name
        print(f"🟢 [SketchTools] Active tool = {self.active_tool or 'None'}")

        # 🔹 إرسال الإشارة إلى العارض
        if self.vtk_viewer:
            self.vtk_viewer.set_active_tool(self.active_tool)
        self.tool_selected.emit(self.active_tool or "")
