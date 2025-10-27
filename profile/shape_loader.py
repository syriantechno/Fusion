# -*- coding: utf-8 -*-
"""
Adapter موحّد لتحميل الأشكال من DXF/BREP بدون تعديل الواجهة.
يحترم مخرجات load_dxf_segments الموجودة لديك (سواء أعادت Edges أو Tuples...).
"""

from pathlib import Path
from OCC.Core import BRepTools
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopoDS import TopoDS_Shape, TopoDS_Edge, TopoDS_Wire
from OCC.Core.gp import gp_Pnt
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_MakeFace,
)

from profile.dxf_normalizer import load_dxf_segments


def _wire_from_segments(segments) -> TopoDS_Wire | None:
    """
    يبني Wire من مخرجات load_dxf_segments أياً كانت:
    - TopoDS_Edge: تُضاف مباشرة
    - tuples/list لنقطتين: تُحوّل إلى Edge
    - (يتجاهل الأنواع غير المدعومة بصمت)
    """
    wb = BRepBuilderAPI_MakeWire()
    valid = 0

    for seg in segments:
        # حالة Edge جاهزة
        if isinstance(seg, TopoDS_Edge):
            wb.Add(seg)
            valid += 1
            continue

        # حالة Wire جاهز (لو مكتبتك تعيد Wires أيضاً)
        if isinstance(seg, TopoDS_Wire):
            wb.Add(seg)
            valid += 1
            continue

        # حالة (p1, p2) أو [p1, p2]
        if isinstance(seg, (tuple, list)) and len(seg) == 2:
            p1, p2 = seg
            try:
                e = BRepBuilderAPI_MakeEdge(
                    gp_Pnt(float(p1[0]), float(p1[1]), float(p1[2]) if len(p1) > 2 else 0.0),
                    gp_Pnt(float(p2[0]), float(p2[1]), float(p2[2]) if len(p2) > 2 else 0.0),
                ).Edge()
                wb.Add(e)
                valid += 1
                continue
            except Exception:
                # نتجاهل العنصر غير القابل للتحويل
                pass

        # حالة قائمة نقاط طويلة [p1, p2, p3, ...] نبني منها سلسلة أضلاع
        if isinstance(seg, (tuple, list)) and len(seg) >= 3 and all(isinstance(p, (tuple, list)) for p in seg):
            try:
                for i in range(len(seg) - 1):
                    a, b = seg[i], seg[i + 1]
                    e = BRepBuilderAPI_MakeEdge(
                        gp_Pnt(float(a[0]), float(a[1]), float(a[2]) if len(a) > 2 else 0.0),
                        gp_Pnt(float(b[0]), float(b[1]), float(b[2]) if len(b) > 2 else 0.0),
                    ).Edge()
                    wb.Add(e)
                    valid += 1
                continue
            except Exception:
                pass

        # غير مدعوم — نتجاهله بصمت لتفادي الضجيج في الواجهة

    if valid == 0:
        return None

    w = wb.Wire()
    return None if w.IsNull() else w


def load_profile_shape(file_path: str) -> TopoDS_Shape | None:
    """
    يحمّل TopoDS_Shape من:
      - BREP: مباشرة
      - DXF: عبر load_dxf_segments + تحويل موحّد إلى Wire/Face
    """
    path = Path(file_path)
    if not path.exists():
        return None

    suffix = path.suffix.lower()

    # BREP: تحميل مباشر
    if suffix == ".brep":
        try:
            builder = BRep_Builder()
            shape = TopoDS_Shape()
            BRepTools.breptools_Read(shape, str(path), builder)
            return shape
        except Exception:
            return None

    # DXF: استخدام البايبلاين الحالي لديك، مع Adapter موحّد
    if suffix == ".dxf":
        try:
            segments, bbox = load_dxf_segments(str(path))
            if not segments:
                return None

            wire = _wire_from_segments(segments)
            if not wire:
                return None

            # نحاول بناء Face إن كان مغلقاً، وإلا نعيد Wire
            try:
                face = BRepBuilderAPI_MakeFace(wire).Face()
                return face
            except Exception:
                return wire
        except Exception:
            return None

    # صيغ أخرى غير مدعومة حالياً
    return None
