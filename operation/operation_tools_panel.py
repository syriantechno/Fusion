# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFrame
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize, Signal


class OperationToolsPanel(QWidget):
    """⚙️ لوحة عمليات التشغيل (Operations Panel) — Fusion style"""

    tool_selected = Signal(str)

    def __init__(self, vtk_viewer=None, parent=None):
        super().__init__(parent)
        self.vtk_viewer = vtk_viewer
        self.active_tool = None
        self.buttons = {}

        # 🧱 أدوات العمليات الهندسية (نفس منطق Fusion)
        operation_tools = [
            ("extrude.png", "إكسترود (Extrude)", "extrude"),
            ("cut.png", "قطع (Cut)", "cut"),
            ("hole.png", "ثقب (Hole)", "hole"),
            ("pattern.png", "تكرار (Pattern)", "pattern"),
            ("combine.png", "دمج / طرح (Combine)", "combine"),
        ]

        # 🧰 أدوات إضافية
        extra_ops = [
            ("measure.png", "قياس", "measure"),
            ("inspect.png", "تفحص", "inspect"),
        ]

        # ❌ إلغاء / عودة
        extra_tools = [
            ("cancel.png", "إلغاء", "none")
        ]

        # 🎨 ستايل موحّد (نفس Sketch/Shape)
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

        # 🟧 عمليات هندسية
        for icon_file, label, tool_id in operation_tools:
            btn = self._make_button(icon_file, label, tool_id)
            layout.addWidget(btn)

        layout.addWidget(self._make_separator())

        # 🟦 أدوات إضافية
        for icon_file, label, tool_id in extra_ops:
            btn = self._make_button(icon_file, label, tool_id)
            layout.addWidget(btn)

        layout.addWidget(self._make_separator())

        # ❌ إلغاء
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
    # 🔹 فاصل عمودي أنيق
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
        print(f"🟢 [OperationTools] Active tool = {self.active_tool or 'None'}")

        if self.vtk_viewer:
            self.vtk_viewer.set_active_tool(self.active_tool)

        self.tool_selected.emit(self.active_tool or "")
