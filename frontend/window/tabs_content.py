from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QVBoxLayout, QStackedWidget
from PySide6.QtCore import Qt, Signal


class TabBar(QWidget):
    def __init__(self, parent=None, tabs=None):
        super().__init__(parent)
        self.tabs = tabs or ["Sketch", "Profile", "Shape", "Operation", "Tools", "CAM"]
        self.buttons = []
        self.active_index = 0

        self.setFixedHeight(42)

        # ✅ تلوين حقيقي بالستايل فقط (بدون QPalette)
        self.setStyleSheet("""
            QWidget#TabBar {
                background-color: #F1F2F1;
                border: none;
                border-bottom: 1px solid #C8C9C8;
            }
            QPushButton {
                background-color: transparent;
                color: #566273;
                font-weight: 500;
                font-size: 11pt;
                border: none;
                padding: 6px 14px;
            }
            QPushButton:hover {
                border-bottom: 3px solid #E67E22;
                color: #E67E22;
            }
            QPushButton:checked {
                border-bottom: 3px solid #E67E22;
                color: #E67E22;
            }
        """)
        self.setObjectName("TabBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        for i, name in enumerate(self.tabs):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setChecked(i == 0)
            btn.clicked.connect(lambda _, ix=i: self.set_active(ix))
            layout.addWidget(btn)
            self.buttons.append(btn)

        layout.addStretch()

    def set_active(self, index: int):
        for i, b in enumerate(self.buttons):
            b.setChecked(i == index)
        self.active_index = index
        tab_name = self.tabs[index]
        print(f"✅ [TabBar] تم اختيار التبويب: {tab_name}")
        if hasattr(self.parent(), "tab_selected"):
            self.parent().tab_selected.emit(tab_name)


class TabsContent(QWidget):
    tab_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ✅ ستايل شامل يفرض الخلفية الفاتحة على كل العناصر بداخلها
        self.setStyleSheet("""
            QWidget#TabsContent {
                background-color: #F1F2F1;
                border: none;
            }
            QStackedWidget {
                background-color: #F1F2F1;
                border: none;
            }
        """)
        self.setObjectName("TabsContent")

        self.tab_bar = TabBar(self)
        layout.addWidget(self.tab_bar)

        self.pages_stack = QStackedWidget()
        layout.addWidget(self.pages_stack, 1)

        # Sketch افتراضي
        self.tab_bar.set_active(0)
        print("✅ TabsContent (لون فاتح مؤكد — بدون أي تأثير من النظام)")
