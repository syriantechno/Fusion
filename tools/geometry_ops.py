# -*- coding: utf-8 -*-
"""
🔧 geometry_ops.py
-----------------
عمليات هندسية عامة (Extrude, Cut, Hole ...)

العارض لا ينفذ أي منطق هندسي — فقط يعرض النتيجة.
"""

from OCC.Core.gp import gp_Vec
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCC.Core.BRepCheck import BRepCheck_Analyzer
from OCC.Core.TopoDS import TopoDS_Shape

from profile.dxf_normalizer import load_dxf_segments, build_face_from_segments


# -------------------------------------------------------------------------
# 🧱 دالة الإكسترود الأساسية (من شكل جاهز)
# -------------------------------------------------------------------------
def extrude_face(face: TopoDS_Shape, depth: float, axis: str = "Y") -> TopoDS_Shape | None:
    """ينفذ عملية الإكسترود على وجه هندسي موجود."""
    try:
        if not face or face.IsNull():
            print("⚠️ [geometry_ops] الوجه غير صالح.")
            return None

        # تحقق هندسي قبل الإكسترود
        analyzer = BRepCheck_Analyzer(face)
        if not analyzer.IsValid():
            print("⚠️ [geometry_ops] الوجه يحتوي أخطاء هندسية، سيتم الإيقاف.")
            return None

        # اتجاه الإكسترود
        vec = {
            "X": gp_Vec(depth, 0, 0),
            "Y": gp_Vec(0, depth, 0),
            "Z": gp_Vec(0, 0, depth),
        }.get(axis.upper(), gp_Vec(0, depth, 0))

        # تنفيذ الإكسترود
        prism = BRepPrimAPI_MakePrism(face, vec).Shape()
        print(f"🟢 [geometry_ops] تم تنفيذ الإكسترود على المحور {axis.upper()} بعمق {depth} مم.")
        return prism

    except Exception as e:
        print(f"❌ [geometry_ops] فشل أثناء الإكسترود: {e}")
        return None


# -------------------------------------------------------------------------
# 📂 دالة إكسترود من ملف DXF مباشرة
# -------------------------------------------------------------------------
def extrude_from_dxf(file_path: str, depth: float, axis: str = "Y") -> TopoDS_Shape | None:
    """
    يقوم بتحميل ملف DXF، بناء وجه مغلق منه، ثم تنفيذ الإكسترود وإرجاع الشكل الناتج.
    """
    try:
        print(f"📂 [geometry_ops] تحميل DXF من: {file_path}")

        # تحميل المقاطع من ملف DXF
        segs, bbox = load_dxf_segments(file_path)
        if not segs:
            print("⚠️ [geometry_ops] ملف DXF فارغ أو غير مدعوم.")
            return None

        # بناء وجه هندسي من المقاطع
        face = build_face_from_segments(segs)
        if not face or face.IsNull():
            print("⚠️ [geometry_ops] لم يتم إنشاء وجه هندسي صالح من DXF.")
            return None

        # استدعاء دالة الإكسترود
        solid = extrude_face(face, depth, axis)
        if solid and not solid.IsNull():
            print("🧱 [geometry_ops] تم إنشاء الشكل النهائي بنجاح من DXF.")
            return solid
        else:
            print("⚠️ [geometry_ops] فشل إنشاء الشكل النهائي من DXF.")
            return None

    except Exception as e:
        print(f"❌ [geometry_ops] خطأ أثناء الإكسترود من DXF: {e}")
        return None
