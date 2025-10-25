# -*- coding: utf-8 -*-
"""
vtk_viewer.py
------------------------------------------------------------
عارض Fusion-style بعد الفصل الهيكلي الكامل
يجمع بين:
- ViewerCore (المشهد والكاميرا والشبكة)
- SketchInteractorStyle (التفاعل بالماوس)
- ToolbarManager (شريط الأدوات الرمادي)
- SketchOps + ModifyOps (أوامر الرسم والتعديل)
- GridAxesManager (الشبكة والمحاور)
- DimInputManager (مربع إدخال القياسات)
------------------------------------------------------------
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

# 🧩 المكونات المفصولة
from viewer.viewer_core import ViewerCore
from viewer.interactor_style import SketchInteractorStyle
from viewer.toolbar_manager import ToolbarManager
from viewer.grid_axes_manager import GridAxesManager
from viewer.dim_input_manager import DimInputManager
from draw.sketch_ops import SketchOps
from draw.modify_ops import ModifyOps


class VTKViewer(QWidget):
    """العارض الرئيسي Fusion-style"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 🔹 التخطيط العام
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 🖥️ واجهة VTK
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        layout.addWidget(self.vtk_widget, 1)

        # 🧱 النواة (المشهد + الكاميرا)
        self.core = ViewerCore(self.vtk_widget.GetRenderWindow())
        self.renderer = self.core.renderer

        # 🧭 الشبكة والمحاور
        self.grid_axes = GridAxesManager(self.renderer)

        # ✏️ أدوات الرسم والتعديل
        self.sketch_ops = SketchOps(self)
        self.modify_ops = ModifyOps(self)

        # 📏 مربع الإدخال (قياسات)
        self.dim_input = DimInputManager(self)

        # 🧰 شريط الأدوات
        #self.toolbar_manager = ToolbarManager(self)
        #layout.addWidget(self.toolbar_manager.get_toolbar())

        # 🖱️ إعداد التفاعل (الماوس والكاميرا)
        self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
        self.style = SketchInteractorStyle(self.renderer, self)
        self.interactor.SetInteractorStyle(self.style)
        self.interactor.Initialize()

        # الأداة الحالية
        self.current_tool = "none"

        print("✅ [Fusion] VTKViewer initialized successfully.")

    # ------------------------------------------------------------------
    # 🎯 إدارة الأدوات
    # ------------------------------------------------------------------
    def set_active_tool(self, tool_name: str):
        """تحديد الأداة الحالية"""
        self.current_tool = tool_name or "none"
        print(f"🎯 [Viewer] Active tool: {self.current_tool}")

    # ------------------------------------------------------------------
    # 🔄 إعادة الرسم
    # ------------------------------------------------------------------
    def update_view(self):
        """تحديث المشهد"""
        if self.vtk_widget:
            self.vtk_widget.GetRenderWindow().Render()

    # ------------------------------------------------------------------
    # 🧼 تنظيف الأشكال من المشهد
    # ------------------------------------------------------------------
    def clear_scene(self):
        """إزالة جميع الأشكال من العارض"""
        actors = self.renderer.GetActors()
        actors.InitTraversal()
        to_remove = []
        a = actors.GetNextActor()
        while a:
            to_remove.append(a)
            a = actors.GetNextActor()
        for actor in to_remove:
            self.renderer.RemoveActor(actor)
        self.update_view()
        print("🧹 Scene cleared")
