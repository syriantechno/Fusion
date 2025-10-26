# -*- coding: utf-8 -*-
from pathlib import Path
from PySide6.QtWidgets import (
    QLabel, QLineEdit, QTextEdit, QPushButton, QFileDialog,
    QVBoxLayout, QHBoxLayout, QWidget, QFrame
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from frontend.base.base_tool_window import BaseToolWindow
from profile.dxf_normalizer import load_dxf_segments
from profile.thumbnailer import draw_segments_thumbnail

class AddProfileWindow(BaseToolWindow):
    def __init__(self, parent=None):
        super().__init__("Add Profile", parent)
        self.setFixedSize(560, 640)
        self._build_ui()

    # --------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self.content_area)
        self.content_area.setStyleSheet("""
            QFrame, QWidget {
                background-color: #F1F2F1;
                border: none;
            }
        """)
        layout.setContentsMargins(24, 20, 24, 10)
        layout.setSpacing(14)

        # 🔹 دالة لإنشاء صف إدخال
        def make_labeled_input(label_text, placeholder=""):
            container = QWidget()
            hbox = QHBoxLayout(container)
            hbox.setContentsMargins(0, 0, 0, 0)
            hbox.setSpacing(10)

            lbl = QLabel(label_text)
            lbl.setFixedWidth(70)
            lbl.setStyleSheet("""
                color: #333;
                font-family: "Roboto";
                font-size: 13px;
                font-weight: 500;
            """)

            inp = QLineEdit()
            inp.setFrame(False)
            inp.setPlaceholderText(placeholder)
            inp.setFixedHeight(36)
            inp.setStyleSheet("""
                QLineEdit {
                    background-color: rgba(255,255,255,0.9);
                    border: 1px solid #C8C9C8;
                    border-radius: 5px;
                    font-family: "Roboto";
                    font-size: 12.5px;
                    color: #333;
                    padding: 4px 6px;
                }
                QLineEdit:focus {
                    border: 1px solid #E67E22;
                    background-color: #FFFFFF;
                }
            """)

            hbox.addWidget(lbl)
            hbox.addWidget(inp, 1)
            return container, inp

        # 🧩 إنشاء الحقول
        self.name_row, self.name_input = make_labeled_input("الاسم:", "Profile Name")
        self.size_row, self.size_input = make_labeled_input("القياس:", "Size")
        self.company_row, self.company_input = make_labeled_input("الشركة:", "Company")

        # 📝 حقل الوصف
        desc_container = QWidget()
        desc_layout = QHBoxLayout(desc_container)
        desc_layout.setContentsMargins(0, 0, 0, 0)
        desc_layout.setSpacing(10)

        desc_label = QLabel("الوصف:")
        desc_label.setFixedWidth(70)
        desc_label.setStyleSheet("color:#333; font-family:'Roboto'; font-size:13px; font-weight:500;")

        self.desc_input = QTextEdit()
        self.desc_input.setFrameStyle(QFrame.NoFrame)
        self.desc_input.setPlaceholderText("Profile Description...")
        self.desc_input.setFixedHeight(70)
        self.desc_input.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255,255,255,0.9);
                border: 1px solid #C8C9C8;
                border-radius: 5px;
                font-family: "Roboto";
                font-size: 12.5px;
                color: #333;
                padding: 6px 7px;
            }
            QTextEdit:focus {
                border: 1px solid #E67E22;
                background-color: #FFFFFF;
            }
        """)
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_input, 1)

        # 🗂️ اختيار ملف DXF
        file_row = QHBoxLayout()
        file_row.setSpacing(10)

        file_label = QLabel("ملف DXF:")
        file_label.setFixedWidth(70)
        file_label.setStyleSheet("color:#333; font-family:'Roboto'; font-size:13px; font-weight:500;")

        self.dxf_path = QLineEdit()
        self.dxf_path.setFrame(False)
        self.dxf_path.setPlaceholderText("Select DXF file...")
        self.dxf_path.setFixedHeight(36)
        self.dxf_path.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255,255,255,0.9);
                border: 1px solid #C8C9C8;
                border-radius: 5px;
                font-family: "Roboto";
                font-size: 13px;
                color: #333;
                padding: 4px 6px;
            }
            QLineEdit:focus {
                border: 1px solid #E67E22;
                background-color: #FFFFFF;
            }
        """)

        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedSize(100, 36)
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #F1F2F1;
                color: #333;
                border: 1px solid #C8C9C8;
                border-radius: 6px;
                font-family: "Roboto";
                font-size: 12.5px;
            }
            QPushButton:hover {
                background-color: #E67E22;
                color: white;
                border: 1px solid #E67E22;
            }
            QPushButton:pressed {
                background-color: #C25F12;
            }
        """)
        browse_btn.clicked.connect(self._browse_dxf)

        file_row.addWidget(file_label)
        file_row.addWidget(self.dxf_path, 1)
        file_row.addWidget(browse_btn)

        # 🖼️ المعاينة
        self.preview_label = QLabel("No Preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedHeight(240)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #F9F9F9;
                border: 1px solid #C8C9C8;
                border-radius: 8px;
                color: #777;
                font-family: "Roboto";
            }
        """)

        # 🧩 الترتيب العام
        layout.addWidget(self.name_row)
        layout.addWidget(self.size_row)
        layout.addWidget(self.company_row)
        layout.addWidget(desc_container)
        layout.addLayout(file_row)
        layout.addWidget(self.preview_label)
        layout.addStretch(1)

        # 🔘 زر OK
        self.btn_ok.clicked.connect(self._on_ok_clicked)
        self.adjustSize()

    # --------------------------------------------------------------
    def _browse_dxf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select DXF File", "", "DXF Files (*.dxf)"
        )
        if not file_path:
            return
        self.dxf_path.setText(file_path)
        self._generate_preview(file_path)

    # --------------------------------------------------------------
    def _generate_preview(self, file_path: str):
        try:
            segs, bbox = load_dxf_segments(Path(file_path))
            # 🧩 استخدم اسم البروفايل بدل اسم DXF
            safe_name = self.name_input.text().strip() or Path(file_path).stem
            safe_name = safe_name.replace(" ", "_").replace("/", "_")

            png_path = draw_segments_thumbnail(segs, bbox, safe_name)
            pix = QPixmap(png_path)
            self.preview_label.setPixmap(pix.scaled(
                self.preview_label.width(),
                self.preview_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
            print(f"✅ [Preview] generated: {png_path}")
        except Exception as e:
            print(f"❌ [Preview Error]: {e}")
            msg = QMessageBox(self)
            msg.setWindowTitle("Preview Error")
            msg.setText(str(e))
            msg.setIcon(QMessageBox.Warning)
            msg.exec()

    # --------------------------------------------------------------
    def _on_ok_clicked(self):
        name = self.name_input.text().strip()
        size = self.size_input.text().strip()
        company = self.company_input.text().strip()
        desc = self.desc_input.toPlainText().strip()
        dxf_path = self.dxf_path.text().strip()

        if not all([name, size, company, dxf_path]):
            self.show_message("حقول ناقصة", "يرجى تعبئة جميع الحقول المطلوبة.", "warn")
            return

        try:
            # 🖼️ توليد الصورة باسم البروفايل وليس DXF
            segs, bbox = load_dxf_segments(Path(dxf_path))
            safe_name = name or Path(dxf_path).stem
            safe_name = safe_name.replace(" ", "_").replace("/", "_")
            png_path = str(Path(draw_segments_thumbnail(segs, bbox, safe_name)).resolve())


            # 💾 حفظ في قاعدة البيانات
            from profile import profiles_db
            profiles_db.add_profile({
                "name": name,
                "code": safe_name,
                "company": company,
                "size": size,
                "file_path": dxf_path,
                "thumb_path": png_path,
                "source": "DXF"
            })

            print(f"💾 [AddProfile] Added to DB: {name} ({size})")
            self.show_message("تم الحفظ", "تم حفظ البروفايل بنجاح.", "success")
            self.close()

        except Exception as e:
            self.show_message("خطأ", f"فشل في حفظ البروفايل:\n{e}", "error")

