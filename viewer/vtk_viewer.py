# -*- coding: utf-8 -*-
"""
VTK Viewer — Fusion-style Interactive Sketching with Live/Fixed Dimensions + Input
Author: AlumProCNC Team

Features:
- Interactive sketch tools: Line / Circle / Rectangle / Arc (with live preview)
- Live dimension near mouse; fixed dimension labels after commit
- Immediate numeric input near cursor to set exact size (Line length, Circle radius, Rect WxH)
- Full camera controls (Rotate: LMB, Pan: MMB, Zoom: Wheel)
- Grid + central Axes + trihedron marker
- Gray toolbar with camera utilities (Zoom In/Out, Pan step, Fit, Iso, Clear Dims)
"""

from math import sqrt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar, QStyle, QFrame, QLineEdit
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QSize
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk
from draw.sketch_ops import SketchOps


def _dbg(msg: str):
    print(f"[DEBUG] {msg}")


# --------------------------- Interactor Style ---------------------------

class SketchInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    """Fusion-style drawing with live preview + live/fixed dimensions, preserving camera controls."""
    def __init__(self, renderer, viewer_ref):
        super().__init__()
        self.renderer = renderer
        self.viewer_ref = viewer_ref
        self.points = []             # clicked world points
        self.temp_actor = None       # preview geometry
        self.last_display_pos = (0, 0)

        # Live text (near cursor) and fixed labels storage
        self.text_actor = vtk.vtkTextActor()
        self.text_actor.GetTextProperty().SetFontSize(16)
        self.text_actor.GetTextProperty().SetColor(0.2, 0.2, 0.2)
        self.text_actor.VisibilityOff()
        self.renderer.AddActor2D(self.text_actor)

        self.permanent_labels = []   # list[vtkTextActor]

        # Live numeric input support
        self.live_dim_value = None    # last numeric entered
        self.live_tool_when_input = None

        # Events
        self.AddObserver("LeftButtonPressEvent", self.on_left_down)
        self.AddObserver("MouseMoveEvent", self.on_mouse_move)
        self.AddObserver("RightButtonPressEvent", self.on_right_down)

    # ---------------- Helpers ----------------
    def _update_preview(self, actor):
        if self.temp_actor:
            self.renderer.RemoveActor(self.temp_actor)
        self.temp_actor = actor
        self.renderer.AddActor(actor)
        self.renderer.GetRenderWindow().Render()

    def _clear_preview(self):
        self.points = []
        if self.temp_actor:
            self.renderer.RemoveActor(self.temp_actor)
            self.temp_actor = None
        self.text_actor.VisibilityOff()
        self.renderer.GetRenderWindow().Render()

    def _place_fixed_label(self, text: str, display_pos: tuple[int, int]):
        lbl = vtk.vtkTextActor()
        lbl.SetInput(text)
        lbl.GetTextProperty().SetFontSize(16)
        lbl.GetTextProperty().SetColor(0.25, 0.25, 0.25)
        # Avoid sticking to the absolute corner: offset a bit
        lbl.SetDisplayPosition(display_pos[0] + 15, display_pos[1] + 10)
        self.renderer.AddActor2D(lbl)
        self.permanent_labels.append(lbl)

    # ---------------- Numeric Apply (called by viewer) ----------------
    def apply_live_dimension(self, value: float, raw_text: str):
        """Apply input while drawing; value is parsed numeric, raw_text original."""
        tool = getattr(self.viewer_ref, "current_tool", None)
        self.live_dim_value = value
        self.live_tool_when_input = tool

        # Guarantees render window:
        rw = self.viewer_ref.vtk_widget.GetRenderWindow()

        # LINE: from P1 along current mouse direction
        if tool == "line" and len(self.points) == 1:
            p1 = self.points[0]
            # Determine direction from p1 -> current mouse world
            # (fallback +X if zero)
            interactor = self.GetInteractor()
            pos = interactor.GetEventPosition()
            picker = vtk.vtkCellPicker()
            picker.Pick(pos[0], pos[1], 0, self.renderer)
            cur = picker.GetPickPosition()
            vx, vy = cur[0] - p1[0], cur[1] - p1[1]
            mag = sqrt(vx*vx + vy*vy) or 1.0
            ux, uy = vx / mag, vy / mag
            p2 = (p1[0] + ux * value, p1[1] + uy * value, 0.0)
            self.viewer_ref.sketch_ops.line(p1, p2)
            self._place_fixed_label(f"{value:.1f} mm", pos)
            self._clear_preview()
            rw.Render()
            return

        # CIRCLE: center at P1, radius = value
        if tool == "circle" and len(self.points) == 1:
            c = self.points[0]
            self.viewer_ref.sketch_ops.circle(c, value)
            # Place label near cursor
            interactor = self.GetInteractor()
            pos = interactor.GetEventPosition()
            self._place_fixed_label(f"R = {value:.1f} mm", pos)
            self._clear_preview()
            rw.Render()
            return

        # RECT: width x height
        if tool == "rect" and len(self.points) == 1:
            # Parse raw_text for WxH (like 80x30 or 80*30)
            w, h = None, None
            txt = raw_text.lower().replace(' ', '')
            for sep in ('x', '*'):
                if sep in txt:
                    parts = txt.split(sep, 1)
                    try:
                        w = float(parts[0]); h = float(parts[1])
                    except Exception:
                        pass
                    break
            if w is None and h is None:
                # single number -> square
                w = h = value

            p1 = self.points[0]
            # Use current mouse to determine quadrant
            interactor = self.GetInteractor()
            pos = interactor.GetEventPosition()
            picker = vtk.vtkCellPicker()
            picker.Pick(pos[0], pos[1], 0, self.renderer)
            cur = picker.GetPickPosition()
            sx = 1.0 if cur[0] >= p1[0] else -1.0
            sy = 1.0 if cur[1] >= p1[1] else -1.0
            self.viewer_ref.sketch_ops.rectangle((p1[0], p1[1], 0.0), sx * abs(w), sy * abs(h))
            self._place_fixed_label(f"{abs(w):.1f} × {abs(h):.1f} mm", pos)
            self._clear_preview()
            rw.Render()
            return

        # ARC: (not interactive via numeric yet)
        # Could parse "R=..;A=.." later if needed.

    # ---------------- Events ----------------
    def on_left_down(self, obj, evt):
        tool = getattr(self.viewer_ref, "current_tool", None)
        interactor = self.GetInteractor()
        pos = interactor.GetEventPosition()

        picker = vtk.vtkCellPicker()
        picker.Pick(pos[0], pos[1], 0, self.renderer)
        world = picker.GetPickPosition()
        self.last_display_pos = pos

        # If no tool -> camera rotate
        if not tool or tool == "none":
            super().OnLeftButtonDown()
            return

        _dbg(f"🟢 Left click ({tool}) at: {world}")

        # LINE
        if tool == "line":
            self.points.append(world)
            if len(self.points) == 2:
                self.viewer_ref.sketch_ops.line(self.points[0], self.points[1])
                # Fixed label
                p1, p2 = self.points
                d = sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
                self._place_fixed_label(f"{d:.1f} mm", pos)
                self._clear_preview()

        # CIRCLE (center -> radius)
        elif tool == "circle":
            if len(self.points) == 0:
                self.points.append(world)
                # show input near cursor
                self.viewer_ref._show_dim_input(pos)
            else:
                c = self.points[0]
                e = world
                r = sqrt((c[0]-e[0])**2 + (c[1]-e[1])**2)
                self.viewer_ref.sketch_ops.circle(c, r)
                self._place_fixed_label(f"R = {r:.1f} mm", pos)
                self._clear_preview()

        # RECT (p1 -> p2)
        elif tool == "rect":
            if len(self.points) == 0:
                self.points.append(world)
                self.viewer_ref._show_dim_input(pos)  # allow typing WxH
            else:
                p1, p2 = self.points[0], world
                x_min, x_max = sorted([p1[0], p2[0]])
                y_min, y_max = sorted([p1[1], p2[1]])
                self.viewer_ref.sketch_ops.rectangle((x_min, y_min, 0.0),
                                                     abs(x_max - x_min),
                                                     abs(y_max - y_min))
                self._place_fixed_label(f"{abs(x_max-x_min):.1f} × {abs(y_max-y_min):.1f} mm", pos)
                self._clear_preview()

        # ARC (3 clicks)
        elif tool == "arc":
            self.points.append(world)
            if len(self.points) == 3:
                self.viewer_ref.sketch_ops.arc_3pt(self.points[0], self.points[1], self.points[2])
                self._clear_preview()

    def on_mouse_move(self, obj, evt):
        tool = getattr(self.viewer_ref, "current_tool", None)

        interactor = self.GetInteractor()
        pos = interactor.GetEventPosition()
        self.last_display_pos = pos

        picker = vtk.vtkCellPicker()
        picker.Pick(pos[0], pos[1], 0, self.renderer)
        world = picker.GetPickPosition()

        # Live previews + live dimension text
        if tool == "circle" and len(self.points) == 1:
            c = self.points[0]
            r = sqrt((c[0]-world[0])**2 + (c[1]-world[1])**2)
            circ = vtk.vtkRegularPolygonSource()
            circ.SetCenter(*c); circ.SetRadius(r); circ.SetNumberOfSides(64); circ.Update()
            mapper = vtk.vtkPolyDataMapper(); mapper.SetInputData(circ.GetOutput())
            actor = vtk.vtkActor(); actor.SetMapper(mapper)
            actor.GetProperty().SetColor(0.7, 0.7, 0.7)
            actor.GetProperty().SetRepresentationToWireframe()
            self._update_preview(actor)
            # live text
            self.text_actor.SetInput(f"R = {r:.1f} mm")
            self.text_actor.SetDisplayPosition(pos[0] + 15, pos[1] + 10)
            self.text_actor.VisibilityOn()
            # show input near cursor
            self.viewer_ref._maybe_move_dim_input(pos)

        elif tool == "rect" and len(self.points) == 1:
            p1, p2 = self.points[0], world
            x_min, x_max = sorted([p1[0], p2[0]]); y_min, y_max = sorted([p1[1], p2[1]])
            pts = [(x_min, y_min, 0), (x_max, y_min, 0), (x_max, y_max, 0), (x_min, y_max, 0)]

            poly = vtk.vtkPolygon(); poly.GetPointIds().SetNumberOfIds(4)
            vpts = vtk.vtkPoints()
            for i, p in enumerate(pts):
                vpts.InsertNextPoint(*p); poly.GetPointIds().SetId(i, i)
            cells = vtk.vtkCellArray(); cells.InsertNextCell(poly)
            pd = vtk.vtkPolyData(); pd.SetPoints(vpts); pd.SetPolys(cells)

            mapper = vtk.vtkPolyDataMapper(); mapper.SetInputData(pd)
            actor = vtk.vtkActor(); actor.SetMapper(mapper)
            actor.GetProperty().SetColor(0.7, 0.7, 0.7)
            actor.GetProperty().SetRepresentationToWireframe()
            self._update_preview(actor)
            # live text
            w = abs(x_max - x_min); h = abs(y_max - y_min)
            self.text_actor.SetInput(f"{w:.1f} × {h:.1f} mm")
            self.text_actor.SetDisplayPosition(pos[0] + 15, pos[1] + 10)
            self.text_actor.VisibilityOn()
            self.viewer_ref._maybe_move_dim_input(pos)

        elif tool == "line" and len(self.points) == 1:
            p1, p2 = self.points[0], world
            line = vtk.vtkLineSource()
            line.SetPoint1(p1); line.SetPoint2(p2)
            mapper = vtk.vtkPolyDataMapper(); mapper.SetInputConnection(line.GetOutputPort())
            actor = vtk.vtkActor(); actor.SetMapper(mapper)
            actor.GetProperty().SetColor(0.7, 0.7, 0.7)
            actor.GetProperty().SetLineWidth(2)
            self._update_preview(actor)
            # live text
            d = sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
            self.text_actor.SetInput(f"{d:.1f} mm")
            self.text_actor.SetDisplayPosition(pos[0] + 15, pos[1] + 10)
            self.text_actor.VisibilityOn()
            self.viewer_ref._maybe_move_dim_input(pos)

        # Always pass to base for smooth camera
        super().OnMouseMove()

    def on_right_down(self, obj, evt):
        # Cancel current drawing & hide input
        self.viewer_ref._hide_dim_input()
        self._clear_preview()
        super().OnRightButtonDown()


# --------------------------- VTK Viewer Widget ---------------------------

class VTKViewer(QWidget):
    """VTK viewer with gray toolbar, grid, axes, interactive sketch tools, and live/fixed dimensions + input."""
    def __init__(self, parent=None):
        super().__init__(parent)

        # Layout root
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0)
        top_bar = self._build_toolbar()  # gray toolbar
        root.addWidget(top_bar)

        # VTK widget
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        # self.vtk_widget.setFrameShape(QFrame.NoFrame)  # not supported by QVTKRenderWindowInteractor
        root.addWidget(self.vtk_widget, 1)

        # Renderer
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.97, 0.975, 0.97)
        self.renderer.SetBackground2(0.78, 0.78, 0.78)
        self.renderer.GradientBackgroundOn()
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)

        # Sketch tools
        self.current_tool = "none"
        self.sketch_ops = SketchOps(self)

        # Camera setup
        cam = self.renderer.GetActiveCamera()
        cam.SetPosition(200, 200, 150)
        cam.SetFocalPoint(0, 0, 0)
        cam.SetViewUp(0, 0, 1)
        self.renderer.ResetCamera()
        self.renderer.ResetCameraClippingRange()

        # Interactor + custom style
        self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
        self.style = SketchInteractorStyle(self.renderer, self)
        self.interactor.SetInteractorStyle(self.style)

        # Grid + axes
        self._add_grid(size=200, spacing=10, color=(0.85, 0.85, 0.85))
        self._add_axes()
        self._add_trihedron()

        # Live numeric input (Qt) — overlay near cursor
        self.dim_input = QLineEdit(self)
        self.dim_input.setFixedWidth(90)
        self.dim_input.setAlignment(Qt.AlignCenter)
        self.dim_input.setPlaceholderText("len / R / W×H")
        self.dim_input.setStyleSheet("""
            QLineEdit {
                background: #fffffb; border: 1px solid #9a9a9a;
                border-radius: 4px; padding: 2px 6px; color: #222;
            }
        """)
        self.dim_input.hide()
        self.dim_input.returnPressed.connect(self._apply_dim_input)

        # Initial render
        self.vtk_widget.GetRenderWindow().Render()
        self.interactor.Initialize()
        print("✅ VTKViewer ready — camera + drawing + grid + axes + live input.")

    # ---------------- Toolbar ----------------
    def _build_toolbar(self) -> QToolBar:
        bar = QToolBar(self)
        bar.setMovable(False)
        bar.setFloatable(False)
        bar.setIconSize(QSize(18, 18))
        bar.setStyleSheet("""
            QToolBar { background: #f2f2f2; border: 0px; padding: 4px; }
            QToolButton { color: #444; }
            QToolButton:hover { background: #e9e9e9; }
        """)

        style = self.style()
        ico_zoom_in  = style.standardIcon(QStyle.SP_ArrowUp)
        ico_zoom_out = style.standardIcon(QStyle.SP_ArrowDown)
        ico_pan      = style.standardIcon(QStyle.SP_ArrowRight)
        ico_fit      = style.standardIcon(QStyle.SP_BrowserReload)
        ico_iso      = style.standardIcon(QStyle.SP_ComputerIcon)
        ico_clear    = style.standardIcon(QStyle.SP_DialogResetButton)

        a_zoom_in  = QAction(ico_zoom_in,  "Zoom In",  self, triggered=self._zoom_in)
        a_zoom_out = QAction(ico_zoom_out, "Zoom Out", self, triggered=self._zoom_out)
        a_pan      = QAction(ico_pan,      "Pan +X",   self, triggered=self._pan_step)
        a_fit      = QAction(ico_fit,      "Fit",      self, triggered=self._fit_view)
        a_iso      = QAction(ico_iso,      "Iso",      self, triggered=self._view_iso)
        a_clear    = QAction(ico_clear,    "Clear Dims", self, triggered=self._clear_dims)

        bar.addAction(a_zoom_in)
        bar.addAction(a_zoom_out)
        bar.addSeparator()
        bar.addAction(a_pan)
        bar.addSeparator()
        bar.addAction(a_fit)
        bar.addAction(a_iso)
        bar.addSeparator()
        bar.addAction(a_clear)
        return bar

    # Camera helpers (toolbar)
    def _zoom_in(self):
        self.renderer.GetActiveCamera().Dolly(1.2)
        self.renderer.ResetCameraClippingRange()
        self.vtk_widget.GetRenderWindow().Render()

    def _zoom_out(self):
        self.renderer.GetActiveCamera().Dolly(1/1.2)
        self.renderer.ResetCameraClippingRange()
        self.vtk_widget.GetRenderWindow().Render()

    def _pan_step(self):
        cam = self.renderer.GetActiveCamera()
        fp = list(cam.GetFocalPoint()); pos = list(cam.GetPosition())
        dx = 10.0
        fp[0] += dx; pos[0] += dx
        cam.SetFocalPoint(*fp); cam.SetPosition(*pos)
        self.vtk_widget.GetRenderWindow().Render()

    def _fit_view(self):
        self.renderer.ResetCamera()
        self.renderer.ResetCameraClippingRange()
        self.vtk_widget.GetRenderWindow().Render()

    def _view_iso(self):
        cam = self.renderer.GetActiveCamera()
        cam.SetPosition(200, 200, 150)
        cam.SetFocalPoint(0, 0, 0)
        cam.SetViewUp(0, 0, 1)
        self.renderer.ResetCameraClippingRange()
        self.vtk_widget.GetRenderWindow().Render()

    # ---------------- Grid + Axes ----------------
    def _add_grid(self, size=200, spacing=10, color=(0.85, 0.85, 0.85)):
        app = vtk.vtkAppendPolyData()
        for i in range(-size, size + spacing, spacing):
            lx = vtk.vtkLineSource(); lx.SetPoint1(-size, i, 0); lx.SetPoint2(size, i, 0); lx.Update()
            ly = vtk.vtkLineSource(); ly.SetPoint1(i, -size, 0); ly.SetPoint2(i, size, 0); ly.Update()
            app.AddInputData(lx.GetOutput()); app.AddInputData(ly.GetOutput())
        app.Update()

        mapper = vtk.vtkPolyDataMapper(); mapper.SetInputData(app.GetOutput())
        actor = vtk.vtkActor(); actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)
        actor.GetProperty().SetLineWidth(1)
        actor.GetProperty().LightingOff()
        self.renderer.AddActor(actor)

    def _add_axes(self):
        axes = vtk.vtkAxesActor()
        axes.SetTotalLength(50, 50, 50)
        axes.AxisLabelsOn()
        self.renderer.AddActor(axes)

    def _add_trihedron(self):
        tri = vtk.vtkAxesActor()
        tri_marker = vtk.vtkOrientationMarkerWidget()
        tri_marker.SetOrientationMarker(tri)
        tri_marker.SetInteractor(self.vtk_widget.GetRenderWindow().GetInteractor())
        tri_marker.SetViewport(0.0, 0.0, 0.18, 0.18)
        tri_marker.EnabledOn()
        tri_marker.InteractiveOff()

    # ---------------- Dimension Input Overlay ----------------
    def _show_dim_input(self, display_pos: tuple[int, int]):
        # show near cursor, but keep on-screen
        x = max(0, display_pos[0] + 30)
        y = max(0, display_pos[1] + 30)
        self.dim_input.move(x, y)
        self.dim_input.setText("")   # clear previous
        self.dim_input.show()
        self.dim_input.raise_()
        self.dim_input.setFocus()

    def _maybe_move_dim_input(self, display_pos: tuple[int, int]):
        if self.dim_input.isVisible():
            x = max(0, display_pos[0] + 30)
            y = max(0, display_pos[1] + 30)
            self.dim_input.move(x, y)

    def _hide_dim_input(self):
        self.dim_input.hide()

    def _apply_dim_input(self):
        raw = self.dim_input.text().strip()
        if not raw:
            self._hide_dim_input()
            return
        # Parse numeric: allow "R=50", "50", "80x30", "80*30"
        txt = raw.lower().replace(' ', '')
        val = None
        if txt.startswith('r='):
            try:
                val = float(txt[2:])
            except Exception:
                val = None
        else:
            # if contains x/* we still pass numeric part for rect square fallback
            try:
                # take first float in string as main value (robust)
                num = ''
                for ch in txt:
                    if (ch.isdigit() or ch in '.-'):
                        num += ch
                    elif num:
                        break
                val = float(num) if num else None
            except Exception:
                val = None

        self._hide_dim_input()
        if val is None:
            return

        # Delegate to interactor style
        if hasattr(self.style, "apply_live_dimension"):
            self.style.apply_live_dimension(val, raw)

    # Clear all fixed dimension labels
    def _clear_dims(self):
        for lbl in self.style.permanent_labels:
            self.renderer.RemoveActor(lbl)
        self.style.permanent_labels.clear()
        self.vtk_widget.GetRenderWindow().Render()

    # ---------------- Public API ----------------
    def set_active_tool(self, tool_name: str):
        self.current_tool = tool_name or "none"
        print(f"🎯 تم تعيين الأداة الحالية إلى: {self.current_tool}")
