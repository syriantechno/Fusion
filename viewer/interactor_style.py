# -*- coding: utf-8 -*-
"""
interactor_style.py — الرسم السريع + الإدخال اليدوي + قائمة يمين (تحريك / نسخ / لصق / حذف)
"""

import math
import vtk
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import QPoint


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

        # 🧩 قائمة الزر اليمين البسيطة
        self.menu = QMenu(viewer_ref)
        self.selected_actor = None
        self.dragging = False
        self.drag_start = None
        self.actor_start_pos = None
        self._clipboard = None

        for name, func in [
            ("↔️ Move", self._menu_move),
            ("📄 Copy", self._menu_copy),
            ("📋 Paste", self._menu_paste),
            ("🗑️ Delete", self._menu_delete),
        ]:
            act = QAction(name, self.menu)
            act.triggered.connect(func)
            self.menu.addAction(act)

        # الأحداث الأساسية
        self.AddObserver("LeftButtonPressEvent", self.on_left_click)
        self.AddObserver("MouseMoveEvent", self.on_mouse_move)
        self.AddObserver("RightButtonPressEvent", self.on_right_click)
        self.AddObserver("KeyPressEvent", self.on_key_press)

    # ----------------------------------------------------------------------
    # أدوات اختيار وتحريك
    # ----------------------------------------------------------------------
    def _pick_point(self, x, y):
        self.picker.Pick(x, y, 0, self.renderer)
        pos = self.picker.GetPickPosition()
        return (pos[0], pos[1], self.Z)

    def _pick_actor(self, x, y):
        prop_picker = vtk.vtkPropPicker()
        prop_picker.Pick(x, y, 0, self.renderer)
        return prop_picker.GetActor()

    # ----------------------------------------------------------------------
    def _clear_preview(self):
        if self.preview_actor:
            self.renderer.RemoveActor(self.preview_actor)
        self.preview_actor = None
        self.preview_source = None
        self.preview_kind = None
        self.viewer_ref.update_view()

    # ----------------------------------------------------------------------
    # قائمة يمين
    # ----------------------------------------------------------------------
    def on_right_click(self, obj, evt):
        inter = self.GetInteractor()
        x, y = inter.GetEventPosition()
        self.selected_actor = self._pick_actor(x, y)
        qt_pos = self.viewer_ref.mapToGlobal(QPoint(x, y))
        self.menu.popup(qt_pos)

    def _menu_move(self):
        if not self.selected_actor:
            print("⚠️ لا يوجد عنصر محدد للتحريك.")
            return
        self.current_tool = "move"
        self.dragging = False
        print("↔️ Move mode — انقر واسحب للتحريك")

    def _menu_copy(self):
        if self.selected_actor and self.selected_actor.GetMapper():
            poly = vtk.vtkPolyData()
            poly.DeepCopy(self.selected_actor.GetMapper().GetInput())
            self._clipboard = poly
            print("📄 Copied object.")
        else:
            print("⚠️ Nothing to copy.")

    def _menu_paste(self):
        if not self._clipboard:
            print("⚠️ Clipboard empty.")
            return
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(self._clipboard)
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.3, 0.3, 0.3)
        self.renderer.AddActor(actor)
        self.viewer_ref.update_view()
        self.selected_actor = actor
        self.current_tool = "move"
        print("📋 Pasted — ready to move.")

    def _menu_delete(self):
        if self.selected_actor:
            self.renderer.RemoveActor(self.selected_actor)
            self.selected_actor = None
            self.viewer_ref.update_view()
            print("🗑️ Deleted.")
        else:
            print("⚠️ Nothing to delete.")

    # ----------------------------------------------------------------------
    # أحداث الماوس
    # ----------------------------------------------------------------------
    def on_left_click(self, obj, evt):
        inter = self.GetInteractor()
        x, y = inter.GetEventPosition()
        world = self._pick_point(x, y)
        tool = getattr(self.viewer_ref, "current_tool", "none")
        self.current_tool = tool
        # 🟦 وضع التحديد (Select Mode)
        if tool == "select":
            actor = self._pick_actor(x, y)
            if actor:
                # إزالة تمييز سابق
                if self.selected_actor and self.selected_actor != actor:
                    self.selected_actor.GetProperty().SetColor(0.3, 0.3, 0.3)

                self.selected_actor = actor
                actor.GetProperty().SetColor(0.1, 0.6, 1.0)  # أزرق مميز
                print("🔵 [Select] عنصر محدد.")
            else:
                print("⚪ [Select] لا يوجد عنصر محدد.")
            self.viewer_ref.update_view()
            return


        # 🟦 وضع التحريك
        if tool == "move" and self.selected_actor:
            if not self.dragging:
                self.dragging = True
                self.drag_start = world
                pos = self.selected_actor.GetPosition()
                self.actor_start_pos = (pos[0], pos[1], pos[2])
                print("🚚 Move start")
            else:
                self.dragging = False
                self.current_tool = None
                print("✅ Move applied")
            return

        # أدوات الرسم العادية (من الكود الأصلي)
        if tool in ("line", "circle", "rect"):
            self.points.append(world)
            if len(self.points) == 1:
                self._start_preview(tool, world)
            elif len(self.points) == 2:
                p1, p2 = self.points
                self._finalize_shape(tool, p1, p2)
                self.points.clear()
                self._clear_preview()

        elif tool == "arc":
            self.points.append(world)
            if len(self.points) == 1:
                print("[ARC] First point set")
            elif len(self.points) == 2:
                print("[ARC] Second point set — starting preview")
                p1, p2 = self.points
                arc_src = vtk.vtkArcSource()
                arc_src.SetPoint1(*p1)
                arc_src.SetPoint2(*p2)
                arc_src.SetCenter((p1[0]+p2[0])/2, (p1[1]+p2[1])/2, self.Z)
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
                p1, p2, p3 = self.points
                try:
                    self.viewer_ref.sketch_ops.arc_3pt(p1, p2, p3)
                except Exception as e:
                    print(f"[⚠️ Arc] {e}")
                self.points.clear()
                self._clear_preview()

        self.OnLeftButtonDown()

    def on_mouse_move(self, obj, evt):
        inter = self.GetInteractor()
        x, y = inter.GetEventPosition()
        p2 = self._pick_point(x, y)

        # تحريك مباشر في وضع Move
        if self.current_tool == "move" and self.dragging and self.selected_actor:
            dx = p2[0] - self.drag_start[0]
            dy = p2[1] - self.drag_start[1]
            pos = self.actor_start_pos
            self.selected_actor.SetPosition(pos[0] + dx, pos[1] + dy, pos[2])
            self.viewer_ref.update_view()
            return

        # معاينات الرسم كما هي
        if len(self.points) != 1 or not self.preview_source:
            return
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
                self.dim_input.show(pos, tool, lambda val, t=tool: self._on_dim_entered(val, t))
                self.dim_input.input.setText(key)
        elif key in ("Escape", "esc"):
            if self.dim_input:
                self.dim_input.hide()
        self.OnKeyPress()

    # ----------------------------------------------------------------------
    # معاينات وإنهاء الأشكال (بدون تغيير)
    # ----------------------------------------------------------------------
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
        vx, vy = cur[0]-p1[0], cur[1]-p1[1]
        mag = math.hypot(vx, vy) or 1.0
        ux, uy = vx/mag, vy/mag
        if self.current_tool == "circle":
            self.viewer_ref.sketch_ops.circle(p1, values[0])
        elif self.current_tool == "rect":
            w, h = (values+[values[0]])[:2]
            self.viewer_ref.sketch_ops.rectangle(p1, w, h)
        elif self.current_tool == "line":
            val = values[0]
            p2 = (p1[0]+ux*val, p1[1]+uy*val, self.Z)
            self.viewer_ref.sketch_ops.line(p1, p2)
        self.points.clear()
        self._clear_preview()
        if self.dim_input:
            self.dim_input.hide()
