# -*- coding: utf-8 -*-
"""
viewer_core.py
------------------------------------------------------------
أساس العارض (VTK Viewer Core)
يتكفل بإعداد:
- الـ Renderer
- الكاميرا الافتراضية
- الشبكة Grid
- المحاور Axes
- trihedron (المحاور الصغيرة في الزاوية)
------------------------------------------------------------
"""

import vtk


class ViewerCore:
    """نواة العرض في Fusion Viewer"""

    def __init__(self, render_window):
        # إنشاء Renderer وربطه مع نافذة العرض
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.97, 0.975, 0.97)
        self.renderer.SetBackground2(0.78, 0.78, 0.78)
        self.renderer.GradientBackgroundOn()
        render_window.AddRenderer(self.renderer)

        # تهيئة الكاميرا
        self._setup_camera()

        # إضافة الشبكة والمحاور
        #self._add_grid()
        #self._add_axes()
        #self._add_trihedron()

        print("✅ ViewerCore initialized (renderer + grid + axes ready)")

    # ------------------------------------------------------------
    # 📷 إعداد الكاميرا
    # ------------------------------------------------------------
    def _setup_camera(self):
        self.camera = self.renderer.GetActiveCamera()
        self.camera.SetPosition(200, 200, 150)
        self.camera.SetFocalPoint(0, 0, 0)
        self.camera.SetViewUp(0, 0, 1)
        self.renderer.ResetCamera()

    # ------------------------------------------------------------
    # 🧱 شبكة أرضية
    # ------------------------------------------------------------
    def _add_grid(self, size=200, spacing=10, color=(0.85, 0.85, 0.85)):
        """إنشاء شبكة بسيطة على المحور XY"""
        append = vtk.vtkAppendPolyData()

        for i in range(-size, size + spacing, spacing):
            # خطوط X
            line_x = vtk.vtkLineSource()
            line_x.SetPoint1(-size, i, 0)
            line_x.SetPoint2(size, i, 0)
            line_x.Update()
            append.AddInputData(line_x.GetOutput())

            # خطوط Y
            line_y = vtk.vtkLineSource()
            line_y.SetPoint1(i, -size, 0)
            line_y.SetPoint2(i, size, 0)
            line_y.Update()
            append.AddInputData(line_y.GetOutput())

        append.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(append.GetOutput())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)
        actor.GetProperty().LightingOff()
        self.renderer.AddActor(actor)

    # ------------------------------------------------------------
    # 🧭 المحاور الأساسية
    # ------------------------------------------------------------
    def _add_axes(self):
        """إضافة محاور رئيسية X/Y/Z"""
        axes = vtk.vtkAxesActor()
        axes.SetTotalLength(50, 50, 50)
        axes.AxisLabelsOn()
        axes.SetCylinderRadius(0.02)
        self.renderer.AddActor(axes)

    # ------------------------------------------------------------
    # 🧩 trihedron صغير في الزاوية
    # ------------------------------------------------------------
    def _add_trihedron(self):
        """إضافة trihedron صغير في الزاوية اليسرى السفلى"""
        orientation_marker = vtk.vtkAxesActor()
        orientation_marker.SetTotalLength(20, 20, 20)
        orientation_marker.AxisLabelsOff()

        marker_widget = vtk.vtkOrientationMarkerWidget()
        marker_widget.SetOrientationMarker(orientation_marker)
        marker_widget.SetViewport(0.0, 0.0, 0.2, 0.2)
        marker_widget.SetInteractor(self.renderer.GetRenderWindow().GetInteractor())
        marker_widget.SetEnabled(True)
        marker_widget.InteractiveOff()
