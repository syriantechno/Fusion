# -*- coding: utf-8 -*-
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QLineEdit, QFrame, QSizePolicy, QSpacerItem, QPushButton
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap
from frontend.base.base_tool_window import BaseToolWindow
from profile.face_selector import FaceSelector


class ProfileManagerWindow(BaseToolWindow):
    def __init__(self, parent=None):
        super().__init__(title="Profile Manager", parent=parent)
        self._profiles = []
        self._current = None
        self._build_ui()
        self._load_profiles_from_db()


    def _build_ui(self):
        layout = QHBoxLayout(self.content_area)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # ---------- القسم الأيسر ----------
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search profiles...")
        self.search_box.textChanged.connect(self._apply_filter)
        self.search_box.setStyleSheet("""
            QLineEdit {
                background: #fff;
                border: 1px solid #C8C9C8;
                border-radius: 3px;
                padding: 6px 8px;
                font-size: 12px;
            }
            QLineEdit:focus { border-color: #999; }
        """)

        self.list_widget = QListWidget()
        self.list_widget.itemSelectionChanged.connect(self._on_select_item)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: #fff;
                border: 1px solid #C8C9C8;
                border-radius: 3px;
                color: #333;
                font-family: "Roboto";
                font-size: 12.5px;
            }
            QListWidget::item { padding: 6px 8px; }
            QListWidget::item:selected {
                background-color: #E67E22;
                color: white;
                border-radius: 3px;
            }
        """)
        left_layout.addWidget(self.search_box)
        left_layout.addWidget(self.list_widget, 1)

        # ---------- القسم الأيمن ----------
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(10)
        right_panel.setStyleSheet("""
            QFrame {
                background-color: rgba(255,255,255,0.7);
                border-radius: 3px;
                border: 1px solid rgba(200,201,200,0.6);
            }
        """)

        self.preview_label = QLabel("No Image")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedSize(260, 180)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #FAFAFA;
                border: 1px dashed #C8C9C8;
                border-radius: 3px;
                color: #666;
            }
        """)
        right_layout.addWidget(self.preview_label, alignment=Qt.AlignCenter)

        # ---------- الحقول ----------
        def make_field(title):
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(255,255,255,0.6);
                    border: 1px solid rgba(180,180,180,0.6);
                    border-radius: 5px;
                }
            """)
            lay = QHBoxLayout(frame)
            lay.setContentsMargins(8, 3, 8, 3)
            lay.setSpacing(8)
            lbl = QLabel(title)
            lbl.setStyleSheet("color:#777;font-family:Roboto;font-size:11.5px;font-weight:500;")
            val = QLabel("-")
            val.setStyleSheet("color:#333;font-family:Roboto;font-size:12.5px;")
            lay.addWidget(lbl)
            lay.addWidget(val, 1)
            return frame, val

        self.name_field, self.name_val = make_field("Name")
        self.size_field, self.size_val = make_field("Size")
        self.company_field, self.company_val = make_field("Company")
        self.desc_field, self.desc_val = make_field("Description")

        for w in [self.name_field, self.size_field, self.company_field, self.desc_field]:
            right_layout.addWidget(w)

        # ---------- أزرار التحكم ----------
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 10, 0, 0)
        btn_layout.setSpacing(10)

        btn_edit = QPushButton("Edit")
        btn_delete = QPushButton("Delete")

        for b in (btn_edit, btn_delete):
            b.setFixedHeight(32)
            b.setMinimumWidth(90)
            b.setStyleSheet("""
                QPushButton {
                    background-color: #F1F2F1;
                    color: #333333;
                    border: 1px solid #C8C9C8;
                    border-radius: 6px;
                    font-family: "Roboto";
                    font-size: 13px;
                    padding: 4px 14px;
                }
                QPushButton:hover {
                    background-color: #E8E8E8;
                    border-color: #B0B0B0;
                }
                QPushButton:pressed {
                    background-color: #DCDCDC;
                }
            """)

        btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #F1F2F1;
                color: #B20000;
                border: 1px solid #C8C9C8;
                border-radius: 6px;
                font-family: Roboto;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #F9E2E2; }
        """)

        btn_layout.addStretch(1)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)
        right_layout.addWidget(btn_container)

        # ---------- الخط الفاصل (رفيع جدًا مثل العلوي) ----------
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Plain)
        sep.setStyleSheet("""
            QFrame {
                background-color: #C8C9C8;
                border: none;
                height: 1px;
                max-height: 1px;
            }
        """)
        right_layout.addWidget(sep)

        # ---------- Face Selector ----------
        face_label = QLabel("Projection Face:")
        face_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-family: "Roboto";
                font-size: 12px;
                
            }
        """)
        right_layout.addWidget(face_label, alignment=Qt.AlignLeft)

        # 🧭 تغليف الأداة مع مسافة مريحة حولها
        face_frame = QFrame()
        face_layout = QHBoxLayout(face_frame)
        face_layout.setContentsMargins(0, 20, 0, 15)  # ✅ زيد المسافة العلوية والسفلية
        face_layout.setAlignment(Qt.AlignCenter)

        self.face_selector = FaceSelector()
        self.face_selector.setFixedSize(120, 120)  # زيادة بسيطة بالسعة
        face_layout.addWidget(self.face_selector)

        # ارتفاع كافٍ لاحتواء كل النصوص الخارجية
        face_frame.setFixedHeight(160)
        right_layout.addWidget(face_frame)

        layout.addWidget(left_panel, 1)
        layout.addWidget(right_panel, 2)
        self.btn_ok.clicked.connect(self._on_ok_clicked)

    # ------------------------------------------------------------------
    def _load_profiles_from_db(self):
        """تحميل البيانات الفعلية من قاعدة SQLite"""
        from profile import profiles_db
        rows = profiles_db.get_all_profiles()

        self._profiles = []
        for r in rows:
            self._profiles.append({
                "id": r[0],
                "name": r[1],
                "code": r[2],
                "company": r[3],
                "size": r[4],
                "file_path": r[5],
                "image": r[6],  # thumb_path
                "source": r[7],
                "date_added": r[8],
            })
        self._populate_list(self._profiles)

    def _populate_list(self, items):
        self.list_widget.clear()
        for p in items:
            it = QListWidgetItem(p["name"])
            it.setData(Qt.UserRole, p)
            self.list_widget.addItem(it)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _apply_filter(self, text):
        t = (text or "").lower().strip()
        if not t:
            self._populate_list(self._profiles)
            return
        f = [p for p in self._profiles if any(t in p[k].lower() for k in ("name","size","company","desc"))]
        self._populate_list(f)

    def _on_select_item(self):
        items = self.list_widget.selectedItems()
        if not items:
            self._show_details(None)
            return
        self._current = items[0].data(Qt.UserRole)
        self._show_details(self._current)

    def _show_details(self, p):
        if not p:
            for lbl in (self.name_val, self.size_val, self.company_val, self.desc_val):
                lbl.setText("-")
            self.preview_label.setText("No Image")
            self.preview_label.setPixmap(QPixmap())
            return
        self.name_val.setText(p["name"])
        self.size_val.setText(p["size"])
        self.company_val.setText(p["company"])
        self.desc_val.setText(p["desc"])
        img = Path(p["image"])
        if img.exists():
            pix = QPixmap(str(img)).scaled(QSize(260, 180), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_label.setPixmap(pix)
        else:
            self.preview_label.setText("No Image")

    def _on_ok_clicked(self):
        if not self._current:
            print("ℹ️ لا يوجد بروفايل محدد")
            return
        print("✅ Profile:", self._current["name"], "| Face:", self.face_selector.get_selected_face())
        self.close()
