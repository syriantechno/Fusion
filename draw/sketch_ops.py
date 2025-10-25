# -*- coding: utf-8 -*-
"""
AlumProCNC — Sketch & Modify (Fusion-style) — Single-file Edition
يشمل:
- SketchOps: line / circle / rect / arc(3pt) + نظام نقرات تفاعلي
- ModifyOps (مضمن): trim / offset / mirror / fillet
- توافق تلقائي مع VTK أو pythonOCC
- ألوان Fusion-like لكل أداة
- ملصقات قياس ثلاثية الأبعاد (VTK) باستخدام vtkVectorText + vtkFollower (اختياري)
"""

from typing import List, Tuple, Optional
import math

# نحاول استيراد OCC؛ إن لم يتوفر نعمل VTK فقط
try:
    from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Ax2
    from OCC.Core.GC import GC_MakeLine, GC_MakeCircle, GC_MakeArcOfCircle
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire
    from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
    _HAS_OCC = True
except Exception:
    _HAS_OCC = False

ColorTuple = Tuple[float, float, float]
Point3D = Tuple[float, float, float]


def _debug(msg: str):
    print(f"[SKETCH] {msg}")


def _qcolor(rgb: ColorTuple):
    if not _HAS_OCC:
        return None
    r, g, b = rgb
    return Quantity_Color(r, g, b, Quantity_TOC_RGB)


# ------------------------------------------------------------
# ModifyOps — أدوات التعديل (مضمنة)
# ------------------------------------------------------------
class ModifyOps:
    """أدوات تعديل مبدئية: Trim / Offset / Mirror / Fillet (متوافقة مع VTK)"""
    def __init__(self, viewer):
        self.viewer = viewer
        # نتوقع أن يكون لدى viewer خاصية renderer في وضع VTK
        self.renderer = getattr(viewer, "renderer", None)

    # ✂️ Trim: يحذف أقرب actor للنقطة (نسخة أولى — لاحقاً نستبدلها بقص هندسي)
    def trim(self, click_world: Point3D, pick_radius: float = 20.0):
        if not self.renderer:
            _debug("Trim: renderer غير متوفر (OCC مدعوم لاحقًا).")
            return
        actors = self.renderer.GetActors()
        actors.InitTraversal()
        closest, best = None, float("inf")
        a = actors.GetNextActor()
        while a:
            try:
                b = a.GetBounds()
                cx, cy = (b[0]+b[1])/2.0, (b[2]+b[3])/2.0
                d = math.hypot(click_world[0]-cx, click_world[1]-cy)
                if d < best:
                    best, closest = d, a
            except Exception:
                pass
            a = actors.GetNextActor()
        if closest and best < pick_radius:
            self.renderer.RemoveActor(closest)
            self.renderer.GetRenderWindow().Render()
            _debug("✂️ Trim: تم حذف الجزء الأقرب.")
        else:
            _debug("Trim: لا يوجد عنصر قريب.")

    # ↔ Offset: إزاحة بسيطة (ترجمة — تحسين لاحقاً للإزاحة الهندسية)
    def offset(self, base_actor, distance: float = 10.0):
        if not self.renderer or not base_actor:
            return
        import vtk
        tf = vtk.vtkTransform()
        tf.Translate(distance, distance, 0)
        filt = vtk.vtkTransformPolyDataFilter()
        filt.SetInputData(base_actor.GetMapper().GetInput())
        filt.SetTransform(tf)
        filt.Update()
        m = vtk.vtkPolyDataMapper()
        m.SetInputData(filt.GetOutput())
        n = vtk.vtkActor()
        n.SetMapper(m)
        n.GetProperty().SetColor(0.45, 0.55, 0.8)
        self.renderer.AddActor(n)
        self.renderer.GetRenderWindow().Render()
        _debug(f"↔ Offset: تم إنشاء نسخة بإزاحة {distance}.")

    # 🔁 Mirror: انعكاس حول محور X أو Y (بسيط — تحسين لاحقاً)
    def mirror(self, base_actor, axis: str = "Y"):
        if not self.renderer or not base_actor:
            return
        import vtk
        s = (1, -1, 1) if axis.upper() == "X" else (-1, 1, 1)
        tf = vtk.vtkTransform()
        tf.Scale(*s)
        filt = vtk.vtkTransformPolyDataFilter()
        filt.SetInputData(base_actor.GetMapper().GetInput())
        filt.SetTransform(tf)
        filt.Update()
        m = vtk.vtkPolyDataMapper()
        m.SetInputData(filt.GetOutput())
        n = vtk.vtkActor()
        n.SetMapper(m)
        n.GetProperty().SetColor(0.5, 0.5, 0.7)
        self.renderer.AddActor(n)
        self.renderer.GetRenderWindow().Render()
        _debug(f"🔁 Mirror: تم الانعكاس حول محور {axis}.")

    # ◔ Fillet: قوس بسيط بين نقطتين (نسخة أولى)
    def fillet(self, p1: Point3D, p2: Point3D, radius: float = 5.0):
        if not self.renderer:
            return
        import vtk
        arc = vtk.vtkArcSource()
        arc.SetPoint1(*p1)
        arc.SetPoint2(*p2)
        arc.SetCenter((p1[0]+p2[0]) / 2.0, (p1[1]+p2[1]) / 2.0, 0.0)
        arc.SetResolution(64)
        arc.Update()
        m = vtk.vtkPolyDataMapper()
        m.SetInputConnection(arc.GetOutputPort())
        a = vtk.vtkActor()
        a.SetMapper(m)
        a.GetProperty().SetColor(0.6, 0.5, 0.8)
        a.GetProperty().SetLineWidth(2)
        self.renderer.AddActor(a)
        self.renderer.GetRenderWindow().Render()
        _debug("◔ Fillet: تم إنشاء قوس بين نقطتين.")


# ------------------------------------------------------------
# SketchOps — أدوات الرسم + إدارة النقرات
# ------------------------------------------------------------
class SketchOps:
    def __init__(self, display, line_width: float = 2.0):
        """
        display: قد يكون VTKViewer (يحوي renderer, vtk_widget) أو OCC display (يحوي GetContext)
        """
        self.display = display
        self.line_width = line_width
        self.modify_ops = ModifyOps(self.display)

        # كشف نوع العارض
        if hasattr(display, "GetContext") and _HAS_OCC:
            self.ctx = display.GetContext()
            self.viewer_type = "OCC"
            _debug("Linked to OCC Display Context ✅")
        else:
            self.ctx = None
            self.viewer_type = "VTK"
            _debug("Linked to VTKViewer ⚙️")

        # نقاط تفاعلية
        self.temp_points: List[Point3D] = []

        # ألوان Fusion-like للأدوات
        self.colors = {
            "line":   (0.29, 0.56, 0.89),  # أزرق ناعم
            "circle": (0.96, 0.65, 0.14),  # برتقالي
            "rect":   (0.49, 0.82, 0.13),  # أخضر
            "arc":    (0.61, 0.35, 0.71),  # بنفسجي
            "dim":    (0.20, 0.20, 0.20),  # نص القياسات
        }

    # ---------------------------- عرض/Render ----------------------------
    def _render(self):
        if self.viewer_type == "VTK":
            self.display.vtk_widget.GetRenderWindow().Render()

    def _show_occ(self, shape, color: ColorTuple):
        ais = self.display.DisplayShape(shape, update=False)
        self.ctx.SetColor(ais, _qcolor(color))
        try:
            self.ctx.SetWidth(ais, self.line_width)
        except Exception:
            pass

    def _label3d_vtk(self, text: str, world_pos: Point3D, scale: float = 2.0):
        """ملصق ثلاثي الأبعاد مرتبط بالشكل (يتبع الكاميرا)"""
        if self.viewer_type != "VTK":
            return
        import vtk
        vtext = vtk.vtkVectorText()
        vtext.SetText(text)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(vtext.GetOutputPort())
        follower = vtk.vtkFollower()
        follower.SetMapper(mapper)
        follower.SetScale(scale, scale, scale)
        follower.SetPosition(*world_pos)
        follower.GetProperty().SetColor(*self.colors["dim"])
        follower.SetCamera(self.display.renderer.GetActiveCamera())
        self.display.renderer.AddActor(follower)

    # ---------------------------- أدوات الرسم ---------------------------
    def line(self, p1: Point3D, p2: Point3D, color: Optional[ColorTuple] = None):
        color = color or self.colors["line"]
        _debug(f"Line {p1} -> {p2}")
        if self.viewer_type == "VTK":
            import vtk
            src = vtk.vtkLineSource()
            src.SetPoint1(*p1); src.SetPoint2(*p2); src.Update()
            m = vtk.vtkPolyDataMapper(); m.SetInputData(src.GetOutput())
            a = vtk.vtkActor(); a.SetMapper(m)
            a.GetProperty().SetColor(*color)
            a.GetProperty().SetLineWidth(self.line_width)
            self.display.renderer.AddActor(a)
            self._label3d_vtk(f"{math.dist((p1[0],p1[1]),(p2[0],p2[1])):.1f} mm",
                              ((p1[0]+p2[0])/2.0, (p1[1]+p2[1])/2.0, 0.0))
            self._render()
            return
        if not _HAS_OCC:
            return
        edge = BRepBuilderAPI_MakeEdge(GC_MakeLine(gp_Pnt(*p1), gp_Pnt(*p2)).Value()).Edge()
        self._show_occ(edge, color)

    def circle(self, center: Point3D, radius: float, color: Optional[ColorTuple] = None):
        color = color or self.colors["circle"]
        _debug(f"Circle C={center} R={radius}")
        if self.viewer_type == "VTK":
            import vtk
            src = vtk.vtkRegularPolygonSource()
            src.SetCenter(*center); src.SetRadius(float(radius)); src.SetNumberOfSides(64); src.Update()
            m = vtk.vtkPolyDataMapper(); m.SetInputData(src.GetOutput())
            a = vtk.vtkActor(); a.SetMapper(m)
            a.GetProperty().SetColor(*color)
            a.GetProperty().SetRepresentationToWireframe()
            a.GetProperty().SetLineWidth(self.line_width)
            self.display.renderer.AddActor(a)
            self._label3d_vtk(f"R = {radius:.1f} mm", (center[0]+radius, center[1], 0.0))
            self._render()
            return
        if not _HAS_OCC:
            return
        ax2 = gp_Ax2(gp_Pnt(*center), gp_Dir(0, 0, 1))
        circ = GC_MakeCircle(ax2, float(radius)).Value()
        edge = BRepBuilderAPI_MakeEdge(circ).Edge()
        self._show_occ(edge, color)

    def rectangle(self, origin: Point3D, width: float, height: float, color: Optional[ColorTuple] = None):
        color = color or self.colors["rect"]
        _debug(f"Rect origin={origin} w={width} h={height}")
        if self.viewer_type == "VTK":
            import vtk
            x, y, z = origin
            pts = [(x, y, z), (x+width, y, z), (x+width, y+height, z), (x, y+height, z)]
            poly = vtk.vtkPolygon(); poly.GetPointIds().SetNumberOfIds(4)
            points = vtk.vtkPoints()
            for i, p in enumerate(pts):
                points.InsertNextPoint(*p); poly.GetPointIds().SetId(i, i)
            cells = vtk.vtkCellArray(); cells.InsertNextCell(poly)
            pd = vtk.vtkPolyData(); pd.SetPoints(points); pd.SetPolys(cells)
            m = vtk.vtkPolyDataMapper(); m.SetInputData(pd)
            a = vtk.vtkActor(); a.SetMapper(m)
            a.GetProperty().SetColor(*color)
            a.GetProperty().SetRepresentationToWireframe()
            self.display.renderer.AddActor(a)
            cx, cy = x + width/2.0, y + height/2.0
            self._label3d_vtk(f"{abs(width):.1f} × {abs(height):.1f} mm", (cx, cy, 0.0))
            self._render()
            return
        if not _HAS_OCC:
            return
        x, y, z = origin
        pts = [gp_Pnt(x, y, z), gp_Pnt(x+width, y, z), gp_Pnt(x+width, y+height, z),
               gp_Pnt(x, y+height, z), gp_Pnt(x, y, z)]
        wmk = BRepBuilderAPI_MakeWire()
        for i in range(4):
            wmk.Add(BRepBuilderAPI_MakeEdge(pts[i], pts[i+1]).Edge())
        wire = wmk.Wire()
        self._show_occ(wire, color)

    def arc_3pt(self, p1: Point3D, p2: Point3D, p3: Point3D, color: Optional[ColorTuple] = None):
        color = color or self.colors["arc"]
        _debug(f"Arc 3pt: {p1} , {p2} , {p3}")
        if self.viewer_type == "VTK":
            import vtk
            # إذا كانت النقاط شبه مستقيمة، نتجاهل
            def area2(a,b,c): return abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
            if area2(p1, p2, p3) < 1e-6:
                _debug("Arc: نقاط شبه مستقيمة — تجاهل.")
                return
            # توليد قوس يدويًا (متوافق مع كل نسخ VTK)
            num_pts = 100
            # مركز الدائرة من 3 نقاط:
            c = self._circle_center_from_3pts(p1, p2, p3)
            if c is None:
                _debug("Arc: فشل إيجاد المركز — تجاهل.")
                return
            r = math.hypot(p1[0]-c[0], p1[1]-c[1])
            ang1 = math.atan2(p1[1]-c[1], p1[0]-c[0])
            angm = math.atan2(p2[1]-c[1], p2[0]-c[0])
            ang2 = math.atan2(p3[1]-c[1], p3[0]-c[0])
            # اختيار اتجاه يمر بالنقطة الوسطى
            def norm(a):
                while a < 0: a += 2*math.pi
                while a >= 2*math.pi: a -= 2*math.pi
                return a
            ang1, angm, ang2 = norm(ang1), norm(angm), norm(ang2)
            if not (ang1 <= angm <= ang2 or (ang2 < ang1 and (angm >= ang1 or angm <= ang2))):
                # اعكس الاتجاه
                ang1, ang2 = ang2, ang1
            import vtk
            pts = vtk.vtkPoints()
            lines = vtk.vtkCellArray()
            for i in range(num_pts):
                t = i/(num_pts-1)
                a = ang1 + t*(ang2-ang1)
                x = c[0] + r*math.cos(a)
                y = c[1] + r*math.sin(a)
                pts.InsertNextPoint(x, y, 0.0)
            for i in range(num_pts-1):
                ln = vtk.vtkLine()
                ln.GetPointIds().SetId(0, i)
                ln.GetPointIds().SetId(1, i+1)
                lines.InsertNextCell(ln)
            pd = vtk.vtkPolyData()
            pd.SetPoints(pts); pd.SetLines(lines)
            m = vtk.vtkPolyDataMapper(); m.SetInputData(pd)
            a = vtk.vtkActor(); a.SetMapper(m)
            a.GetProperty().SetColor(*color)
            a.GetProperty().SetLineWidth(self.line_width)
            self.display.renderer.AddActor(a)
            # ملصق نصف القطر
            self._label3d_vtk(f"R ≈ {r:.1f} mm", p2)
            self._render()
            return
        if not _HAS_OCC:
            return
        edge = BRepBuilderAPI_MakeEdge(
            GC_MakeArcOfCircle(gp_Pnt(*p1), gp_Pnt(*p2), gp_Pnt(*p3)).Value()
        ).Edge()
        self._show_occ(edge, color)

    # ------------------------- هندسة مساعدة -------------------------
    @staticmethod
    def _circle_center_from_3pts(p1: Point3D, p2: Point3D, p3: Point3D) -> Optional[Point3D]:
        (x1, y1, _), (x2, y2, _), (x3, y3, _) = p1, p2, p3
        a = 2 * (x1*(y2-y3) + x2*(y3-y1) + x3*(y1-y2))
        if abs(a) < 1e-9: return None
        x1s, x2s, x3s = x1*x1 + y1*y1, x2*x2 + y2*y2, x3*x3 + y3*y3
        cx = (x1s*(y2-y3) + x2s*(y3-y1) + x3s*(y1-y2)) / a
        cy = (x1*(x2s-x3s) + x2*(x3s-x1s) + x3*(x1s-x2s)) / a
        return (cx, cy, 0.0)

    # ---------------------- نظام النقرات التفاعلي ----------------------
    def handle_click(self, world: Point3D, tool: str):
        """واجهة موحّدة تستدعي دوال النقر لكل أداة"""
        if tool == "line":
            self.add_line_point(world)
        elif tool == "circle":
            self.add_circle_point(world)
        elif tool == "rect":
            self.add_rect_point(world)
        elif tool == "arc":
            self.add_arc_point(world)

    # كل أداة تتعامل مع النقرات:
    def add_line_point(self, pt: Point3D):
        self.temp_points.append(pt)
        if len(self.temp_points) == 2:
            p1, p2 = self.temp_points
            self.line(p1, p2)
            self.temp_points.clear()

    def add_circle_point(self, pt: Point3D):
        self.temp_points.append(pt)
        if len(self.temp_points) == 2:
            c = self.temp_points[0]
            r = math.hypot(pt[0]-c[0], pt[1]-c[1])
            self.circle(c, r)
            self.temp_points.clear()

    def add_rect_point(self, pt: Point3D):
        self.temp_points.append(pt)
        if len(self.temp_points) == 2:
            p1, p2 = self.temp_points
            w = p2[0] - p1[0]
            h = p2[1] - p1[1]
            self.rectangle(p1, w, h)
            self.temp_points.clear()

    def add_arc_point(self, pt: Point3D):
        self.temp_points.append(pt)
        if len(self.temp_points) == 3:
            p1, p2, p3 = self.temp_points
            self.arc_3pt(p1, p2, p3)
            self.temp_points.clear()

    # ---------------------- وصل أدوات التعديل ----------------------
    # يمكن استدعاء هذه الدوال من interactor/toolbar عبر viewer.modify_ops
    def trim_at(self, click_world: Point3D):
        self.modify_ops.trim(click_world)

    def offset_last(self, distance: float = 10.0):
        """إزاحة آخر عنصر (VTK فقط حالياً)"""
        if self.viewer_type != "VTK":
            _debug("Offset: وضع OCC غير مدعوم بعد.")
            return
        actors = self.display.renderer.GetActors()
        actors.InitTraversal()
        last_actor = None
        a = actors.GetNextActor()
        while a:
            last_actor = a
            a = actors.GetNextActor()
        if last_actor:
            self.modify_ops.offset(last_actor, distance)

    def mirror_last(self, axis: str = "Y"):
        if self.viewer_type != "VTK":
            _debug("Mirror: وضع OCC غير مدعوم بعد.")
            return
        actors = self.display.renderer.GetActors()
        actors.InitTraversal()
        last_actor = None
        a = actors.GetNextActor()
        while a:
            last_actor = a
            a = actors.GetNextActor()
        if last_actor:
            self.modify_ops.mirror(last_actor, axis)

    def fillet_two_points(self, p1: Point3D, p2: Point3D, radius: float = 5.0):
        self.modify_ops.fillet(p1, p2, radius)
