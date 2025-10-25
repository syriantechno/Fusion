# frontend/profile/dxf_normalizer.py
# -*- coding: utf-8 -*-
"""
مُطَبِّع DXF قوي:
- يحمّل DXF بأي ترميز (حتى Corel الغريبة)، يحاول recover()
- يتجاهل paperspace ويركّز على modelspace
- يفكّ INSERT/BLOCKs إلى entities (explode)
- يحوّل SPLINE/ELLIPSE/ARC إلى polyline نقاط للرسم
- يُرجع قائمة segments [(x1,y1),(x2,y2), ...] مع bounds
"""
from __future__ import annotations
from typing import List, Tuple
from pathlib import Path
import math

try:
    import ezdxf
    from ezdxf.recover import recover
    _HAS_EZDXF = True
except Exception:
    _HAS_EZDXF = False

Point = Tuple[float, float]
Segment = Tuple[Point, Point]

def load_dxf_segments(path: Path, arc_segments: int = 48) -> Tuple[List[Segment], Tuple[float,float,float,float]]:
    if not _HAS_EZDXF:
        raise RuntimeError("ezdxf مطلوب: pip install ezdxf>=1.0.3")

    print(f"📂 [DXF] loading {path}")
    try:
        doc, auditor = recover(str(path))
        if auditor.has_errors:
            print(f"⚠️ [DXF] auditor: {len(auditor.errors)} issues — continuing")
    except Exception as e:
        # ترميزات عنيدة: محاولة فتح عادي
        print(f"⚠️ recover failed: {e}, trying readfile()…")
        doc = ezdxf.readfile(str(path))

    msp = doc.modelspace()
    segs: List[Segment] = []

    def add_line(p1: Point, p2: Point):
        if p1 != p2:
            segs.append((p1, p2))

    # فكّ أي INSERT إلى entities مباشرة
    to_process = list(msp)
    for e in to_process:
        try:
            if e.dxftype() == "INSERT":
                block = doc.blocks[e.dxf.name]
                mat = e.ocs().transform  # تقريبًا، وقد نطبّق move/scale/rotate حسب e.dxf attrs
                base = (e.dxf.insert.x, e.dxf.insert.y)
                for be in block:
                    be = be.copy()  # نسخة مستقلة
                    # تطبيق translate كبداية (تحسين لاحقًا للتحجيم/الدوران)
                    try:
                        if be.dxf.hasattr("start") and be.dxf.hasattr("end"):
                            s, t = be.dxf.start, be.dxf.end
                            add_line((s.x+base[0], s.y+base[1]), (t.x+base[0], t.y+base[1]))
                    except Exception:
                        pass
            elif e.dxftype() in ("LINE", "LWPOLYLINE", "POLYLINE", "CIRCLE", "ARC", "ELLIPSE", "SPLINE"):
                if e.dxftype() == "LINE":
                    s, t = e.dxf.start, e.dxf.end
                    add_line((s.x, s.y), (t.x, t.y))

                elif e.dxftype() in ("LWPOLYLINE", "POLYLINE"):
                    pts = [(p[0], p[1]) for p in e.get_points("xy")]
                    for i in range(len(pts)-1):
                        add_line(pts[i], pts[i+1])
                    if getattr(e, "closed", False):
                        add_line(pts[-1], pts[0])

                elif e.dxftype() == "CIRCLE":
                    cx, cy, r = e.dxf.center.x, e.dxf.center.y, e.dxf.radius
                    prev = None
                    for i in range(arc_segments):
                        ang = 2*math.pi * i/arc_segments
                        p = (cx + r*math.cos(ang), cy + r*math.sin(ang))
                        if prev: add_line(prev, p)
                        prev = p

                elif e.dxftype() == "ARC":
                    cx, cy, r = e.dxf.center.x, e.dxf.center.y, e.dxf.radius
                    a1, a2 = math.radians(e.dxf.start_angle), math.radians(e.dxf.end_angle)
                    # احترم اتجاه القوس
                    steps = arc_segments
                    for i in range(steps):
                        t1 = a1 + (a2 - a1) * (i / steps)
                        t2 = a1 + (a2 - a1) * ((i+1) / steps)
                        p1 = (cx + r*math.cos(t1), cy + r*math.sin(t1))
                        p2 = (cx + r*math.cos(t2), cy + r*math.sin(t2))
                        add_line(p1, p2)

                elif e.dxftype() == "ELLIPSE":
                    cx, cy = e.dxf.center.x, e.dxf.center.y
                    ma = e.dxf.major_axis  # (x,y,0)
                    ratio = e.dxf.minor_axis_ratio
                    # تقريب ellipse إلى polyline
                    steps = arc_segments
                    prev = None
                    for i in range(steps+1):
                        t = 2*math.pi * i/steps
                        x = cx + ma.x*math.cos(t)
                        y = cy + ma.y*ratio*math.sin(t)
                        p = (x, y)
                        if prev: add_line(prev, p)
                        prev = p

                elif e.dxftype() == "SPLINE":
                    # تقريب Spline إلى polyline
                    pts = [tuple(p) for p in e.approximate(arc_segments)]
                    for i in range(len(pts)-1):
                        add_line(pts[i], pts[i+1])
        except Exception as ex:
            print(f"⚠️ entity {e.dxftype()} skipped: {ex}")

    if not segs:
        raise RuntimeError("DXF فارغ أو غير مدعوم — تحقّق من Layout/Entities.")

    xs = [p[0] for seg in segs for p in seg]
    ys = [p[1] for seg in segs for p in seg]
    bbox = (min(xs), min(ys), max(xs), max(ys))
    print(f"✅ [DXF] segments={len(segs)} bbox={bbox}")
    return segs, bbox
