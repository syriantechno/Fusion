# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont


class FaceSelector(QWidget):
    """🧭 أداة اختيار الوجه (كل الاتجاهات ظاهرة تمامًا)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 120)   # مساحة كافية لكل النصوص
        self.active_face = "left"

        # نقاط الاتجاهات
        self.face_positions = {
            "top": QPointF(60, 25),
            "bottom": QPointF(60, 95),
            "left": QPointF(25, 60),
            "right": QPointF(95, 60),
        }

        # تسميات الاتجاهات
        self.labels = {
            "top": "TOP",
            "bottom": "BOT",
            "left": "L",
            "right": "R",
        }

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#FFFFFF"))

        # 🟦 المربع المركزي
        p.setPen(QPen(Qt.black, 1))
        p.setBrush(QBrush(QColor(245, 245, 245)))
        p.drawRect(50, 50, 20, 20)

        # 🟠 النقاط + التسميات
        font = QFont("Roboto", 8)
        font.setBold(True)
        p.setFont(font)

        for face, pos in self.face_positions.items():
            # لون النقطة
            color = QColor("#E74C3C") if face == self.active_face else QColor("#AAAAAA")
            p.setBrush(QBrush(color))
            p.setPen(QPen(Qt.black, 0.6))
            p.drawEllipse(pos, 5, 5)

            # مواضع النصوص خارج الإطار بدقة
            if face == "top":
                text_pos = QPointF(pos.x() - 12, pos.y() - 12)
            elif face == "bottom":
                text_pos = QPointF(pos.x() - 12, pos.y() + 22)
            elif face == "left":
                text_pos = QPointF(pos.x() - 25, pos.y() + 4)
            else:  # right
                text_pos = QPointF(pos.x() + 12, pos.y() + 4)

            p.setPen(QColor("#444"))
            p.drawText(text_pos, self.labels[face])

    def mousePressEvent(self, event):
        for face, pos in self.face_positions.items():
            if (event.position() - pos).manhattanLength() <= 8:
                self.active_face = face
                self.update()
                print(f"🧭 الوجه المختار: {face.upper()}")
                break

    def get_selected_face(self):
        return self.active_face
