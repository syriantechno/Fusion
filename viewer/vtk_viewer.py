# -*- coding: utf-8 -*-
"""
VTKViewer — نسخة مُحدّثة
تحلّ مشكلات الكاميرا والشبكة في أوضاع الرسم والتحديد.
تدعم عرض ملفات DXF بالإسقاط العمودي على محور Y (على مستوى XZ)
وتحافظ على الشبكة والمحاور.
"""

import vtk
from PySide6.QtWidgets import QWidget, QVBoxLayout
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera

from viewer.viewer_core import ViewerCore
from viewer.grid_axes_manager import GridAxesManager
from draw.sketch_ops import SketchOps
from draw.modify_ops import ModifyOps
from viewer.dim_input_manager import DimInputManager
from viewer.interactor_style import SketchInteractorStyle


class VTKViewer(QWidget):
    """العارض الرئيسي Fusion-style"""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 🖥️ واجهة VTK
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        layout.addWidget(self.vtk_widget, 1)

        # 🧱 النواة والمشهد
        self.core = ViewerCore(self.vtk_widget.GetRenderWindow())
        self.renderer = self.core.renderer

        # 🧭 الشبكة والمحاور
        self.grid_axes = GridAxesManager(self.renderer)

        # ✏️ أدوات الرسم والتعديل
        self.sketch_ops = SketchOps(self)
        self.modify_ops = ModifyOps(self)

        # 📏 إدخال القياسات
        self.dim_input = DimInputManager(self)

        # 🖱️ إعداد التفاعل
        self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
        self.style = SketchInteractorStyle(self.renderer, self)
        self.interactor.SetInteractorStyle(self.style)
        self.interactor.Initialize()

        # ✅ تأكيد تشغيل التفاعل
        self.interactor.Enable()
        self.vtk_widget.GetRenderWindow().Render()

        # ✅ تتبع العناصر (actors) الخاصة بالأشكال فقط
        self._shape_actors = []

        # ✅ إعداد مفتاح Space لتحريك الكاميرا مؤقتًا
        self._trackball = vtkInteractorStyleTrackballCamera()
        self._install_camera_toggle_hotkey()

        # ✅ تأكيد ظهور الشبكة
        if hasattr(self, "grid_axes"):
            try:
                self.grid_axes.show_grid(True)
                self.grid_axes.update()
            except Exception:
                pass

        print("✅ [Fusion] VTKViewer initialized successfully.")

    # ------------------------------------------------------------------
    def _install_camera_toggle_hotkey(self):
        """اضغط وامسك Space لتفعيل تحريك الكاميرا مؤقتًا، وحرّرها للعودة للوضع العادي."""
        iren = self.vtk_widget.GetRenderWindow().GetInteractor()

        def on_key_press(obj, evt):
            if obj.GetKeySym() == "space":
                iren.SetInteractorStyle(self._trackball)
                iren.Render()

        def on_key_release(obj, evt):
            if obj.GetKeySym() == "space":
                iren.SetInteractorStyle(self.style)
                iren.Render()

        iren.AddObserver("KeyPressEvent", on_key_press)
        iren.AddObserver("KeyReleaseEvent", on_key_release)
    # ------------------------------------------------------------------
    # 🎯 إدارة الأداة الحالية
    # ------------------------------------------------------------------
    def set_active_tool(self, tool_name: str):
        """تحديد الأداة الحالية وتمريرها إلى الـInteractor."""
        self.current_tool = tool_name or "none"
        print(f"🎯 [Viewer] Active tool: {self.current_tool}")

        # تمرير الأداة إلى نمط التفاعل (Interactor Style)
        if hasattr(self, "style") and self.style:
            self.style.current_tool = self.current_tool


    # ------------------------------------------------------------------
    def update_view(self):
        if self.vtk_widget:
            self.vtk_widget.GetRenderWindow().Render()

    # ------------------------------------------------------------------
    def clear_scene(self):
        actors = self.renderer.GetActors()
        actors.InitTraversal()
        to_remove = []
        actor = actors.GetNextActor()
        while actor:
            to_remove.append(actor)
            actor = actors.GetNextActor()
        for a in to_remove:
            self.renderer.RemoveActor(a)
        self.update_view()
        print("🧹 Scene cleared")

    # ------------------------------------------------------------------
    def load_dxf(self, file_path: str):
        """تحميل ملف DXF وإظهاره في المشهد بإسقاط عمودي على Y."""
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
        self.last_segments = segs

        try:
            # 🧹 حذف الأشكال القديمة فقط
            for a in getattr(self, "_shape_actors", []):
                try:
                    self.core.renderer.RemoveActor(a)
                except Exception:
                    pass
            self._shape_actors = []

            # 📏 الإزاحة لتكون الزاوية السفلية اليسرى هي الأصل
            min_x, min_y = float("inf"), float("inf")
            for (p1, p2) in segs:
                min_x = min(min_x, p1[0], p2[0])
                min_y = min(min_y, p1[1], p2[1])
            offset_x, offset_y = -min_x, -min_y

            # 🧩 بناء PolyData موحدة (على مستوى XZ)
            points = vtk.vtkPoints()
            lines = vtk.vtkCellArray()
            pid = 0

            for (p1, p2) in segs:
                x1, z1 = float(p1[0]) + offset_x, float(p1[1]) + offset_y
                x2, z2 = float(p2[0]) + offset_x, float(p2[1]) + offset_y

                id1, id2 = pid, pid + 1
                points.InsertNextPoint(x1, 0.0, z1)
                points.InsertNextPoint(x2, 0.0, z2)

                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, id1)
                line.GetPointIds().SetId(1, id2)
                lines.InsertNextCell(line)

                pid += 2

            polydata = vtk.vtkPolyData()
            polydata.SetPoints(points)
            polydata.SetLines(lines)

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(polydata)

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(0.25, 0.55, 0.95)
            actor.GetProperty().SetLineWidth(1.6)

            self.core.renderer.AddActor(actor)
            self._shape_actors.append(actor)

            # 🧭 تحديث الشبكة بعد التحميل
            if hasattr(self, "grid_axes"):
                try:
                    self.grid_axes.show_grid(True)
                    self.grid_axes.update()
                except Exception:
                    pass

            # تحديث العرض بدون كسر الكاميرا
            self.core.renderer.ResetCameraClippingRange()
            self.update_view()

            print("🟢 [VTKViewer] تم عرض الملف بنجاح مع الحفاظ على الشبكة والمحاور.")

        except Exception as e:
            print(f"❌ [VTKViewer] فشل في عرض DXF: {e}")


from tools.geometry_ops import extrude_profile

def extrude_current_shape(self, depth: float = 40.0, axis: str = "Y"):
    """ينفذ الإكسترود عبر geometry_ops"""
    if not hasattr(self, "last_profile_path"):
        print("⚠️ [VTKViewer] لا يوجد مسار ملف DXF.")
        return
    prism = extrude_profile(self.last_profile_path, depth, axis)
    if prism:
        self.clear_scene()
        self.core.display_shape(prism)
        print("🟢 [VTKViewer] تم عرض الإكسترود بنجاح.")
    else:
        print("⚠️ [VTKViewer] لم يُنشأ أي شكل.")



