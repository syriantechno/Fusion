# -*- coding: utf-8 -*-
"""
toolbar_manager.py
------------------------------------------------------------
شريط الأدوات (Fusion Toolbar)
- يحتوي على أدوات الرسم الأساسية (Line, Circle, Rect, Arc)
- فاصل عمودي رمادي
- أدوات التعديل (Trim, Offset, Mirror, Fillet)
- متوافق مع واجهة Fusion-style الرمادية
------------------------------------------------------------
"""

from PySide6.QtWidgets import QToolBar, QWidget
from PySide6.QtGui import QAction

from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize
from pathlib import Path


class ToolbarManager:
    """إدارة شريط الأدوات الرئيسي في العارض"""

    def __init__(self, viewer, parent=None):
        self.viewer = viewer
        self.toolbar = self._build_toolbar(parent)
        print("✅ ToolbarManager initialized")

    # ------------------------------------------------------------------
    # 🧩 بناء الشريط الكامل
    # ------------------------------------------------------------------
    def _build_toolbar(self, parent=None) -> QToolBar:
        bar = QToolBar(parent)
        self.toolbar = bar  # ✅ حفظ المرجع قبل إنشاء الأزرار
        bar.setMovable(False)
        bar.setFloatable(False)
        bar.setIconSize(QSize(28, 28))
        bar.setStyleSheet("""
            QToolBar {
                background-color: #F1F2F1;
                border: none;
                spacing: 6px;
                padding: 4px 8px;
            }
            QToolButton {
                background: transparent;
                border: none;
                margin: 2px;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #E6E6E6;
                border-radius: 6px;
            }
            QToolButton:checked {
                background-color: rgba(230, 126, 34, 0.2);
                border-radius: 6px;
            }
        """)

        # ----------------------------------------------------------
        # أدوات الرسم الأساسية
        # ----------------------------------------------------------
        draw_tools = [
            ("line", "Line", "line.png"),
            ("circle", "Circle", "circle.png"),
            ("rect", "Rectangle", "rect.png"),
            ("arc", "Arc", "arc.png"),
        ]

        # ----------------------------------------------------------
        # أدوات التعديل
        # ----------------------------------------------------------
        modify_tools = [
            ("trim", "Trim", "trim.png"),
            ("offset", "Offset", "offset.png"),
            ("mirror", "Mirror", "mirror.png"),
            ("fillet", "Fillet", "fillet.png"),
        ]

        # ----------------------------------------------------------
        # إضافة أدوات الرسم
        # ----------------------------------------------------------
        for name, tip, icon_file in draw_tools:
            act = self._create_action(name, tip, icon_file)
            bar.addAction(act)

        # فاصل رمادي أنيق
        sep = QWidget()
        sep.setFixedWidth(1)
        sep.setStyleSheet("background-color: #C8C9C8; margin: 0 10px;")
        bar.addWidget(sep)

        # ----------------------------------------------------------
        # إضافة أدوات التعديل
        # ----------------------------------------------------------
        for name, tip, icon_file in modify_tools:
            act = self._create_action(name, tip, icon_file)
            bar.addAction(act)

        return bar

    # ------------------------------------------------------------------
    # 🧱 إنشاء زر (Action) جديد
    # ------------------------------------------------------------------
    def _create_action(self, name: str, tooltip: str, icon_filename: str):
        """إنشاء زر أداة قياسي"""
        icon_path = Path("assets/icons") / icon_filename
        act = QAction(QIcon(str(icon_path)), tooltip, self.toolbar)
        act.setCheckable(True)
        act.triggered.connect(lambda checked, n=name: self._on_tool_selected(n))
        return act

    # ------------------------------------------------------------------
    # 🎯 عند اختيار أداة
    # ------------------------------------------------------------------
    def _on_tool_selected(self, tool_name: str):
        print(f"🟠 [Toolbar] Tool selected: {tool_name}")
        self.viewer.set_active_tool(tool_name)
