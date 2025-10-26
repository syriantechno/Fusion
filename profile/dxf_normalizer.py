# -*- coding: utf-8 -*-
"""
DXF normalizer (hybrid)
- يحاول أولاً استخدام OCC/VTK (الدقّة الأعلى) لتفكيك جميع الكيانات إلى Edges ثم sampling -> segments
- عند عدم توفر OCC/VTK، يستخدم ezdxf فقط مع تقسيم أقواس/دوائر/سبلاين إلى segments ناعمة
- يُعيد: (segments, bbox)
    segments: List[((x1,y1), (x2,y2))]
    bbox: (xmin, ymin, xmax, ymax)
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Tuple
import math

# ----------------------------
# محاولة استيراد OCC/VTK (اختيارية)
# ----------------------------
_HAS_OCC = True
try:
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
    from OCC.Core.BRep import BRep_Builder, BRep_Tool
    from OCC.Core.TopoDS import TopoDS_Compound
    from OCC.Core.TopExp import TopExp_Explorer
    from OCC.Core.TopAbs import TopAbs_EDGE
    from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Ax2, gp_Circ
    from OCC.Core.GeomAPI import GeomAPI_PointsToBSpline
    from OCC.Core.TColgp import TColgp_Array1OfPnt
except Exception:
    _HAS_OCC = False

try:
    import ezdxf
except Exception as e:
    raise RuntimeError("ezdxf مطلوب: pip install ezdxf>=1.0.3") from e


Point = Tuple[float, float]
Segment = Tuple[Point, Point]


# ==============================================================
#                    Fallback: ezdxf فقط
# ==============================================================
def _segments_by_ezdxf(path: Path) -> Tuple[List[Segment], Tuple[float,float,float,float]]:
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()

    segs: List[Segment] = []
    xmin = ymin = float("inf")
    xmax = ymax = float("-inf")

    def add_seg(x1, y1, x2, y2):
        nonlocal xmin, ymin, xmax, ymax
        segs.append(((float(x1), float(y1)), (float(x2), float(y2))))
        xmin = min(xmin, x1, x2)
        ymin = min(ymin, y1, y2)
        xmax = max(xmax, x1, x2)
        ymax = max(ymax, y1, y2)

    # --- LINE
    for e in msp.query("LINE"):
        s, t = e.dxf.start, e.dxf.end
        add_seg(s[0], s[1], t[0], t[1])

    # --- LWPOLYLINE (مع bulge)
    for poly in msp.query("LWPOLYLINE"):
        pts = poly.get_points("xyb")  # (x,y,bulge)
        n = len(pts)
        if n < 2:
            continue
        closed = poly.closed
        for i in range(n if closed else n - 1):
            x1, y1, bulge = pts[i]
            x2, y2, _ = pts[(i + 1) % n]
            if abs(bulge) < 1e-9:
                add_seg(x1, y1, x2, y2)
            else:
                # تحويل bulge إلى قوس
                ang = 4.0 * math.atan(bulge)  # الزاوية الممركزة
                # اتجاه الحبل
                dx, dy = (x2 - x1), (y2 - y1)
                chord = math.hypot(dx, dy)
                if chord < 1e-12:
                    continue
                # نصف قطر القوس
                radius = chord / (2.0 * math.sin(ang / 2.0))
                # مركز القوس
                # زاوية اتجاه الحبل:
                theta = math.atan2(dy, dx)
                # المسافة من منتصف الحبل لمركز القوس:
                sagitta_dir = theta + (math.pi/2.0 - ang/2.0)
                mx, my = (x1 + x2) * 0.5, (y1 + y2) * 0.5
                cx = mx - radius * math.sin(theta) * (1 if bulge > 0 else -1)
                cy = my + radius * math.cos(theta) * (1 if bulge > 0 else -1)

                # زوايا البداية والنهاية بالنسبة للمركز
                a_start = math.atan2(y1 - cy, x1 - cx)
                # الانحراف a_start->a_start+ang
                steps = max(16, int(abs(ang) / (math.pi/36)))  # ~5° خطوة
                for j in range(steps):
                    t1 = a_start + ang * (j / steps)
                    t2 = a_start + ang * ((j + 1) / steps)
                    add_seg(cx + radius * math.cos(t1), cy + radius * math.sin(t1),
                            cx + radius * math.cos(t2), cy + radius * math.sin(t2))

    # --- CIRCLE
    for circ in msp.query("CIRCLE"):
        cx, cy = circ.dxf.center.x, circ.dxf.center.y
        r = circ.dxf.radius
        steps = max(48, int(2 * math.pi * r / 2.0))  # خطوة ~2 وحدات
        steps = min(256, steps)
        for i in range(steps):
            a1 = 2 * math.pi * i / steps
            a2 = 2 * math.pi * (i + 1) / steps
            add_seg(cx + r * math.cos(a1), cy + r * math.sin(a1),
                    cx + r * math.cos(a2), cy + r * math.sin(a2))

    # --- ARC
    for arc in msp.query("ARC"):
        cx, cy = arc.dxf.center.x, arc.dxf.center.y
        r = arc.dxf.radius
        a0 = math.radians(arc.dxf.start_angle)
        a1 = math.radians(arc.dxf.end_angle)
        span = a1 - a0
        # ط normalise
        if span == 0:
            span = 2 * math.pi
        steps = max(24, int(abs(span) / (math.pi/36)))  # ~5°
        for i in range(steps):
            t1 = a0 + span * (i / steps)
            t2 = a0 + span * ((i + 1) / steps)
            add_seg(cx + r * math.cos(t1), cy + r * math.sin(t1),
                    cx + r * math.cos(t2), cy + r * math.sin(t2))

    # --- SPLINE (fit_points)
    for sp in msp.query("SPLINE"):
        fit = list(sp.fit_points)
        if len(fit) >= 2:
            # تقسيم ناعم بين نقاط الملائمة
            steps = max(32, len(fit) * 8)
            # تقريب بخطوط بين النقاط المتتالية
            for i in range(len(fit) - 1):
                x1, y1 = fit[i][0], fit[i][1]
                x2, y2 = fit[i+1][0], fit[i+1][1]
                add_seg(x1, y1, x2, y2)

    if not segs:
        raise RuntimeError("لم يتم العثور على هندسة صالحة في DXF (ezdxf).")

    return segs, (xmin, ymin, xmax, ymax)


# ==============================================================
#                OCC/VTK -> Segments (إذا متوفر)
# ==============================================================
def _segments_by_occ(path: Path) -> Tuple[List[Segment], Tuple[float,float,float,float]]:
    if not _HAS_OCC:
        raise RuntimeError("OCC غير متوفر، سيُستخدم مسار ezdxf فقط.")

    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()

    edges = []

    # LINE
    for line in msp.query("LINE"):
        s, e = line.dxf.start, line.dxf.end
        edges.append(BRepBuilderAPI_MakeEdge(gp_Pnt(s[0], s[1], 0), gp_Pnt(e[0], e[1], 0)).Edge())

    # LWPOLYLINE (نحوّل كل مقطع لخط، ونترك الأقواس كخطوات صغيرة ezdxf سبق عالجناها أفضل؛
    # هنا نضيف فقط الخطوط المباشرة)
    for poly in msp.query("LWPOLYLINE"):
        pts = poly.get_points("xyb")
        n = len(pts)
        if n < 2:
            continue
        closed = poly.closed
        for i in range(n if closed else n - 1):
            x1, y1, b = pts[i]
            x2, y2, _ = pts[(i + 1) % n]
            if abs(b) < 1e-9:
                edges.append(BRepBuilderAPI_MakeEdge(gp_Pnt(x1, y1, 0), gp_Pnt(x2, y2, 0)).Edge())
    # CIRCLE
    for circ in msp.query("CIRCLE"):
        c = circ.dxf.center
        r = circ.dxf.radius
        ax2 = gp_Ax2(gp_Pnt(c[0], c[1], 0), gp_Dir(0, 0, 1))
        circle = gp_Circ(ax2, r)
        edges.append(BRepBuilderAPI_MakeEdge(circle).Edge())

    # ARC
    for arc in msp.query("ARC"):
        c = arc.dxf.center
        r = arc.dxf.radius
        a0 = math.radians(arc.dxf.start_angle)
        a1 = math.radians(arc.dxf.end_angle)
        ax2 = gp_Ax2(gp_Pnt(c[0], c[1], 0), gp_Dir(0, 0, 1))
        circle = gp_Circ(ax2, r)
        edges.append(BRepBuilderAPI_MakeEdge(circle, a0, a1).Edge())

    # SPLINE
    for spline in msp.query("SPLINE"):
        fit = spline.fit_points
        n = len(fit)
        if n >= 2:
            arr = TColgp_Array1OfPnt(1, n)
            for i, pt in enumerate(fit, start=1):
                arr.SetValue(i, gp_Pnt(pt[0], pt[1], 0))
            bspline = GeomAPI_PointsToBSpline(arr).Curve()
            edges.append(BRepBuilderAPI_MakeEdge(bspline).Edge())

    if not edges:
        # لو الملف كله arcs داخل LWPOLYLINE ب bulge، الأفضل نرجع لمسار ezdxf
        return _segments_by_ezdxf(path)

    # Compound
    builder = BRep_Builder()
    comp = TopoDS_Compound()
    builder.MakeCompound(comp)
    for e in edges:
        builder.Add(comp, e)

    # Sampling لكل edge -> segments
    segs: List[Segment] = []
    xmin = ymin = float("inf")
    xmax = ymax = float("-inf")

    exp = TopExp_Explorer(comp, TopAbs_EDGE)
    while exp.More():
        edge = exp.Current()
        curve, first, last = BRep_Tool.Curve(edge)
        if curve is not None:
            # عدد العينات مناسب (تكيفي)
            samples = 40
            prev = None
            for i in range(samples + 1):
                u = first + (last - first) * (i / samples)
                pnt = curve.Value(u)
                x, y = float(pnt.X()), float(pnt.Y())
                if prev is not None:
                    x0, y0 = prev
                    segs.append(((x0, y0), (x, y)))
                    xmin = min(xmin, x0, x)
                    ymin = min(ymin, y0, y)
                    xmax = max(xmax, x0, x)
                    ymax = max(ymax, y0, y)
                prev = (x, y)
        exp.Next()

    if not segs:
        # fallback أخير
        return _segments_by_ezdxf(path)

    return segs, (xmin, ymin, xmax, ymax)


# ==============================================================
#                    الواجهة العامة
# ==============================================================
def load_dxf_segments(path: Path) -> Tuple[List[Segment], Tuple[float,float,float,float]]:
    """واجهة واحدة للمشروع: تُعيد segments + bbox بدقّة عالية، مع fallback تلقائي."""
    try:
        if _HAS_OCC:
            return _segments_by_occ(path)
        else:
            return _segments_by_ezdxf(path)
    except Exception as e:
        # كحل أخير جرّب ezdxf فقط
        try:
            return _segments_by_ezdxf(path)
        except Exception as e2:
            raise RuntimeError(f"فشل تفكيك DXF: {e}\nFallback error: {e2}")
