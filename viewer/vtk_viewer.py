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
        self.selected_actor = None  # 🟦 لتخزين الشكل المحدد العام

        print(f"🎯 [Viewer] Active tool: {self.current_tool}")
        # 🆕 تمرير الأداة إلى interactor
        if hasattr(self, "style"):
            self.style.current_tool = self.current_tool
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

    def load_dxf(self, file_path: str):
        """
        تحميل ملف DXF من المسار وعرضه في مشهد VTK بسرعة عالية.
        يحافظ على الشبكة والمحاور والكاميرا.
        الإسقاط عمودي على محور Y (الشكل على مستوى XZ)
        ونقطة الصفر هي الزاوية السفلية اليسرى.
        """
        import vtk
        from profile.dxf_normalizer import load_dxf_segments

        print(f"📂 [VTKViewer] تحميل DXF من: {file_path}")

        try:
            segs, bbox = load_dxf_segments(file_path)
            if not segs:
                print("⚠️ [VTKViewer] ملف DXF فارغ أو غير مدعوم.")
                return
        except Exception as e:
            print(f"❌ [VTKViewer] خطأ أثناء قراءة DXF: {e}")
            return

        try:
            # 🧹 تنظيف المجسمات السابقة فقط (دون حذف الشبكة والمحاور)
            actors = self.core.renderer.GetActors()
            actors.InitTraversal()
            to_remove = []
            actor = actors.GetNextActor()
            while actor:
                # لا نحذف الشبكة أو المحاور
                name = actor.GetClassName()
                if not ("Axes" in name or "Grid" in name):
                    to_remove.append(actor)
                actor = actors.GetNextActor()
            for a in to_remove:
                self.core.renderer.RemoveActor(a)

            # حساب إزاحة الشكل بحيث تكون الزاوية السفلية اليسرى عند (0,0,0)
            min_x, min_y = float("inf"), float("inf")
            for (p1, p2) in segs:
                min_x = min(min_x, p1[0], p2[0])
                min_y = min(min_y, p1[1], p2[1])

            offset_x = -min_x
            offset_y = -min_y

            # 🧩 إنشاء الشكل داخل PolyData واحدة (إسقاط على مستوى XZ)
            points = vtk.vtkPoints()
            lines = vtk.vtkCellArray()
            point_id = 0

            for (p1, p2) in segs:
                x1, z1 = float(p1[0]) + offset_x, float(p1[1]) + offset_y
                x2, z2 = float(p2[0]) + offset_x, float(p2[1]) + offset_y

                id1 = point_id
                id2 = point_id + 1
                points.InsertNextPoint(x1, 0.0, z1)  # Y=0 => على مستوى XZ
                points.InsertNextPoint(x2, 0.0, z2)

                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, id1)
                line.GetPointIds().SetId(1, id2)
                lines.InsertNextCell(line)

                point_id += 2

            polydata = vtk.vtkPolyData()
            polydata.SetPoints(points)
            polydata.SetLines(lines)

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(polydata)

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(0.25, 0.55, 0.95)
            actor.GetProperty().SetLineWidth(1.6)

            # ✅ عرض الشكل الجديد
            self.core.renderer.AddActor(actor)

            # 🧭 إعادة الكاميرا دون كسر التفاعل أو الشبكة
            self.core.renderer.ResetCameraClippingRange()
            self.update_view()

            print("🟢 [VTKViewer] تم عرض الملف بنجاح مع الحفاظ على الشبكة والمحاور.")

        except Exception as e:
            print(f"❌ [VTKViewer] فشل في عرض DXF: {e}")







