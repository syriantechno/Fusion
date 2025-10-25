# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QVBoxLayout
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk


class SketchInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    """ستايل تفاعلي للرسم (يتبع الأداة المختارة من VTKViewer)"""
    def __init__(self, renderer, viewer_ref):
        super().__init__()
        self.renderer = renderer
        self.viewer_ref = viewer_ref
        self.points = []
        self.temp_actor = None

        # أحداث الماوس
        self.AddObserver("LeftButtonPressEvent", self.left_click)
        self.AddObserver("RightButtonPressEvent", self.right_click)
        self.AddObserver("MouseMoveEvent", self.mouse_move)

    def left_click(self, obj, event):
        tool = getattr(self.viewer_ref, "current_tool", None)
        if not tool or tool == "none":
            print("⚠️ لا توجد أداة نشطة — تجاهل النقر")
            return

        click_pos = self.GetInteractor().GetEventPosition()
        picker = vtk.vtkCellPicker()
        picker.Pick(click_pos[0], click_pos[1], 0, self.renderer)
        world_pos = picker.GetPickPosition()
        print(f"🟢 Left click ({tool}) at: {world_pos}")

        # حسب نوع الأداة
        if tool == "line":
            self.points.append(world_pos)
            if len(self.points) == 2:
                self._add_line(self.points[0], self.points[1])
                self.points = []
        elif tool == "circle":
            self._add_circle(world_pos)
        elif tool == "rect":
            self._add_rectangle(world_pos)
        elif tool == "arc":
            self._add_arc(world_pos)

    def right_click(self, obj, event):
        print("🔴 Right click → reset points")
        self.points = []
        if self.temp_actor:
            self.renderer.RemoveActor(self.temp_actor)
            self.temp_actor = None
            self.renderer.GetRenderWindow().Render()

    def mouse_move(self, obj, event):
        """معاينة مؤقتة أثناء الرسم"""
        tool = getattr(self.viewer_ref, "current_tool", None)
        if tool != "line" or len(self.points) != 1:
            return

        interactor = self.GetInteractor()
        pos = interactor.GetEventPosition()
        picker = vtk.vtkCellPicker()
        picker.Pick(pos[0], pos[1], 0, self.renderer)
        world_pos = picker.GetPickPosition()
        p1 = self.points[0]
        p2 = world_pos

        # خط مؤقت
        line_source = vtk.vtkLineSource()
        line_source.SetPoint1(p1)
        line_source.SetPoint2(p2)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(line_source.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.9, 0.3, 0.1)
        actor.GetProperty().SetLineWidth(2)

        if self.temp_actor:
            self.renderer.RemoveActor(self.temp_actor)
        self.temp_actor = actor
        self.renderer.AddActor(actor)
        self.renderer.GetRenderWindow().Render()

    def _add_line(self, p1, p2):
        line_source = vtk.vtkLineSource()
        line_source.SetPoint1(p1)
        line_source.SetPoint2(p2)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(line_source.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.2, 0.3, 0.6)
        actor.GetProperty().SetLineWidth(3)
        self.renderer.AddActor(actor)
        self.renderer.GetRenderWindow().Render()
        print("✅ خط تمت إضافته")

    def _add_circle(self, center):
        """Placeholder: دائرة بسيطة"""
        print("⭕ دائرة مبدئية عند:", center)

    def _add_rectangle(self, center):
        """Placeholder: مستطيل"""
        print("⬛ مستطيل مبدئي عند:", center)

    def _add_arc(self, center):
        """Placeholder: قوس"""
        print("〰️ قوس مبدئي عند:", center)


class VTKViewer(QWidget):
    """عارض VTK مع دعم تفعيل الأدوات فقط عند الاختيار"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # إعداد واجهة VTK
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        layout.addWidget(self.vtk_widget)

        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.97, 0.975, 0.97)     # أسفل
        self.renderer.SetBackground2(0.75, 0.75, 0.75)     # أعلى
        self.renderer.GradientBackgroundOn()

        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)

        # 🔹 الأداة النشطة (None بالبداية)
        self.current_tool = "none"

        # 🔹 الشبكة الأرضية
        plane_source = vtk.vtkPlaneSource()
        plane_source.SetOrigin(-100, -100, 0)
        plane_source.SetPoint1(100, -100, 0)
        plane_source.SetPoint2(-100, 100, 0)
        plane_source.SetXResolution(20)
        plane_source.SetYResolution(20)
        plane_mapper = vtk.vtkPolyDataMapper()
        plane_mapper.SetInputConnection(plane_source.GetOutputPort())
        plane_actor = vtk.vtkActor()
        plane_actor.SetMapper(plane_mapper)
        plane_actor.GetProperty().SetColor(0.8, 0.8, 0.8)
        plane_actor.GetProperty().SetRepresentationToWireframe()
        plane_actor.PickableOn()
        self.renderer.AddActor(plane_actor)

        # 🔹 الكاميرا
        cam = self.renderer.GetActiveCamera()
        cam.SetPosition(200, 200, 150)
        cam.SetFocalPoint(0, 0, 0)
        cam.SetViewUp(0, 0, 1)
        self.renderer.ResetCamera()
        self.renderer.ResetCameraClippingRange()

        # 🔹 التفاعل
        self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
        self.style = SketchInteractorStyle(self.renderer, self)
        self.interactor.SetInteractorStyle(self.style)

        # 🔹 المؤشر الثلاثي
        axes = vtk.vtkAxesActor()
        widget = vtk.vtkOrientationMarkerWidget()
        widget.SetOrientationMarker(axes)
        widget.SetInteractor(self.interactor)
        widget.EnabledOn()
        widget.InteractiveOff()

        # تشغيل أولي
        self.vtk_widget.GetRenderWindow().Render()
        self.interactor.Initialize()
        print("✅ VTKViewer جاهز — لا يرسم حتى اختيار أداة")

    # 🔹 دالة استقبال الأداة من SketchToolsPanel
    def set_active_tool(self, tool_name: str):
        self.current_tool = tool_name or "none"
        print(f"🎯 تم تعيين الأداة الحالية إلى: {self.current_tool}")
