# -*- coding: utf-8 -*-
"""
AlumProCNC — Sketch Operations (Final Advanced Edition)
Author: AlumProCNC Team

وحدة شاملة لكل أدوات Sketch (أساسية + متقدّمة) باستخدام pythonOCC-core.
مصممة للعمل مع display/context (AIS) وتطبع Debug للمساعدة أثناء التطوير.
"""

from typing import List, Tuple, Optional, Union

# ===== OpenCASCADE / pythonOCC =====
from OCC.Core.gp import (
    gp_Pnt, gp_Vec, gp_Dir, gp_Ax2, gp_Trsf, gp_Ax1
)
from OCC.Core.GC import (
    GC_MakeLine, GC_MakeCircle, GC_MakeArcOfCircle, GC_MakeEllipse
)
from OCC.Core.GeomAPI import GeomAPI_PointsToBSpline
from OCC.Core.Geom import Geom_Plane
from OCC.Core.AIS import (
    AIS_Shape, AIS_Point, AIS_Axis, AIS_LengthDimension, AIS_AngleDimension
)
from OCC.Core.Quantity import Quantity_Color, Quantity_NOC_BLACK, Quantity_TOC_RGB
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_Transform
)
from OCC.Core.BRepPrimAPI import (
    BRepPrimAPI_MakePrism,
    BRepPrimAPI_MakeRevol
)
from OCC.Core.BRepOffsetAPI import (
    BRepOffsetAPI_MakePipe,
    BRepOffsetAPI_MakeOffset
)
from OCC.Core.BRepFilletAPI import (
    BRepFilletAPI_MakeFillet2d,
    BRepFilletAPI_MakeChamfer
)
from OCC.Core.BRepAlgoAPI import (
    BRepAlgoAPI_Fuse,
    BRepAlgoAPI_Cut
)
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopoDS import TopoDS_Shape, TopoDS_Edge, TopoDS_Wire, TopoDS_Face
from OCC.Core.TopAbs import TopAbs_EDGE, TopAbs_WIRE, TopAbs_FACE
from OCC.Core.GC import GC_MakeArcOfCircle
from OCC.Core.BOPAlgo import BOPAlgo_Splitter
from OCC.Core.TopTools import TopTools_ListOfShape
from OCC.Core.BRep import BRep_Tool

# ===== Helpers =====
ColorTuple = Tuple[float, float, float]   # RGB normalized (0..1)
Point3D = Tuple[float, float, float]


def _qcolor(rgb: ColorTuple) -> Quantity_Color:
    r, g, b = rgb
    return Quantity_Color(r, g, b, Quantity_TOC_RGB)


def _debug(msg: str):
    print(f"[SKETCH] {msg}")


# ============================================================
#  Core class: SketchOps
# ============================================================
class SketchOps:
    """
    محرّك أوامر السكيتش. استخدمه عبر إنشاء كائن وتمريرة display (عارضك).
    أمثلة:
        ops = SketchOps(display, default_color=(0.15, 0.25, 0.45))
        edge = ops.line((0,0,0), (50,0,0))
        circ = ops.circle((0,0,0), 25)
    """
    def __init__(self, display, default_color: ColorTuple = (0.15, 0.25, 0.45), line_width: float = 1.5):
        self.display = display
        self.ctx = display.GetContext()
        self.default_color = default_color
        self.line_width = line_width
        _debug(f"Initialized (color={self.default_color}, width={self.line_width})")

    # ----------------- Styling -----------------
    def set_color(self, rgb: ColorTuple):
        self.default_color = rgb
        _debug(f"Default color -> {rgb}")

    def set_line_width(self, width: float):
        self.line_width = max(1.0, float(width))
        _debug(f"Line width -> {self.line_width}")

    # ----------------- Display helpers -----------------
    def _show(self, shape: TopoDS_Shape, color: Optional[ColorTuple] = None, update: bool = True) -> AIS_Shape:
        ais = self.display.DisplayShape(shape, update=update)
        if color is None:
            color = self.default_color
        self.ctx.SetColor(ais, _qcolor(color))
        try:
            self.ctx.SetWidth(ais, self.line_width)
        except Exception:
            pass
        return ais

    # ====================================================
    #  Drawing primitives (2D on Z=0 by default)
    # ====================================================
    def point(self, p: Point3D, color: Optional[ColorTuple] = None) -> AIS_Point:
        _debug(f"Point {p}")
        ais = AIS_Point(gp_Pnt(*p))
        self.ctx.Display(ais, True)
        if color:
            self.ctx.SetColor(ais, _qcolor(color))
        return ais

    def axis(self, origin: Point3D, direction: Tuple[float, float, float] = (1, 0, 0)) -> AIS_Axis:
        _debug(f"Axis origin={origin}, dir={direction}")
        ax = AIS_Axis(gp_Ax1(gp_Pnt(*origin), gp_Dir(*direction)))
        self.ctx.Display(ax, True)
        return ax

    def line(self, p1: Point3D, p2: Point3D, color: Optional[ColorTuple] = None) -> TopoDS_Edge:
        _debug(f"Line {p1} → {p2}")
        line = GC_MakeLine(gp_Pnt(*p1), gp_Pnt(*p2)).Value()
        edge = BRepBuilderAPI_MakeEdge(line).Edge()
        self._show(edge, color)
        return edge

    def circle(self, center: Point3D, radius: float, color: Optional[ColorTuple] = None) -> TopoDS_Edge:
        _debug(f"Circle center={center}, r={radius}")
        circ = GC_MakeCircle(gp_Pnt(*center), float(radius)).Value()
        edge = BRepBuilderAPI_MakeEdge(circ).Edge()
        self._show(edge, color)
        return edge

    def arc_3pt(self, p1: Point3D, p2: Point3D, p3: Point3D, color: Optional[ColorTuple] = None) -> TopoDS_Edge:
        _debug(f"Arc3pt {p1}, {p2}, {p3}")
        arc = GC_MakeArcOfCircle(gp_Pnt(*p1), gp_Pnt(*p2), gp_Pnt(*p3)).Value()
        edge = BRepBuilderAPI_MakeEdge(arc).Edge()
        self._show(edge, color)
        return edge

    def rectangle(self, origin: Point3D, width: float, height: float, color: Optional[ColorTuple] = None) -> TopoDS_Wire:
        _debug(f"Rect origin={origin}, w={width}, h={height}")
        x, y, z = origin
        pts = [
            gp_Pnt(x, y, z),
            gp_Pnt(x + width, y, z),
            gp_Pnt(x + width, y + height, z),
            gp_Pnt(x, y + height, z),
            gp_Pnt(x, y, z),
        ]
        wmk = BRepBuilderAPI_MakeWire()
        for i in range(4):
            wmk.Add(BRepBuilderAPI_MakeEdge(pts[i], pts[i + 1]).Edge())
        wire = wmk.Wire()
        self._show(wire, color)
        return wire

    def ellipse(self, center: Point3D, major: float, minor: float, angle_deg: float = 0.0, color: Optional[ColorTuple] = None) -> TopoDS_Edge:
        _debug(f"Ellipse center={center}, a={major}, b={minor}, ang={angle_deg}")
        ax2 = gp_Ax2(gp_Pnt(*center), gp_Dir(0, 0, 1))
        if abs(angle_deg) > 1e-6:
            # تدوير نظام المحاور لو لزم
            tr = gp_Trsf()
            tr.SetRotation(gp_Ax1(gp_Pnt(*center), gp_Dir(0, 0, 1)), angle_deg * 3.1415926535 / 180.0)
            ax2.Transform(tr)
        ell = GC_MakeEllipse(ax2, float(major), float(minor)).Value()
        edge = BRepBuilderAPI_MakeEdge(ell).Edge()
        self._show(edge, color)
        return edge

    def polyline(self, points: List[Point3D], closed: bool = False, color: Optional[ColorTuple] = None) -> TopoDS_Wire:
        _debug(f"Polyline n={len(points)}, closed={closed}")
        if len(points) < 2:
            raise ValueError("Polyline needs >= 2 points")
        wmk = BRepBuilderAPI_MakeWire()
        for i in range(len(points) - 1):
            wmk.Add(BRepBuilderAPI_MakeEdge(gp_Pnt(*points[i]), gp_Pnt(*points[i + 1])).Edge())
        if closed:
            wmk.Add(BRepBuilderAPI_MakeEdge(gp_Pnt(*points[-1]), gp_Pnt(*points[0])).Edge())
        wire = wmk.Wire()
        self._show(wire, color)
        return wire

    def polygon(self, points: List[Point3D], color: Optional[ColorTuple] = None) -> TopoDS_Wire:
        return self.polyline(points, closed=True, color=color)

    def spline(self, points: List[Point3D], color: Optional[ColorTuple] = None) -> TopoDS_Edge:
        _debug(f"Spline n={len(points)}")
        if len(points) < 2:
            raise ValueError("Spline needs >= 2 points")
        gp_pts = [gp_Pnt(*p) for p in points]
        curve = GeomAPI_PointsToBSpline(gp_pts).Curve()
        edge = BRepBuilderAPI_MakeEdge(curve).Edge()
        self._show(edge, color)
        return edge

    # ====================================================
    #  Modify / Advanced 2D ops
    # ====================================================
    def _ensure_face_from_wire(self, wire: TopoDS_Wire) -> TopoDS_Face:
        """إنشاء وجه مسطّح من Wire (مطلوب لبعض أوامر 2D مثل Fillet2D/Chamfer2D)."""
        face = BRepBuilderAPI_MakeFace(wire).Face()
        return face

    def offset(self, shape: TopoDS_Shape, distance: float, color: Optional[ColorTuple] = (0.6, 0.6, 0.15)) -> TopoDS_Shape:
        _debug(f"Offset dist={distance}")
        off = BRepOffsetAPI_MakeOffset(shape)
        off.Perform(float(distance))
        new_shape = off.Shape()
        self._show(new_shape, color)
        return new_shape

    def fillet2d(self, wire: TopoDS_Wire, radius: float, color: Optional[ColorTuple] = (0.9, 0.45, 0.2)) -> TopoDS_Wire:
        _debug(f"Fillet2D R={radius}")
        face = self._ensure_face_from_wire(wire)
        mk = BRepFilletAPI_MakeFillet2d(face)
        # أضف كل الحواف للفلّت
        exp = TopExp_Explorer(wire, TopAbs_EDGE)
        while exp.More():
            edge = TopoDS_Edge(exp.Current())
            try:
                mk.AddFillet(edge, float(radius))
            except Exception:
                pass
            exp.Next()
        mk.Build()
        res_face = mk.Shape()
        # محاولة استخراج Wire الناتج من الوجه
        out_wires = []
        expw = TopExp_Explorer(res_face, TopAbs_WIRE)
        while expw.More():
            out_wires.append(TopoDS_Wire(expw.Current()))
            expw.Next()
        result = out_wires[0] if out_wires else wire
        self._show(result, color)
        return result

    def chamfer2d(self, wire: TopoDS_Wire, d1: float, d2: Optional[float] = None,
                  color: Optional[ColorTuple] = (0.9, 0.4, 0.2)) -> TopoDS_Wire:
        _debug(f"Chamfer2D d1={d1}, d2={d2 or d1}")
        face = self._ensure_face_from_wire(wire)
        mk = BRepFilletAPI_MakeFillet2d(face)
        d2 = d2 if d2 is not None else d1
        # شيمفر كل الحواف
        exp = TopExp_Explorer(wire, TopAbs_EDGE)
        while exp.More():
            edge = TopoDS_Edge(exp.Current())
            try:
                mk.AddChamfer(edge, float(d1), float(d2))
            except Exception:
                pass
            exp.Next()
        mk.Build()
        res_face = mk.Shape()
        out_wires = []
        expw = TopExp_Explorer(res_face, TopAbs_WIRE)
        while expw.More():
            out_wires.append(TopoDS_Wire(expw.Current()))
            expw.Next()
        result = out_wires[0] if out_wires else wire
        self._show(result, color)
        return result

    # ----------------- Booleans -----------------
    def fuse(self, a: TopoDS_Shape, b: TopoDS_Shape, color: Optional[ColorTuple] = (0.3, 0.7, 0.3)) -> TopoDS_Shape:
        _debug("Fuse")
        res = BRepAlgoAPI_Fuse(a, b).Shape()
        self._show(res, color)
        return res

    def cut(self, a: TopoDS_Shape, b: TopoDS_Shape, color: Optional[ColorTuple] = (0.7, 0.3, 0.3)) -> TopoDS_Shape:
        _debug("Cut")
        res = BRepAlgoAPI_Cut(a, b).Shape()
        self._show(res, color)
        return res

    # ----------------- Transformations -----------------
    def mirror(self, shape: TopoDS_Shape, axis: Tuple[float, float, float] = (1, 0, 0)) -> TopoDS_Shape:
        _debug(f"Mirror axis={axis}")
        tr = gp_Trsf()
        if axis == (1, 0, 0):
            tr.SetMirror(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0)))
        elif axis == (0, 1, 0):
            tr.SetMirror(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0)))
        else:
            tr.SetMirror(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)))
        out = BRepBuilderAPI_Transform(shape, tr, True).Shape()
        self._show(out)
        return out

    def translate(self, shape: TopoDS_Shape, vec: Tuple[float, float, float]) -> TopoDS_Shape:
        _debug(f"Translate {vec}")
        tr = gp_Trsf()
        tr.SetTranslation(gp_Vec(*vec))
        out = BRepBuilderAPI_Transform(shape, tr, True).Shape()
        self._show(out)
        return out

    def rotate_z(self, shape: TopoDS_Shape, angle_deg: float, center: Point3D = (0, 0, 0)) -> TopoDS_Shape:
        _debug(f"Rotate Z {angle_deg}° around {center}")
        tr = gp_Trsf()
        tr.SetRotation(gp_Ax1(gp_Pnt(*center), gp_Dir(0, 0, 1)), angle_deg * 3.1415926535 / 180.0)
        out = BRepBuilderAPI_Transform(shape, tr, True).Shape()
        self._show(out)
        return out

    def scale(self, shape: TopoDS_Shape, factor: float, center: Point3D = (0, 0, 0)) -> TopoDS_Shape:
        _debug(f"Scale {factor} around {center}")
        tr = gp_Trsf()
        tr.SetScale(gp_Pnt(*center), float(factor))
        out = BRepBuilderAPI_Transform(shape, tr, True).Shape()
        self._show(out)
        return out

    # ====================================================
    #  Dimensions (AIS)
    # ====================================================
    def dim_length(self, p1: Point3D, p2: Point3D, offset_dir: Tuple[float, float, float] = (0, 0, 1),
                   color: ColorTuple = (0.2, 0.2, 0.2)) -> AIS_LengthDimension:
        """إضافة قياس طول (LINEAR) بين نقطتين مع إزاحة عرضية بسيطة."""
        _debug(f"Dim Length {p1}–{p2}")
        dim = AIS_LengthDimension(gp_Pnt(*p1), gp_Pnt(*p2), gp_Dir(*offset_dir))
        self.ctx.Display(dim, True)
        self.ctx.SetColor(dim, _qcolor(color))
        return dim

    def dim_angle(self, p1: Point3D, vertex: Point3D, p2: Point3D,
                  color: ColorTuple = (0.2, 0.2, 0.2)) -> AIS_AngleDimension:
        """إضافة قياس زاوية بين خطين (vertex نقطة التقاء)."""
        _debug(f"Dim Angle ({p1}) ∠ ({vertex}) ∠ ({p2})")
        dim = AIS_AngleDimension(gp_Pnt(*vertex), gp_Pnt(*p1), gp_Pnt(*p2))
        self.ctx.Display(dim, True)
        self.ctx.SetColor(dim, _qcolor(color))
        return dim

    # ====================================================
    #  Utilities (show/hide/delete)
    # ====================================================
    def erase(self, ais_or_shape: Union[AIS_Shape, TopoDS_Shape], update: bool = True):
        _debug("Erase")
        try:
            self.ctx.Erase(ais_or_shape, update)
        except Exception:
            # إذا كان TopoDS_Shape وليس AIS
            self.ctx.Remove(ais_or_shape, update)

    def hide_all(self):
        _debug("Hide all")
        self.ctx.EraseAll(False)
        self.display.Repaint()

    def show(self, shape: TopoDS_Shape):
        _debug("Show shape")
        self._show(shape, update=True)

    # ====================================================
    #  3D (اختياري لاحقًا): Extrude / Revolve / Pipe
    # ====================================================
    def extrude(self, wire_or_face: TopoDS_Shape, vec: Tuple[float, float, float]) -> TopoDS_Shape:
        _debug(f"Extrude vec={vec}")
        prism = BRepPrimAPI_MakePrism(wire_or_face, gp_Vec(*vec)).Shape()
        self._show(prism)
        return prism

    def revolve(self, wire_or_face: TopoDS_Shape, axis_point: Point3D, axis_dir: Tuple[float, float, float],
                angle_deg: float = 360.0) -> TopoDS_Shape:
        _debug(f"Revolve angle={angle_deg}")
        ax = gp_Ax1(gp_Pnt(*axis_point), gp_Dir(*axis_dir))
        rev = BRepPrimAPI_MakeRevol(wire_or_face, ax, angle_deg * 3.1415926535 / 180.0).Shape()
        self._show(rev)
        return rev

    def sweep_pipe(self, profile: TopoDS_Shape, path_wire: TopoDS_Wire) -> TopoDS_Shape:
        _debug("Sweep/Pipe")
        pipe = BRepOffsetAPI_MakePipe(path_wire, profile).Shape()
        self._show(pipe)
        return pipe
