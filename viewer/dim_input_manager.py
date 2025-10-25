# -*- coding: utf-8 -*-
"""
dim_input_manager.py — Fusion-style manual input overlay
"""

from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont

class DimInputManager:
    def __init__(self, viewer):
        self.viewer = viewer
        self.input = QLineEdit(viewer)
        self.input.hide()
        self.input.setFixedWidth(100)
        self.input.setAlignment(Qt.AlignCenter)
        self.input.setPlaceholderText("Enter value")
        self.input.setStyleSheet("""
            QLineEdit {
                background-color: #F1F2F1;
                border: 1px solid #C8C9C8;
                border-radius: 6px;
                color: #222;
                padding: 3px;
                font: 11pt 'Roboto';
            }
            QLineEdit:focus {
                border: 1px solid #E67E22;
            }
        """)

        self.input.returnPressed.connect(self.apply_value)
        self.input.keyPressEvent = self._on_key_press

        self.active = False
        self.callback = None

    def show(self, screen_pos, label="Value", callback=None):
        self.active = True
        self.callback = callback
        self.input.clear()
        self.input.show()
        self.input.move(QPoint(screen_pos[0] + 15, screen_pos[1] - 25))
        self.input.setFocus()

    def hide(self):
        self.active = False
        self.callback = None
        self.input.hide()

    def apply_value(self):
        if not self.active:
            return
        text = self.input.text().strip()
        if not text:
            self.hide()
            return
        if self.callback:
            self.callback(text)
        self.hide()

    def _on_key_press(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            QLineEdit.keyPressEvent(self.input, event)
