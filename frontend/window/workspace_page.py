from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame
from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from frontend.window.top_bar import TopBar
from frontend.window.tabs_content import TabsContent
from draw.sketch_tools_panel import SketchToolsPanel
from viewer.vtk_viewer import VTKViewer
from profile.profile_tools_panel import ProfileToolsPanel
from tools.tools_tools_panel import ToolsToolsPanel
from shape.shape_tools_panel import ShapeToolsPanel
from cam.cam_tools_panel import CamToolsPanel
from operation.operation_tools_panel import OperationToolsPanel

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

        # 🧩 لوحة أدوات البروفايل (Profile Tools Panel)

        self.profile_tools_panel = ProfileToolsPanel(parent=self)
        self.profile_tools_panel.hide()
        layout.addWidget(self.profile_tools_panel, 0)

        self.shape_tools_panel = ShapeToolsPanel(parent=self)
        self.shape_tools_panel.hide()
        layout.addWidget(self.shape_tools_panel, 0)

        self.tools_tools_panel = ToolsToolsPanel(parent=self)
        self.tools_tools_panel.hide()
        layout.addWidget(self.tools_tools_panel, 0)

        self.operation_tools_panel = OperationToolsPanel(parent=self)
        self.operation_tools_panel.hide()
        layout.addWidget(self.operation_tools_panel, 0)


        self.cam_tools_panel = CamToolsPanel(parent=self)
        self.cam_tools_panel.hide()
        layout.addWidget(self.cam_tools_panel, 0)


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

    def on_tab_changed(self, tab_name: str):
        """
        يتم استدعاؤها عند تغيير التبويب من الأعلى (Sketch / Profile / Shape / Tools / CAM / Door)
        وتقوم بإظهار شريط الأدوات المناسب فقط بدون إخفاء العارض.
        """
        print(f"[Tab] Switched to: {tab_name}")

        # ✅ العارض يبقى دائمًا ظاهر
        if hasattr(self, "vtk_container"):
            self.vtk_container.show()

        # 🧹 إخفاء كل الأشرطة أولاً
        for panel_name in [
            "sketch_tools_panel",
            "profile_tools_panel",
            "shape_tools_panel",
            "tools_tools_panel",
            "operation_tools_panel",
            "cam_tools_panel",

        ]:
            panel = getattr(self, panel_name, None)
            if panel:
                panel.hide()

        # 🧭 قاموس يربط أسماء التبويبات مع الأشرطة
        panels = {
            "Sketch": getattr(self, "sketch_tools_panel", None),
            "Profile": getattr(self, "profile_tools_panel", None),
            "Shape": getattr(self, "shape_tools_panel", None),
            "Tools": getattr(self, "tools_tools_panel", None),
            "Operation": getattr(self, "operation_tools_panel", None),
            "CAM": getattr(self, "cam_tools_panel", None),

        }

        # 🎯 إظهار الشريط المطلوب
        target_panel = panels.get(tab_name)
        if target_panel:
            target_panel.show()
            print(f"🟢 [Workspace] تم تفعيل شريط {tab_name}")
        else:
            print(f"⚠️ [Workspace] تبويب غير معروف: {tab_name}")

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

    # ------------------------------------------------------------
    # 🔸 فتح نافذة قسم البروفايلات من المجلد الخارجي
    # ------------------------------------------------------------


