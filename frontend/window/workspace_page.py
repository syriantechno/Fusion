from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame
from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from frontend.window.top_bar import TopBar
from frontend.window.tabs_content import TabsContent
from draw.sketch_tools_panel import SketchToolsPanel
from viewer.vtk_viewer import VTKViewer


class WorkspacePage(QWidget):
    """صفحة بيئة العمل (ألوان فاتحة فقط)"""
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.setStyleSheet("background-color: #F1F2F1;")

        # 🔹 التوب بار
        self.top_bar = TopBar(self)
        layout.addWidget(self.top_bar, 0)

        # 🔹 التبويبات
        self.tabs_content = TabsContent(self)
        layout.addWidget(self.tabs_content, 0)

        # 🔹 أدوات السكيتش
        self.sketch_tools_panel = SketchToolsPanel(parent=self)
        layout.addWidget(self.sketch_tools_panel, 0)

        # ✅ مبدئياً نظهرها لأن Sketch هو النشط
        self.sketch_tools_panel.show()

        # 🔹 العارض
        self.vtk_container = QFrame(self)
        self.vtk_container.setStyleSheet("background-color: #F1F2F1; border:none;")
        vtk_layout = QVBoxLayout(self.vtk_container)
        vtk_layout.setContentsMargins(0, 0, 0, 0)
        self.vtk_viewer = VTKViewer(self.vtk_container)
        vtk_layout.addWidget(self.vtk_viewer)
        layout.addWidget(self.vtk_container, 1)

        # 🔗 ربط الأدوات بالعارض
        self.sketch_tools_panel.vtk_viewer = self.vtk_viewer

        # 🔗 ربط إشارة التبويبات
        self.tabs_content.tab_selected.connect(self.on_tab_changed)

        print("✅ WorkspacePage (فاتحة بالكامل — Sketch نشطة افتراضيًا)")

    def on_tab_changed(self, tab_name):
        """إظهار أو إخفاء أدوات السكيتش"""
        if tab_name == "Sketch":
            self.fade_panel(True)
        else:
            self.fade_panel(False)

    def fade_panel(self, show=True):
        """تأثير ظهور/اختفاء سلس"""
        panel = self.sketch_tools_panel
        anim = QPropertyAnimation(panel, b"windowOpacity")
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        if show:
            panel.setWindowOpacity(0)
            panel.show()
            anim.setStartValue(0)
            anim.setEndValue(1)
        else:
            anim.setStartValue(1)
            anim.setEndValue(0)
            anim.finished.connect(panel.hide)
        anim.start()
        self._fade_anim = anim
