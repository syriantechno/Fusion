# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFrame
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize, Signal


class CamToolsPanel(QWidget):
    """⚙️ لوحة أدوات الـ CAM (التصنيع / المحاكاة / التوليد) — Fusion Style"""

    tool_selected = Signal(str)

    def __init__(self, vtk_viewer=None, parent=None):
        super().__init__(parent)
        self.vtk_viewer = vtk_viewer
        self.active_tool = None
        self.buttons = {}

        # 🔹 أدوات العمليات الأساسية (عمليات التشغيل)
        cam_ops = [
            ("setup.png", "إعداد التشغيل", "setup"),
            ("drill.png", "عملية الثقب", "drill"),
            ("pocket.png", "عملية التفريغ (Pocket)", "pocket"),
            ("contour.png", "عملية المحيط (Contour)", "contour"),
        ]

        # 🔹 أدوات المحاكاة والمعالجة
        simulation_ops = [
            ("simulate.png", "محاكاة التشغيل", "simulate"),
            ("verify.png", "تحقق من المسار", "verify"),
            ("toolpath.png", "عرض المسار", "show_path"),
            ("gcode.png", "توليد G-Code", "generate_gcode"),
        ]

        # 🔹 أداة الإلغاء / الخروج
        extra_tools = [
            ("cancel.png", "إلغاء", "none")
        ]

        # 🎨 تنسيق موحد
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
                background-color: rgba(230,126,34,0.1);
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # 🟧 أدوات التشغيل
        for icon_file, label, tool_id in cam_ops:
            btn = self._make_button(icon_file, label, tool_id)
            layout.addWidget(btn)

        layout.addWidget(self._make_separator())

        # 🟦 أدوات المحاكاة والمعالجة
        for icon_file, label, tool_id in simulation_ops:
            btn = self._make_button(icon_file, label, tool_id)
            layout.addWidget(btn)

        layout.addWidget(self._make_separator())

        # ❌ زر الإلغاء
        for icon_file, label, tool_id in extra_tools:
            btn = self._make_button(icon_file, label, tool_id)
            layout.addWidget(btn)

        layout.addStretch()

    # ------------------------------------------------------------
    # 🔹 إنشاء زر أيقونة موحد
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
    # 🔹 فاصل عمودي بين المجموعات
    # ------------------------------------------------------------
    def _make_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("color: #C8C9C8; margin: 0 10px;")
        sep.setFixedHeight(40)
        return sep

    # ------------------------------------------------------------
    # 🔹 تفعيل أداة معينة
    # ------------------------------------------------------------
    def activate_tool(self, tool_name):
        """تفعيل الأداة وتحديث مظهر الأزرار"""
        for name, btn in self.buttons.items():
            btn.setChecked(name == tool_name)
            if name == tool_name and tool_name != "none":
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(230,126,34,0.2);
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
                        background-color: rgba(230,126,34,0.1);
                    }
                """)

        self.active_tool = None if tool_name == "none" else tool_name
        print(f"🟢 [CAMTools] Active tool = {self.active_tool or 'None'}")

        if self.vtk_viewer:
            self.vtk_viewer.set_active_tool(self.active_tool)

        self.tool_selected.emit(self.active_tool or "")

