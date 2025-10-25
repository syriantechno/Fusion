# -*- coding: utf-8 -*-
"""
AlumProCNC — Top Bar
✅ تصميم الشريط العلوي (يسار أيقونات + وسط فاتح + يمين إعدادات)
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QFrame, QPushButton
from PySide6.QtGui import QPainter, QPainterPath, QBrush, QColor, QPixmap, QIcon
from PySide6.QtCore import Qt, QSize, QEvent
from PySide6.QtSvg import QSvgRenderer

# 🎨 ألوان AlumProCNC الرسمية
DARK_COLOR = "#C8C9C8"       # الرمادي الغامق (الأطراف)
LIGHT_COLOR = "#F1F2F1"      # الرمادي الفاتح (الوسط)
ACCENT_ORANGE = "#E67E22"    # اللون البرتقالي للنشاط
ICON_COLOR = "#566273"       # اللون الأساسي للأيقونات والنصوص

# ==============================================================
# 🔧 دالة مساعدة لتلوين SVG
# ==============================================================
def tint_svg(svg_path: str, color_hex: str, size: QSize) -> QIcon:
    """تلوين SVG بلون مخصص"""
    renderer = QSvgRenderer(svg_path)
    pixmap = QPixmap(size)
    pixmap.fill(Qt.transparent)

    p = QPainter(pixmap)
    renderer.render(p)
    p.end()

    tinted = QPixmap(size)
    tinted.fill(Qt.transparent)
    p2 = QPainter(tinted)
    p2.fillRect(tinted.rect(), QColor(color_hex))
    p2.setCompositionMode(QPainter.CompositionMode_DestinationIn)
    p2.drawPixmap(0, 0, pixmap)
    p2.end()

    return QIcon(tinted)

# ==============================================================
# 🧭 الكلاس الأساسي للشريط العلوي
# ==============================================================
class TopBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedHeight(40)
        self.setStyleSheet("background-color: transparent;")

        self.icon_color = ICON_COLOR
        self.icon_hover_color = ACCENT_ORANGE
        self.icon_size = QSize(24, 24)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ⬅️ القسم الغامق اليساري (أزرار الأدوات)
        left_bar = QFrame()
        left_bar.setFixedWidth(200)
        left_bar.setStyleSheet(f"background-color: {DARK_COLOR};")
        left_layout = QHBoxLayout(left_bar)
        left_layout.setContentsMargins(8, 4, 8, 4)
        left_layout.setSpacing(10)

        icons = [
            ("open.svg", "فتح ملف"),
            ("new.svg", "ملف جديد"),
            ("save.svg", "حفظ"),
            ("undo.svg", "تراجع"),
            ("redo.svg", "تقدم")
        ]

        self.buttons = []
        for icon_name, tooltip in icons:
            btn = QPushButton()
            btn.setToolTip(tooltip)
            btn.setIcon(tint_svg(f"assets/icons/{icon_name}", self.icon_color, self.icon_size))
            btn.setIconSize(self.icon_size)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    padding: 4px;
                }
                QPushButton:hover {
                    background: transparent;
                }
            """)
            btn.installEventFilter(self)
            left_layout.addWidget(btn)
            self.buttons.append((btn, icon_name))

        # 🟦 القسم الفاتح الأوسط
        center = QFrame()
        center.setStyleSheet(f"background-color: {LIGHT_COLOR};")
        center.setMinimumWidth(400)

        # ➡️ القسم الغامق اليميني (زر الإعدادات)
        right_bar = QFrame()
        right_bar.setFixedWidth(200)
        right_bar.setStyleSheet(f"background-color: {DARK_COLOR};")

        right_layout = QHBoxLayout(right_bar)
        right_layout.setContentsMargins(8, 4, 8, 4)
        right_layout.setSpacing(10)
        right_layout.addStretch()

        # ⚙️ زر الإعدادات
        self.settings_btn = QPushButton()
        self.settings_btn.setToolTip("الإعدادات")
        self.settings_btn.setIcon(tint_svg("assets/icons/gear.svg", self.icon_color, self.icon_size))
        self.settings_btn.setIconSize(self.icon_size)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 4px;
            }
            QPushButton:hover {
                background: transparent;
            }
        """)
        self.settings_btn.installEventFilter(self)
        self.settings_btn.clicked.connect(lambda: print("⚙️ Settings clicked"))
        right_layout.addWidget(self.settings_btn)

        layout.addWidget(left_bar)
        layout.addWidget(center, 1)
        layout.addWidget(right_bar)

        # أضف زر الإعدادات إلى القائمة العامة
        self.buttons.append((self.settings_btn, "gear.svg"))

    # ==============================================================
    # 🖱️ تغيير لون الأيقونات عند hover فقط
    # ==============================================================
    def eventFilter(self, obj, event):
        for btn, path in self.buttons:
            if obj == btn:
                if event.type() == QEvent.Enter:
                    btn.setIcon(tint_svg(f"assets/icons/{path}", self.icon_hover_color, self.icon_size))
                elif event.type() == QEvent.Leave:
                    btn.setIcon(tint_svg(f"assets/icons/{path}", self.icon_color, self.icon_size))
        return super().eventFilter(obj, event)

    # ==============================================================
    # 🎨 رسم الكورنرات العلوية للقسم الفاتح الأوسط
    # ==============================================================
    def paintEvent(self, event):
        """رسم الزوايا المستديرة للجزء الفاتح"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        r = 8

        path = QPainterPath()
        path.moveTo(200, h)
        path.lineTo(200, r)
        path.quadTo(200, 0, 200 + r, 0)
        path.lineTo(w - 200 - r, 0)
        path.quadTo(w - 200, 0, w - 200, r)
        path.lineTo(w - 200, h)
        path.lineTo(200, h)
        path.closeSubpath()

        painter.setBrush(QBrush(QColor(LIGHT_COLOR)))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)

    # ==============================================================
    # 🎨 تغيير لون جميع الأيقونات أثناء التشغيل
    # ==============================================================
    def set_icon_color(self, color_hex: str):
        """تغيير لون جميع الأيقونات أثناء التشغيل"""
        print(f"🎨 تغيير لون الأيقونات إلى: {color_hex}")
        self.icon_color = color_hex
        for btn, path in self.buttons:
            btn.setIcon(tint_svg(f"assets/icons/{path}", color_hex, self.icon_size))
