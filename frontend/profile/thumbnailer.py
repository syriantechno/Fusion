# frontend/profile/thumbnailer.py
# -*- coding: utf-8 -*-
"""
يرسم المصغّرات باستخدام QPainter مباشرة:
- يأخذ segments + bbox
- يرسم خطوط رفيعة anti-aliased على خلفية فاتحة
- يحفظ PNG في thumbnails/
"""
from __future__ import annotations
from typing import List, Tuple
from pathlib import Path
from PySide6.QtGui import QImage, QPainter, QPen, QColor
from PySide6.QtCore import Qt

Point = Tuple[float,float]
Segment = Tuple[Point,Point]

THUMBS_DIR = Path("data/thumbnails")
THUMBS_DIR.mkdir(parents=True, exist_ok=True)

def draw_segments_thumbnail(segs: List[Segment], bbox, out_name: str, size: int = 280) -> str:
    x1, y1, x2, y2 = bbox
    w = max(1e-9, x2 - x1); h = max(1e-9, y2 - y1)
    scale = 0.85 * size / max(w, h)
    cx = (x1 + x2) / 2.0; cy = (y1 + y2) / 2.0

    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(QColor("#F1F2F1"))
    p = QPainter(img)
    p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
    pen = QPen(QColor("#2C3E50"))
    pen.setWidthF(1.2)
    p.setPen(pen)

    def map_pt(px, py):
        X = (px - cx) * scale + size/2
        Y = (cy - py) * scale + size/2  # قلب محور Y للرسم
        return X, Y

    for (a, b) in segs:
        X1, Y1 = map_pt(a[0], a[1])
        X2, Y2 = map_pt(b[0], b[1])
        p.drawLine(int(X1), int(Y1), int(X2), int(Y2))

    p.end()
    out_path = THUMBS_DIR / f"{out_name}.png"
    img.save(str(out_path))
    print(f"🖼️ [Thumb] saved {out_path}")
    return str(out_path)
