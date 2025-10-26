# frontend/profile/thumbnailer.py
# -*- coding: utf-8 -*-
"""
🎨 توليد معاينات DXF (thumbnails) باستخدام QPainter
- يرسم الخطوط بدقة عالية وبألوان هادئة مشابهة لـ Fusion.
- يقوم بتصحيح اتجاه X/Y لتطابق العرض الحقيقي في برامج CAD.
- يحفظ الصورة ضمن مجلد data/thumbnails.
"""

from __future__ import annotations
from typing import List, Tuple
from pathlib import Path
from PySide6.QtGui import QImage, QPainter, QPen, QColor
from PySide6.QtCore import Qt

Point = Tuple[float, float]
Segment = Tuple[Point, Point]

# 📂 مجلد حفظ المصغرات
THUMBS_DIR = Path("data/thumbnails")
THUMBS_DIR.mkdir(parents=True, exist_ok=True)


def draw_segments_thumbnail(segs: List[Segment], bbox, out_name: str, size: int = 280) -> str:
    """يرسم معاينة 2D من مقاطع DXF ويحفظها كـ PNG."""
    x1, y1, x2, y2 = bbox
    w = max(1e-9, x2 - x1)
    h = max(1e-9, y2 - y1)
    scale = 0.85 * size / max(w, h)
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0

    # 🧱 إنشاء الصورة الخلفية
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(QColor("#F1F2F1"))  # خلفية موحدة لباقي البرنامج

    p = QPainter(img)
    p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)

    # ✏️ إعداد القلم (ألوان Fusion-style)
    pen = QPen(QColor("#34495E"))  # رمادي أزرق ناعم
    pen.setWidthF(0.9)
    p.setPen(pen)

    # ✨ دالة تحويل النقاط لتصحيح الاتجاه (X و Y)
    from math import cos, sin, radians

    # 👇 زاوية التصحيح (يمكن تعديلها حسب نوع ملفاتك)
    ROT_ANGLE = 90  # جرّب 90 أو -90 حسب الحاجة

    def map_pt(px, py):
        # مركز الشكل
        dx = px - cx
        dy = py - cy

        # تدوير حول المركز (rotation)
        rad = radians(ROT_ANGLE)
        rx = dx * cos(rad) - dy * sin(rad)
        ry = dx * sin(rad) + dy * cos(rad)

        # قلب محور Y لتوحيد الاتجاه (لأن QPainter يرسم للأسفل)
        ry = -ry

        # تحجيم ونقل إلى منتصف الصورة
        X = rx * scale + size / 2
        Y = ry * scale + size / 2
        return X, Y

    # 🖊️ رسم جميع المقاطع
    for (a, b) in segs:
        X1, Y1 = map_pt(a[0], a[1])
        X2, Y2 = map_pt(b[0], b[1])
        p.drawLine(int(X1), int(Y1), int(X2), int(Y2))

    # 🔲 حدود ظل خفيف حول الشكل
    shadow_pen = QPen(QColor(0, 0, 0, 35))
    shadow_pen.setWidthF(2.2)
    p.setPen(shadow_pen)
    for (a, b) in segs:
        X1, Y1 = map_pt(a[0], a[1])
        X2, Y2 = map_pt(b[0], b[1])
        p.drawLine(int(X1), int(Y1), int(X2), int(Y2))

    p.end()

    # 💾 حفظ الناتج
    out_path = THUMBS_DIR / f"{out_name}.png"
    img.save(str(out_path))
    print(f"🖼️ [Thumb] saved {out_path}")
    return str(out_path)
