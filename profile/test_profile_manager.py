# -*- coding: utf-8 -*-
import sys
from PySide6.QtWidgets import QApplication
from profile.profile_manager_window import ProfileManagerWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # إنشاء النافذة
    win = ProfileManagerWindow()
    win.show()

    sys.exit(app.exec())
