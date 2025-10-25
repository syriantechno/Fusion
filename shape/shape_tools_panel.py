# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFrame
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize, Signal


class ShapeToolsPanel(QWidget):
    """🧱 لوحة أدوات الأشكال (Shape Tools Panel) — مطابقة لتصميم Sketch"""

    tool_selected = Signal(str)

    def __init__(self, vtk_viewer=None, parent=None):
        super().__init__(parent)
        self.vtk_viewer = vtk_viewer
        self.active_tool = None
        self.buttons = {}

        # 🔸 قائمة الأدوات الخاصة بالأشكال
        shape_tools = [
            ("box.png", "إنشاء مكعب", "box"),
            ("cylinder.png", "إنشاء أسطوانة", "cylinder"),
            ("sphere.png", "إنشاء كرة", "sphere"),
            ("cone.png", "إنشاء مخروط", "cone"),
            ("torus.png", "إنشاء طورس (حلقة)", "torus"),
        ]

        # 🔹 أدوات العمليات على الأشكال
        modify_tools = [
            ("move.png", "تحريك الشكل", "move"),
            ("rotate.png", "تدوير الشكل", "rotate"),
            ("scale.png", "تحجيم الشكل", "scale"),
            ("delete.png", "حذف الشكل", "delete"),
        ]

        # 🔹 أداة الإلغاء
        extra_tools = [
            ("cancel.png", "إلغاء التحديد", "none")
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

        # 🟧 أدوات إنشاء الأشكال
        for icon_file, label, tool_id in shape_tools:
            btn = self._make_button(icon_file, label, tool_id)
            layout.addWidget(btn)

        # ┇ فاصل
        sep = self._make_separator()
        layout.addWidget(sep)

        # 🟦 أدوات التعديل
        for icon_file, label, tool_id in modify_tools:
            btn = self._make_button(icon_file, label, tool_id)
            layout.addWidget(btn)

        # ┇ فاصل
        sep2 = self._make_separator()
        layout.addWidget(sep2)

        # ❌ إلغاء
        for icon_file, label, tool_id in extra_tools:
            btn = self._make_button(icon_file, label, tool_id)
            layout.addWidget(btn)

        layout.addStretch()

    # ------------------------------------------------------------
    # 🔹 زر قياسي مع أيقونة
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
    # 🔹 فاصل عمودي
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
        """تفعيل الأداة وتحديث المظهر"""
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
        print(f"🟢 [ShapeTools] Active tool = {self.active_tool or 'None'}")

        if self.vtk_viewer:
            self.vtk_viewer.set_active_tool(self.active_tool)

        self.tool_selected.emit(self.active_tool or "")
