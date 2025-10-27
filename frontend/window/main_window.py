# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QLabel, QHBoxLayout, QPushButton
)
from PySide6.QtCore import Qt
from frontend.window.workspace_page import WorkspacePage

# استيراد العارض VTK
from viewer.vtk_viewer import VTKViewer


# -------------------------------------------------------------
# صفحة البداية
# -------------------------------------------------------------
class StartupPage(QWidget):
    """صفحة البداية — Start screen"""
    def __init__(self, on_start_callback=None):
        super().__init__()
        self.on_start_callback = on_start_callback

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("🔷 AlumProCNC\nمرحبا بك في بيئة العمل")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 20px; color: #566273;")

        start_btn = QPushButton("بدء العمل")
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #E67E22;
                color: white;
                padding: 10px 25px;
                border-radius: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #F39C12;
            }
        """)
        start_btn.clicked.connect(self._start_clicked)

        layout.addWidget(label)
        layout.addWidget(start_btn)

    def _start_clicked(self):
        print("✅ تم الضغط على بدء العمل")
        if self.on_start_callback:
            self.on_start_callback()

# -------------------------------------------------------------
# النافذة الرئيسية
# -------------------------------------------------------------
class MainWindow(QWidget):
    """النافذة الرئيسية التي تحتوي على كل صفحات البرنامج"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AlumProCNC — Main Window")
        self.resize(1200, 700)

        # 🔸 صفحات البرنامج
        self.pages = QStackedWidget()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.pages)

        # الصفحة 0: صفحة البداية
        self.startup_page = StartupPage(on_start_callback=self.show_workspace)
        self.pages.addWidget(self.startup_page)

        # الصفحة 1: صفحة بيئة العمل
        self.workspace_page = WorkspacePage()
        self.pages.addWidget(self.workspace_page)

        # بدء التشغيل على صفحة البداية
        self.pages.setCurrentIndex(0)

    def show_workspace(self):
        """الانتقال من صفحة البداية إلى صفحة العمل"""
        print("🚀 الانتقال إلى واجهة العمل")
        self.pages.setCurrentIndex(1)

    def open_profile_file(self, file_path: str):
        """تحميل ملف البروفايل عبر عارض VTK"""
        try:
            viewer = self.workspace_page.vtk_viewer
            viewer.load_dxf(file_path)  # ✅ الدالة الجديدة
            print(f"🟢 [MainWindow] تم تحميل الملف في العارض: {file_path}")
        except Exception as e:
            print(f"❌ [MainWindow] فشل تحميل الملف في العارض: {e}")



