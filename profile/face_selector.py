from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor


class FaceSelector(QWidget):
    """🧭 أداة اختيار الوجه الرئيسي (Top / Bottom / Left / Right)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(160, 160)
        self.active_face = "left"
        self.face_positions = {
            "top": QPointF(80, 25),
            "bottom": QPointF(80, 135),
            "left": QPointF(25, 80),
            "right": QPointF(135, 80),
        }

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#FFFFFF"))

        # المربع
        p.setPen(QPen(Qt.black, 1))
        p.setBrush(QBrush(QColor(245, 245, 245)))
        p.drawRect(55, 55, 50, 50)

        # النقاط
        for face, pos in self.face_positions.items():
            color = QColor("#00AEEF") if face == self.active_face else QColor("#AAAAAA")
            p.setBrush(QBrush(color))
            p.drawEllipse(pos, 10, 10)

    def mousePressEvent(self, event):
        for face, pos in self.face_positions.items():
            if (event.position() - pos).manhattanLength() <= 12:
                self.active_face = face
                self.update()
                print(f"🧭 الوجه المختار: {face}")
                break

    def get_selected_face(self):
        return self.active_face
