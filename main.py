# -*- coding: utf-8 -*-
"""
AlumProCNC — Main Launcher
🚀 الملف الرئيسي لتشغيل واجهة البرنامج
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt
from frontend.window.main_window import MainWindow

if __name__ == "__main__":
    # 🔹 إنشاء التطبيق مرة واحدة
    app = QApplication(sys.argv)

    # 🔹 تعطيل أي ستايل داكن مفروض
    app.setStyle("Fusion")

    # 🔹 فرض الألوان الفاتحة على مستوى التطبيق كله
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#F1F2F1"))
    palette.setColor(QPalette.Base, QColor("#F1F2F1"))
    palette.setColor(QPalette.Button, QColor("#F1F2F1"))
    palette.setColor(QPalette.AlternateBase, QColor("#FFFFFF"))
    palette.setColor(QPalette.Text, QColor("#566273"))
    palette.setColor(QPalette.ButtonText, QColor("#566273"))
    palette.setColor(QPalette.Highlight, QColor("#E67E22"))
    palette.setColor(QPalette.HighlightedText, Qt.white)
    app.setPalette(palette)

    # 🔹 إنشاء الواجهة الرئيسية
    window = MainWindow()
    window.show()

    # 🔹 تشغيل التطبيق
    sys.exit(app.exec())


