# -*- coding: utf-8 -*-
"""
VTK Viewer — Fusion-style Interactive Sketching
- Live preview + live text near cursor
- Fixed dimensions: 3D labels (vtkVectorText + vtkFollower) attached to shapes
- Numeric input near cursor (Line length, Circle radius, Rect WxH)
- Full camera controls (Rotate: LMB, Pan: MMB, Zoom: Wheel)
- Grid + central Axes + trihedron
- Gray toolbar (Zoom In/Out, Pan step, Fit, Iso, Clear Dims)
- Soft Fusion-like colors for each primitive
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


# --------------------------- helpers ---------------------------

def _soft_color(hex_str: str):
    """#RRGGBB -> (r,g,b) in 0..1"""
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16)/255.0 for i in (0, 2, 4))

def _circle_center_from_3pts(p1, p2, p3):
    """Compute circle center in XY from 3 non-colinear points. Returns (cx,cy,0) or None."""
    (x1,y1,_),(x2,y2,_),(x3,y3,_) = p1,p2,p3
    a = 2*(x1*(y2-y3)+x2*(y3-y1)+x3*(y1-y2))
    if abs(a) < 1e-6:
        return None
    x1s,y1s = x1*x1+y1*y1, y1
    x2s,y2s = x2*x2+y2*y2, y2
    x3s,y3s = x3*x3+y3*y3, y3
    cx = ((x1s*(y2-y3)+x2s*(y3-y1)+x3s*(y1-y2))/a)
    cy = ((x1*(x2s-x3s)+x2*(x3s-x1s)+x3*(x1s-x2s))/a)
    return (cx, cy, 0.0)

def _midpoint(p1, p2):
    return ((p1[0]+p2[0])/2.0, (p1[1]+p2[1])/2.0, (p1[2]+p2[2])/2.0)


# --------------------------- Interactor Style ---------------------------

class SketchInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    """Fusion-style drawing with live preview + fixed 3D labels, preserving camera controls."""
    def __init__(self, renderer, viewer_ref):
        super().__init__()
        self.renderer = renderer
        self.viewer_ref = viewer_ref
        self.points = []             # clicked world points
        self.temp_actor = None       # preview geometry
        self.last_display_pos = (0, 0)

        # Live 2D text (near cursor)
        self.text_actor = vtk.vtkTextActor()
        self.text_actor.GetTextProperty().SetFontSize(16)
        self.text_actor.GetTextProperty().SetColor(0.2, 0.2, 0.2)
        self.text_actor.VisibilityOff()
        self.renderer.AddActor2D(self.text_actor)

        # Permanent 3D labels (vtkFollower)
        self.permanent_labels = []   # list[vtkFollower]

        # live numeric input state
        self.live_dim_value = None
        self.live_tool_when_input = None

        # Colors (Fusion-like soft)
        self.colors = {
            "line":   _soft_color("#4A90E2"),  # soft blue
            "circle": _soft_color("#F5A623"),  # soft orange
            "rect":   _soft_color("#7ED321"),  # soft green
            "arc":    _soft_color("#9B59B6"),  # soft purple
            "preview": (0.7, 0.7, 0.7),
        }

        # Events
        self.AddObserver("LeftButtonPressEvent", self.on_left_down)
        self.AddObserver("MouseMoveEvent", self.on_mouse_move)
        self.AddObserver("RightButtonPressEvent", self.on_right_down)

    # ---------------- internal display helpers ----------------
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

    def _place_fixed_label(self, text: str, world_pos: tuple[float, float, float]):
        """3D label that follows camera zoom/rotation (attached to shape)."""
        vector_text = vtk.vtkVectorText()
        vector_text.SetText(text)

        text_mapper = vtk.vtkPolyDataMapper()
        text_mapper.SetInputConnection(vector_text.GetOutputPort())

        follower = vtk.vtkFollower()
        follower.SetMapper(text_mapper)
        follower.SetScale(2.0, 2.0, 2.0)  # text size
        follower.SetPosition(*world_pos)
        follower.GetProperty().SetColor(0.2, 0.2, 0.2)
        follower.SetCamera(self.renderer.GetActiveCamera())  # follow camera

        self.renderer.AddActor(follower)
        self.permanent_labels.append(follower)

    # ---------------- numeric apply (called by viewer) ----------------
    def apply_live_dimension(self, value: float, raw_text: str):
        tool = getattr(self.viewer_ref, "current_tool", None)
        self.live_dim_value = value
        self.live_tool_when_input = tool
        rw = self.viewer_ref.vtk_widget.GetRenderWindow()

        # LINE: fix length from P1 towards current cursor
        if tool == "line" and len(self.points) == 1:
            p1 = self.points[0]
            interactor = self.GetInteractor()
            pos = interactor.GetEventPosition()
            picker = vtk.vtkCellPicker()
            picker.Pick(pos[0], pos[1], 0, self.renderer)
            cur = picker.GetPickPosition()
            vx, vy = cur[0]-p1[0], cur[1]-p1[1]
            mag = sqrt(vx*vx+vy*vy) or 1.0
            ux, uy = vx/mag, vy/mag
            p2 = (p1[0] + ux*value, p1[1] + uy*value, 0.0)
            self.viewer_ref.sketch_ops.line(p1, p2, color=self.colors["line"])
            self._place_fixed_label(f"{value:.1f} mm", _midpoint(p1, p2))
            self._clear_preview()
            rw.Render()
            return

        # CIRCLE: radius
        if tool == "circle" and len(self.points) == 1:
            c = self.points[0]
            self.viewer_ref.sketch_ops.circle(c, value, color=self.colors["circle"])
            # place at point on circumference
            e = (c[0]+value, c[1], 0.0)
            self._place_fixed_label(f"R = {value:.1f} mm", e)
            self._clear_preview()
            rw.Render()
            return

        # RECT: WxH (parse raw)
        if tool == "rect" and len(self.points) == 1:
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
                w = h = value
            p1 = self.points[0]
            interactor = self.GetInteractor()
            pos = interactor.GetEventPosition()
            picker = vtk.vtkCellPicker()
            picker.Pick(pos[0], pos[1], 0, self.renderer)
            cur = picker.GetPickPosition()
            sx = 1.0 if cur[0] >= p1[0] else -1.0
            sy = 1.0 if cur[1] >= p1[1] else -1.0
            self.viewer_ref.sketch_ops.rectangle((p1[0], p1[1], 0.0),
                                                 sx*abs(w), sy*abs(h),
                                                 color=self.colors["rect"])
            center = (p1[0] + sx*abs(w)/2.0, p1[1] + sy*abs(h)/2.0, 0.0)
            self._place_fixed_label(f"{abs(w):.1f} × {abs(h):.1f} mm", center)
            self._clear_preview()
            rw.Render()
            return

    # ---------------- events ----------------
    def on_left_down(self, obj, evt):
        tool = getattr(self.viewer_ref, "current_tool", None)
        interactor = self.GetInteractor()
        pos = interactor.GetEventPosition()

        picker = vtk.vtkCellPicker()
        picker.Pick(pos[0], pos[1], 0, self.renderer)
        world = picker.GetPickPosition()
        self.last_display_pos = pos

        if not tool or tool == "none":
            super().OnLeftButtonDown()
            return

        _dbg(f"🟢 Left click ({tool}) at: {world}")

        if tool == "line":
            self.points.append(world)
            if len(self.points) == 2:
                p1, p2 = self.points
                self.viewer_ref.sketch_ops.line(p1, p2, color=self.colors["line"])
                d = sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
                self._place_fixed_label(f"{d:.1f} mm", _midpoint(p1, p2))
                self._clear_preview()

        elif tool == "circle":
            if len(self.points) == 0:
                self.points.append(world)
                self.viewer_ref._show_dim_input(pos)  # allow numeric radius now
            else:
                c = self.points[0]; e = world
                r = sqrt((c[0]-e[0])**2 + (c[1]-e[1])**2)
                self.viewer_ref.sketch_ops.circle(c, r, color=self.colors["circle"])
                self._place_fixed_label(f"R = {r:.1f} mm", e)
                self._clear_preview()

        elif tool == "rect":
            if len(self.points) == 0:
                self.points.append(world)
                self.viewer_ref._show_dim_input(pos)  # allow WxH
            else:
                p1, p2 = self.points[0], world
                x_min, x_max = sorted([p1[0], p2[0]])
                y_min, y_max = sorted([p1[1], p2[1]])
                self.viewer_ref.sketch_ops.rectangle((x_min, y_min, 0.0),
                                                     abs(x_max - x_min),
                                                     abs(y_max - y_min),
                                                     color=self.colors["rect"])
                center = ((x_min+x_max)/2.0, (y_min+y_max)/2.0, 0.0)
                self._place_fixed_label(f"{abs(x_max-x_min):.1f} × {abs(y_max-y_min):.1f} mm", center)
                self._clear_preview()

        elif tool == "arc":
            # 3 clicks: start, on-arc point, end
            self.points.append(world)
            if len(self.points) == 3:
                p1, pm, p2 = self.points
                # let SketchOps finalize
                self.viewer_ref.sketch_ops.arc_3pt(p1, pm, p2, color=self.colors["arc"])
                # label at arc mid (approximate via normalized sum)
                c = _circle_center_from_3pts(p1, pm, p2)
                if c:
                    import math
                    def unit(v):
                        m = math.hypot(v[0], v[1]);
                        return (v[0]/m, v[1]/m) if m else (1.0,0.0)
                    r = sqrt((p1[0]-c[0])**2 + (p1[1]-c[1])**2)
                    u1 = unit((p1[0]-c[0], p1[1]-c[1])); u2 = unit((p2[0]-c[0], p2[1]-c[1]))
                    um = unit((u1[0]+u2[0], u1[1]+u2[1]))
                    mid = (c[0]+um[0]*r, c[1]+um[1]*r, 0.0)
                    self._place_fixed_label(f"R ≈ {r:.1f} mm", mid)
                self._clear_preview()

    def on_mouse_move(self, obj, evt):
        tool = getattr(self.viewer_ref, "current_tool", None)

        interactor = self.GetInteractor()
        pos = interactor.GetEventPosition()
        self.last_display_pos = pos

        picker = vtk.vtkCellPicker()
        picker.Pick(pos[0], pos[1], 0, self.renderer)
        world = picker.GetPickPosition()

        # circle preview
        if tool == "circle" and len(self.points) == 1:
            c = self.points[0]
            r = sqrt((c[0]-world[0])**2 + (c[1]-world[1])**2)
            circ = vtk.vtkRegularPolygonSource()
            circ.SetCenter(*c); circ.SetRadius(r); circ.SetNumberOfSides(64); circ.Update()
            mapper = vtk.vtkPolyDataMapper(); mapper.SetInputData(circ.GetOutput())
            actor = vtk.vtkActor(); actor.SetMapper(mapper)
            actor.GetProperty().SetColor(*self.colors["preview"])
            actor.GetProperty().SetRepresentationToWireframe()
            self._update_preview(actor)
            self.text_actor.SetInput(f"R = {r:.1f} mm")
            self.text_actor.SetDisplayPosition(pos[0]+15, pos[1]+10)
            self.text_actor.VisibilityOn()
            self.viewer_ref._maybe_move_dim_input(pos)

        # rect preview
        elif tool == "rect" and len(self.points) == 1:
            p1, p2 = self.points[0], world
            x_min, x_max = sorted([p1[0], p2[0]]); y_min, y_max = sorted([p1[1], p2[1]])
            pts = [(x_min, y_min, 0), (x_max, y_min, 0), (x_max, y_max, 0), (x_min, y_max, 0)]
            poly = vtk.vtkPolygon(); poly.GetPointIds().SetNumberOfIds(4)
            vpts = vtk.vtkPoints()
            for i,p in enumerate(pts): vpts.InsertNextPoint(*p); poly.GetPointIds().SetId(i,i)
            cells = vtk.vtkCellArray(); cells.InsertNextCell(poly)
            pd = vtk.vtkPolyData(); pd.SetPoints(vpts); pd.SetPolys(cells)
            mapper = vtk.vtkPolyDataMapper(); mapper.SetInputData(pd)
            actor = vtk.vtkActor(); actor.SetMapper(mapper)
            actor.GetProperty().SetColor(*self.colors["preview"])
            actor.GetProperty().SetRepresentationToWireframe()
            self._update_preview(actor)
            w = abs(x_max-x_min); h = abs(y_max-y_min)
            self.text_actor.SetInput(f"{w:.1f} × {h:.1f} mm")
            self.text_actor.SetDisplayPosition(pos[0]+15, pos[1]+10)
            self.text_actor.VisibilityOn()
            self.viewer_ref._maybe_move_dim_input(pos)

        # line preview
        elif tool == "line" and len(self.points) == 1:
            p1, p2 = self.points[0], world
            line = vtk.vtkLineSource()
            line.SetPoint1(p1); line.SetPoint2(p2)
            mapper = vtk.vtkPolyDataMapper(); mapper.SetInputConnection(line.GetOutputPort())
            actor = vtk.vtkActor(); actor.SetMapper(mapper)
            actor.GetProperty().SetColor(*self.colors["preview"])
            actor.GetProperty().SetLineWidth(2)
            self._update_preview(actor)
            d = sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
            self.text_actor.SetInput(f"{d:.1f} mm")
            self.text_actor.SetDisplayPosition(pos[0]+15, pos[1]+10)
            self.text_actor.VisibilityOn()
            self.viewer_ref._maybe_move_dim_input(pos)

        # arc preview (after 2nd point, use 1st=start, 2nd=on-arc, mouse=end)
        elif tool == "arc" and len(self.points) == 2:
            p1, pm = self.points[0], self.points[1]
            p2 = world
            c = _circle_center_from_3pts(p1, pm, p2)
            if c:
                # ✅ Compatible Arc Preview (for all VTK versions)
                import math
                num_pts = 100
                arc_points = vtk.vtkPoints()
                arc_lines = vtk.vtkCellArray()

                r = math.hypot(p1[0] - c[0], p1[1] - c[1])
                ang1 = math.atan2(p1[1] - c[1], p1[0] - c[0])
                ang2 = math.atan2(p2[1] - c[1], p2[0] - c[0])
                # تأكد الاتجاه الصحيح (اتجاه عقارب الساعة أو عكسها)
                if (ang2 < ang1):
                    ang2 += 2 * math.pi

                for i in range(num_pts):
                    t = i / (num_pts - 1)
                    ang = ang1 + t * (ang2 - ang1)
                    x = c[0] + r * math.cos(ang)
                    y = c[1] + r * math.sin(ang)
                    arc_points.InsertNextPoint(x, y, 0)

                for i in range(num_pts - 1):
                    line = vtk.vtkLine()
                    line.GetPointIds().SetId(0, i)
                    line.GetPointIds().SetId(1, i + 1)
                    arc_lines.InsertNextCell(line)

                arc_poly = vtk.vtkPolyData()
                arc_poly.SetPoints(arc_points)
                arc_poly.SetLines(arc_lines)

                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputData(arc_poly)
                actor = vtk.vtkActor()
                actor.SetMapper(mapper)

                actor.GetProperty().SetColor(*self.colors["preview"])
                actor.GetProperty().SetLineWidth(2)
                self._update_preview(actor)
                # live text radius
                r = sqrt((p1[0]-c[0])**2 + (p1[1]-c[1])**2)
                self.text_actor.SetInput(f"R ≈ {r:.1f} mm")
                self.text_actor.SetDisplayPosition(pos[0]+15, pos[1]+10)
                self.text_actor.VisibilityOn()
            else:
                # colinear -> no preview
                if self.temp_actor:
                    self.renderer.RemoveActor(self.temp_actor)
                    self.temp_actor = None
                self.text_actor.VisibilityOff()
                self.renderer.GetRenderWindow().Render()

        super().OnMouseMove()

    def on_right_down(self, obj, evt):
        self.viewer_ref._hide_dim_input()
        self._clear_preview()
        super().OnRightButtonDown()


# --------------------------- VTK Viewer Widget ---------------------------

class VTKViewer(QWidget):
    """VTK viewer with gray toolbar, grid, axes, interactive sketch tools, live/fixed dimensions and numeric input."""
    def __init__(self, parent=None):
        super().__init__(parent)

        # Layout root
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0)
        top_bar = self._build_toolbar()
        root.addWidget(top_bar)

        # VTK widget
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        # self.vtk_widget.setFrameShape(QFrame.NoFrame)  # not supported
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

        # Numeric input (Qt) overlay near cursor
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
        print("✅ VTKViewer ready — camera + drawing + grid + axes + live input + 3D labels.")

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

        a_zoom_in  = QAction(ico_zoom_in,  "Zoom In",   self, triggered=self._zoom_in)
        a_zoom_out = QAction(ico_zoom_out, "Zoom Out",  self, triggered=self._zoom_out)
        a_pan      = QAction(ico_pan,      "Pan +X",    self, triggered=self._pan_step)
        a_fit      = QAction(ico_fit,      "Fit",       self, triggered=self._fit_view)
        a_iso      = QAction(ico_iso,      "Iso",       self, triggered=self._view_iso)
        a_clear    = QAction(ico_clear,    "Clear Dims",self, triggered=self._clear_dims)

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
        x = max(0, display_pos[0] + 30)
        y = max(0, display_pos[1] + 30)
        self.dim_input.move(x, y)
        self.dim_input.setText("")
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
        txt = raw.lower().replace(' ', '')
        val = None
        if txt.startswith('r='):
            try: val = float(txt[2:])
            except: val = None
        else:
            try:
                num='';
                for ch in txt:
                    if (ch.isdigit() or ch in '.-'): num+=ch
                    elif num: break
                val = float(num) if num else None
            except: val = None

        self._hide_dim_input()
        if val is None:
            return
        if hasattr(self.style, "apply_live_dimension"):
            self.style.apply_live_dimension(val, raw)

    # Clear all fixed 3D dimension labels
    def _clear_dims(self):
        for lbl in self.style.permanent_labels:
            self.renderer.RemoveActor(lbl)
        self.style.permanent_labels.clear()
        self.vtk_widget.GetRenderWindow().Render()

    # ---------------- Public API ----------------
    def set_active_tool(self, tool_name: str):
        self.current_tool = tool_name or "none"
        print(f"🎯 تم تعيين الأداة الحالية إلى: {self.current_tool}")
