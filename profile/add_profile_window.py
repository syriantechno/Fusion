# -*- coding: utf-8 -*-
import os
import math
import tempfile
from PySide6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QLineEdit,
    QFileDialog, QFrame, QMessageBox, QGraphicsView, QGraphicsScene
)
from PySide6.QtGui import QPixmap, QColor, QPainter, QPen, QPainterPath, QTransform
from PySide6.QtCore import Qt, QSize, Signal
from frontend.base.base_tool_window import BaseToolWindow

try:
    import ezdxf
except Exception:
    ezdxf = None


class DXFPreview(QGraphicsView):
    """🖼️ عرض DXF مع دعم Zoom + Pan"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setBackgroundBrush(QColor("#F8F8F8"))
        self._zoom = 1.0
        self._pan = False
        self._last_pos = None
        self.setRenderHint(QPainter.Antialiasing)

    def load_dxf(self, dxf_path: str):
        if not ezdxf:
            return False, 0, 0

        try:
            doc = ezdxf.readfile(dxf_path)
        except Exception:
            try:
                with open(dxf_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().replace(",", ".")
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".dxf")
                tmp.write(content.encode("utf-8"))
                tmp.close()
                doc = ezdxf.readfile(tmp.name)
                os.unlink(tmp.name)
            except Exception:
                return False, 0, 0

        msp = doc.modelspace()
        entities = list(msp.query("LINE ARC CIRCLE LWPOLYLINE SPLINE"))
        if not entities:
            return False, 0, 0

        self.scene().clear()
        min_x, min_y, max_x, max_y = 1e9, 1e9, -1e9, -1e9

        pen = QPen(QColor("#2C3E50"))
        pen.setWidthF(0.6)

        for e in entities:
            try:
                if e.dxftype() == "LINE":
                    s, t = e.dxf.start, e.dxf.end
                    self.scene().addLine(s.x, -s.y, t.x, -t.y, pen)
                    min_x, max_x = min(min_x, s.x, t.x), max(max_x, s.x, t.x)
                    min_y, max_y = min(min_y, s.y, t.y), max(max_y, s.y, t.y)
                elif e.dxftype() == "CIRCLE":
                    c, r = e.dxf.center, e.dxf.radius
                    self.scene().addEllipse(c.x - r, -c.y - r, 2 * r, 2 * r, pen)
                    min_x, max_x = min(min_x, c.x - r), max(max_x, c.x + r)
                    min_y, max_y = min(min_y, c.y - r), max(max_y, c.y + r)
                elif e.dxftype() == "ARC":
                    c, r = e.dxf.center, e.dxf.radius
                    start, end = e.dxf.start_angle, e.dxf.end_angle
                    path = QPainterPath()
                    path.moveTo(c.x + r * math.cos(math.radians(start)), -c.y - r * math.sin(math.radians(start)))
                    step = 4
                    a = start
                    while a < end:
                        x = c.x + r * math.cos(math.radians(a))
                        y = -c.y - r * math.sin(math.radians(a))
                        path.lineTo(x, y)
                        a += step
                    self.scene().addPath(path, pen)
                    min_x, max_x = min(min_x, c.x - r), max(max_x, c.x + r)
                    min_y, max_y = min(min_y, c.y - r), max(max_y, c.y + r)
                elif e.dxftype() == "LWPOLYLINE":
                    pts = [(v[0], -v[1]) for v in e]
                    path = QPainterPath()
                    for i, (x, y) in enumerate(pts):
                        path.moveTo(*pts[0]) if i == 0 else path.lineTo(x, y)
                    if e.closed:
                        path.closeSubpath()
                    self.scene().addPath(path, pen)
                elif e.dxftype() == "SPLINE":
                    pts = [(p.x, -p.y) for p in e.fit_points()]
                    path = QPainterPath()
                    for i, (x, y) in enumerate(pts):
                        path.moveTo(*pts[0]) if i == 0 else path.lineTo(x, y)
                    self.scene().addPath(path, pen)
            except Exception:
                pass

        width, height = max_x - min_x, max_y - min_y
        self.fitInView(min_x, -max_y, width, height, Qt.KeepAspectRatio)
        return True, width, height

    def wheelEvent(self, e):
        zoom_factor = 1.15 if e.angleDelta().y() > 0 else 1 / 1.15
        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._pan = True
            self._last_pos = e.pos()
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._pan and self._last_pos:
            delta = e.pos() - self._last_pos
            self._last_pos = e.pos()
            self.translate(delta.x(), delta.y())
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._pan = False
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(e)


class AddProfileWindow(BaseToolWindow):
    """نافذة إضافة بروفايل جديدة"""

    profile_ready = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(title="إضافة بروفايل جديد", parent=parent)
        self.setMinimumSize(900, 600)

        self.file_path = ""
        self.thumb_path = ""

        root = QHBoxLayout(self.content_area)
        root.setContentsMargins(10, 10, 10, 10)

        # القسم الأيسر
        self.viewer = DXFPreview()
        root.addWidget(self.viewer, 1)

        # القسم الأيمن
        right = QFrame()
        right.setFixedWidth(300)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 8, 8, 8)

        def make_edit(ph):
            e = QLineEdit()
            e.setPlaceholderText(ph)
            e.setFixedHeight(36)
            e.setStyleSheet("QLineEdit{background:#fff;border:1px solid #C8C9C8;border-radius:6px;padding:6px 10px;}")
            return e

        self.edt_name = make_edit("اسم البروفايل")
        self.edt_code = make_edit("الكود / رقم التعريف")
        self.edt_company = make_edit("اسم الشركة")
        self.edt_size = make_edit("الأبعاد (مم)")

        self.btn_browse = QPushButton("📂 اختيار ملف DXF…")
        self.btn_browse.setFixedHeight(36)
        self.btn_browse.setStyleSheet("QPushButton{background:#3498DB;color:#fff;border-radius:6px;font-weight:bold;} QPushButton:hover{background:#5DADE2;}")

        for w in (self.edt_name, self.edt_code, self.edt_company, self.edt_size, self.btn_browse):
            right_layout.addWidget(w)
        right_layout.addStretch(1)

        self.btn_ok.setText("إضافة إلى المكتبة")
        self.btn_cancel.setText("إلغاء")

        root.addWidget(right, 0)

        self.btn_browse.clicked.connect(self._pick_dxf)
        self.btn_ok.clicked.connect(self._submit)

        self.setToolTip("استخدم عجلة الماوس للتكبير/التصغير — اسحب لتحريك")

    def _pick_dxf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "اختيار ملف DXF", "", "ملفات DXF (*.dxf)")
        if not file_path:
            return
        self.file_path = file_path
        ok, w, h = self.viewer.load_dxf(file_path)
        if ok:
            self.edt_size.setText(f"{w:.2f} x {h:.2f} mm")

    def _submit(self):
        if not self.file_path:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار ملف DXF.")
            return
        data = {
            "name": self.edt_name.text(),
            "code": self.edt_code.text(),
            "company": self.edt_company.text(),
            "size": self.edt_size.text(),
            "file_path": self.file_path,
            "thumb_path": "",
            "source": "DXF",
        }
        self.profile_ready.emit(data)
        self.close()
