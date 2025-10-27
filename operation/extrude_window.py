# -*- coding: utf-8 -*-
"""
🧱 ExtrudeWindow (Fusion-style)
------------------------------
نافذة تنفيذ الإكسترود على أي بروفايل DXF محمّل.
تعتمد فقط على tools/geometry_ops.py للمنطق الهندسي.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton
)
from PySide6.QtCore import Qt

from frontend.base.base_tool_window import BaseToolWindow
from tools.geometry_ops import extrude_from_dxf


class ExtrudeWindow(BaseToolWindow):
    def __init__(self, parent=None, profile_path: str | None = None):
        super().__init__("Extrude", parent)
        self.setFixedSize(400, 260)
        self.profile_path = profile_path  # المسار القادم من Profile Manager
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        """تصميم الواجهة الأساسية"""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # الإدخال 1: العمق
        row_depth = QHBoxLayout()
        row_depth.addWidget(QLabel("Depth (mm):"))
        self.depth_input = QLineEdit("40.0")
        self.depth_input.setAlignment(Qt.AlignCenter)
        row_depth.addWidget(self.depth_input)
        layout.addLayout(row_depth)

        # الإدخال 2: المحور
        row_axis = QHBoxLayout()
        row_axis.addWidget(QLabel("Axis:"))
        self.axis_selector = QComboBox()
        self.axis_selector.addItems(["X", "Y", "Z"])
        self.axis_selector.setCurrentText("Y")
        row_axis.addWidget(self.axis_selector)
        layout.addLayout(row_axis)

        # الأزرار
        row_btns = QHBoxLayout()
        self.preview_btn = QPushButton("Preview")
        self.apply_btn = QPushButton("Apply")
        self.cancel_btn = QPushButton("Cancel")
        row_btns.addWidget(self.preview_btn)
        row_btns.addWidget(self.apply_btn)
        row_btns.addWidget(self.cancel_btn)
        layout.addLayout(row_btns)

        # حاوية
        box = QWidget()
        box.setLayout(layout)
        self.set_content_widget(box)

        # الأحداث
        self.preview_btn.clicked.connect(lambda: self._on_apply(preview=True))
        self.apply_btn.clicked.connect(lambda: self._on_apply(preview=False))
        self.cancel_btn.clicked.connect(self.close)

    # ------------------------------------------------------------------
    def _find_viewer(self):
        """تحديد العارض الرئيسي (vtk_viewer) عبر MainWindow"""
        mw = self.parent()
        while mw and not hasattr(mw, "workspace_page"):
            mw = mw.parent()
        if mw and hasattr(mw.workspace_page, "vtk_viewer"):
            print("🟢 [ExtrudeWindow] تم العثور على العارض عبر: main_window.workspace_page.vtk_viewer")
            return mw.workspace_page.vtk_viewer
        print("⚠️ [ExtrudeWindow] لم يتم العثور على أي عارض متاح.")
        return None

    # ------------------------------------------------------------------
    def _get_profile_path(self):
        """تحديد المسار الحالي لملف البروفايل"""
        if self.profile_path:
            return self.profile_path

        # في حال لم يمرّر المسار عند الفتح، نحاول إيجاده من MainWindow
        mw = self.parent()
        if hasattr(mw, "last_profile_path"):
            return mw.last_profile_path

        print("⚠️ [ExtrudeWindow] لا يوجد مسار ملف DXF محدد.")
        return None

    # ------------------------------------------------------------------
    def _on_apply(self, preview=False):
        """تنفيذ الإكسترود"""
        viewer = self._find_viewer()
        if not viewer:
            return

        dxf_path = self._get_profile_path()
        if not dxf_path:
            return

        try:
            depth = float(self.depth_input.text())
        except ValueError:
            print("⚠️ [ExtrudeWindow] عمق غير صالح.")
            return

        axis = self.axis_selector.currentText().upper()
        print(f"🟢 [ExtrudeWindow] بدء الإكسترود على المحور {axis} بعمق {depth}mm ...")

        try:
            solid = extrude_from_dxf(dxf_path, depth, axis)
            if solid and not solid.IsNull():
                if hasattr(viewer, "clear_scene"):
                    viewer.clear_scene()
                if hasattr(viewer, "display_shape"):
                    viewer.display_shape(solid)
                else:
                    viewer.core.display_shape(solid)
                print("🟢 [ExtrudeWindow] تم عرض الشكل بعد الإكسترود بنجاح.")
            else:
                print("⚠️ [ExtrudeWindow] لم يُنشأ شكل صالح للإكسترود.")

        except Exception as e:
            print(f"❌ [ExtrudeWindow] خطأ أثناء الإكسترود: {e}")

        if not preview:
            self.close()
