# -*- coding: utf-8 -*-
"""
interactor_style.py — interactive drawing + dimension input
"""

import math
import vtk


class SketchInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, renderer, viewer_ref):
        super().__init__()
        self.renderer = renderer
        self.viewer_ref = viewer_ref
        self.points = []
        self.preview_actor = None
        self.preview_source = None
        self.preview_kind = None
        self.current_tool = None
        self.Z = 0.01
        self.picker = vtk.vtkCellPicker()
        self.picker.SetTolerance(0.001)
        self.dim_input = getattr(viewer_ref, "dim_input", None)


        self.AddObserver("LeftButtonPressEvent", self.on_left_click)
        self.AddObserver("MouseMoveEvent", self.on_mouse_move)
        self.AddObserver("KeyPressEvent", self.on_key_press)

    # -------------------------------
    # Helpers
    # -------------------------------
    def _pick_point(self, x, y):
        self.picker.Pick(x, y, 0, self.renderer)
        pos = self.picker.GetPickPosition()
        return (pos[0], pos[1], self.Z)

    def _clear_preview(self):
        if self.preview_actor:
            self.renderer.RemoveActor(self.preview_actor)
        self.preview_actor = None
        self.preview_source = None
        self.preview_kind = None
        self.viewer_ref.update_view()

    # -------------------------------
    # Events
    # -------------------------------
    def on_left_click(self, obj, evt):
        inter = self.GetInteractor()
        x, y = inter.GetEventPosition()
        world = self._pick_point(x, y)
        tool = getattr(self.viewer_ref, "current_tool", "none")
        self.current_tool = tool

        # الأدوات الأساسية (خط - دائرة - مستطيل)
        if tool in ("line", "circle", "rect"):
            self.points.append(world)

            # أول نقرة → ابدأ المعاينة
            if len(self.points) == 1:
                self._start_preview(tool, world)

            # ثاني نقرة → أنهي الشكل
            elif len(self.points) == 2:
                p1, p2 = self.points
                self._finalize_shape(tool, p1, p2)
                self.points.clear()
                self._clear_preview()

        # ✅ أداة القوس (Arc 3pt)
        elif tool == "arc":
            self.points.append(world)

            if len(self.points) == 1:
                # أول نقطة → بداية القوس
                print("[ARC] First point set")

            elif len(self.points) == 2:
                # ثاني نقطة → نقطة وسط القوس → إنشاء معاينة فورية
                print("[ARC] Second point set — starting preview")
                p1, p2 = self.points

                # إنشاء مصدر قوس مبدئي
                arc_src = vtk.vtkArcSource()
                arc_src.SetPoint1(*p1)
                arc_src.SetPoint2(*p2)
                arc_src.SetCenter((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2, self.Z)
                arc_src.SetResolution(64)

                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(arc_src.GetOutputPort())
                actor = vtk.vtkActor()
                actor.SetMapper(mapper)
                actor.GetProperty().SetColor(0.3, 0.3, 0.3)
                actor.GetProperty().SetLineWidth(2)

                self.renderer.AddActor(actor)
                self.preview_source = arc_src
                self.preview_actor = actor
                self.preview_kind = "arc"
                self.viewer_ref.update_view()

            elif len(self.points) == 3:
                # ثالث نقطة → إنهاء القوس
                p1, p2, p3 = self.points
                print(f"[ARC] Finalizing arc: {p1}, {p2}, {p3}")
                try:
                    self.viewer_ref.sketch_ops.arc_3pt(p1, p2, p3)
                except Exception as e:
                    print(f"[⚠️ Arc] خطأ أثناء إنشاء القوس: {e}")
                self.points.clear()
                self._clear_preview()

        self.OnLeftButtonDown()

    def on_mouse_move(self, obj, evt):
        if len(self.points) != 1 or not self.preview_source:
            return
        inter = self.GetInteractor()
        x, y = inter.GetEventPosition()
        p2 = self._pick_point(x, y)

        if self.preview_kind == "line":
            self.preview_source.SetPoint2(*p2)
        elif self.preview_kind == "circle":
            c = self.points[0]
            r = math.hypot(p2[0] - c[0], p2[1] - c[1])
            self.preview_source.SetRadius(r)
        elif self.preview_kind == "rect":
            self._update_preview_rect(p2)
        self.preview_source.Modified()
        self.viewer_ref.update_view()
        self.OnMouseMove()

    def on_key_press(self, obj, evt):
        inter = self.GetInteractor()
        key = inter.GetKeySym()
        if key in "0123456789.-":
            if self.dim_input:
                pos = inter.GetEventPosition()
                tool = getattr(self.viewer_ref, "current_tool", "")
                # 🔧 نمرر اسم الأداة الحالية حتى يعرف الإدخال لأي شكل يرجع
                self.dim_input.show(pos, tool, lambda val, t=tool: self._on_dim_entered(val, t))
                self.dim_input.input.setText(key)

        elif key in ("Escape", "esc"):
            if self.dim_input:
                self.dim_input.hide()

        self.OnKeyPress()

    # -------------------------------
    # Preview creation
    # -------------------------------
    def _start_preview(self, tool, p1):
        if tool == "line":
            src = vtk.vtkLineSource()
            src.SetPoint1(*p1)
            src.SetPoint2(*p1)
        elif tool == "circle":
            src = vtk.vtkRegularPolygonSource()
            src.SetCenter(*p1)
            src.SetRadius(0)
            src.SetNumberOfSides(64)
        elif tool == "rect":
            src = vtk.vtkLineSource()
            src.SetPoint1(*p1)
            src.SetPoint2(*p1)
        else:
            return

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(src.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.4, 0.4, 0.4)
        actor.GetProperty().SetLineWidth(2)
        self.renderer.AddActor(actor)

        self.preview_actor = actor
        self.preview_source = src
        self.preview_kind = tool
        self.viewer_ref.update_view()

    def _update_preview_rect(self, p2):
        p1 = self.points[0]
        points = vtk.vtkPoints()
        polys = vtk.vtkCellArray()
        pts = [
            (p1[0], p1[1], self.Z),
            (p2[0], p1[1], self.Z),
            (p2[0], p2[1], self.Z),
            (p1[0], p2[1], self.Z),
        ]
        for pt in pts:
            points.InsertNextPoint(*pt)
        polys.InsertNextCell(5)
        for i in range(4):
            polys.InsertCellPoint(i)
        polys.InsertCellPoint(0)

        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetLines(polys)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)
        self.preview_actor.SetMapper(mapper)

    # -------------------------------
    # Finalize
    # -------------------------------
    def _finalize_shape(self, tool, p1, p2):
        if tool == "line":
            self.viewer_ref.sketch_ops.line(p1, p2)
        elif tool == "circle":
            r = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            self.viewer_ref.sketch_ops.circle(p1, r)
        elif tool == "rect":
            w, h = p2[0] - p1[0], p2[1] - p1[1]
            self.viewer_ref.sketch_ops.rectangle(p1, w, h)
        self.viewer_ref.update_view()

    def _on_dim_entered(self, text=None, tool=None, *args, **kwargs):
        if not text:
            if self.dim_input:
                text = self.dim_input.input.text().strip()
            else:
                return
        if not text or not self.points:
            return

        # 🔹 تحليل الإدخال: دعم 50*30 أو 50x30
        text = text.lower().replace('x', '*')
        parts = text.split('*')
        values = []
        for p in parts:
            try:
                values.append(float(p))
            except Exception:
                pass
        if not values:
            return

        p1 = self.points[0]
        cur = self._pick_point(*self.GetInteractor().GetEventPosition())
        vx, vy = cur[0] - p1[0], cur[1] - p1[1]
        mag = math.hypot(vx, vy) or 1.0
        ux, uy = vx / mag, vy / mag

        # 🔹 حسب نوع الأداة
        if self.current_tool == "circle":
            r = values[0]
            self.viewer_ref.sketch_ops.circle(p1, r)

        elif self.current_tool == "rect":
            if len(values) == 1:
                w, h = values[0], values[0]
            else:
                w, h = values[0], values[1]
            self.viewer_ref.sketch_ops.rectangle(p1, w, h)

        elif self.current_tool == "line":
            val = values[0]
            p2 = (p1[0] + ux * val, p1[1] + uy * val, self.Z)
            self.viewer_ref.sketch_ops.line(p1, p2)

        # تنظيف المعاينة والإدخال
        self.points.clear()
        self._clear_preview()
        if self.dim_input:
            self.dim_input.hide()


