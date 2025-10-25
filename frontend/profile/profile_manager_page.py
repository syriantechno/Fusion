# frontend/window/profile_manager_page.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QScrollArea, QFrame, QLabel, QLineEdit, QFormLayout, QDialog, QMessageBox, QGridLayout
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QIcon
from pathlib import Path

from frontend.profile.profiles_db import ProfilesDB, ProfileItem
from frontend.profile.dxf_normalizer import load_dxf_segments
from frontend.profile.thumbnailer import draw_segments_thumbnail

ASSETS = Path("assets")
ASSETS.mkdir(exist_ok=True, parents=True)

class AddProfileDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إضافة بروفايل")
        self.setMinimumWidth(420)
        self.file_path: Path | None = None

        form = QFormLayout(self)
        self.name_in = QLineEdit(); self.code_in = QLineEdit()
        self.notes_in = QLineEdit()
        pick_btn = QPushButton("اختيار ملف…")
        pick_btn.clicked.connect(self._pick_file)

        form.addRow("الاسم:", self.name_in)
        form.addRow("الكود:", self.code_in)
        form.addRow("ملاحظات:", self.notes_in)
        form.addRow("ملف البروفايل:", pick_btn)

        btns = QHBoxLayout()
        ok = QPushButton("إضافة"); ok.setStyleSheet("background:#27AE60;color:white;padding:6px 14px;border-radius:8px;")
        cancel = QPushButton("إلغاء")
        ok.clicked.connect(self.accept); cancel.clicked.connect(self.reject)
        btns.addWidget(ok); btns.addWidget(cancel)
        form.addRow(btns)

    def _pick_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "اختيار ملف", "", "DXF/BREP/STEP (*.dxf *.brep *.stp *.step)")
        if f:
            self.file_path = Path(f)

    def get_data(self):
        return self.name_in.text().strip(), self.code_in.text().strip(), self.notes_in.text().strip(), self.file_path

class ProfileCard(QFrame):
    def __init__(self, item: ProfileItem, on_ok):
        super().__init__()
        self.item = item
        self.setObjectName("card")
        self.setStyleSheet("""
        QFrame#card { background:#FFFFFF; border:1px solid #C8C9C8; border-radius:16px; }
        QFrame#card:hover { border-color:#E67E22; }
        QLabel.title { font-size:13px; font-weight:600; color:#2C3E50; }
        QLabel.sub { color:#7F8C8D; }
        """)
        lay = QVBoxLayout(self); lay.setContentsMargins(12,12,12,12)
        img = QLabel()
        thumb = item.thumbnail_path if item.thumbnail_path and Path(item.thumbnail_path).exists() else "assets/icons/profile_placeholder.png"
        img.setPixmap(QPixmap(thumb).scaled(220,220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        img.setAlignment(Qt.AlignCenter)
        t = QLabel(f"{item.name}"); t.setProperty("class","title")
        s = QLabel(f"{item.code} — {item.file_type.upper()}"); s.setProperty("class","sub")
        btn = QPushButton("OK · تحميل"); btn.setStyleSheet("background:#E67E22;color:white;border-radius:10px;padding:6px 10px;")
        btn.clicked.connect(lambda: on_ok(item))
        lay.addWidget(img); lay.addWidget(t); lay.addWidget(s); lay.addWidget(btn)

class ProfileManagerPage(QWidget):
    def __init__(self, viewer=None, parent=None):
        super().__init__(parent)
        self.viewer = viewer  # لزر OK
        self.db = ProfilesDB()

        root = QVBoxLayout(self); root.setContentsMargins(10,10,10,10)
        header = QHBoxLayout()
        title = QLabel("📚 مكتبة البروفايلات"); title.setStyleSheet("font-size:16px;font-weight:700;color:#2C3E50;")
        add_btn = QPushButton("➕ إضافة بروفايل"); add_btn.setStyleSheet("background:#27AE60;color:white;border-radius:10px;padding:6px 12px;")
        add_btn.clicked.connect(self._add_profile)
        header.addWidget(title); header.addStretch(); header.addWidget(add_btn)
        root.addLayout(header)

        # شبكة بطاقات داخل Scroll
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.cards_host = QWidget(); self.grid = QGridLayout(self.cards_host)
        self.grid.setSpacing(12)
        self.scroll.setWidget(self.cards_host)
        root.addWidget(self.scroll, 1)

        self.reload_cards()

    def reload_cards(self):
        # امسح الشبكة
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w: w.deleteLater()
        items = self.db.list_all()
        cols = 4
        for i, it in enumerate(items):
            card = ProfileCard(it, self._on_ok)
            self.grid.addWidget(card, i//cols, i%cols)

    def _on_ok(self, item: ProfileItem):
        print(f"🟧 [Profile OK] {item.code} -> تحميل للعارض…")
        # هنا أعمل load حسب نوع الملف – DXF/BREP/…
        # حالياً فقط رسالة:
        QMessageBox.information(self, "Profile", f"سيتم تحميل: {item.name} ({item.code})")

    def _add_profile(self):
        dlg = AddProfileDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        name, code, notes, fpath = dlg.get_data()
        if not name or not code or not fpath:
            QMessageBox.warning(self, "تنبيه", "الاسم + الكود + الملف مطلوبة.")
            return

        path = Path(fpath)
        ftype = path.suffix.lower().lstrip(".")
        item = ProfileItem(None, name, code, str(path), ftype, None, None, None, notes or "")
        pid = self.db.add(item)

        # لو DXF: طبّع + اصنع مصغّر + استخرج أبعاد تقريبيّة
        thumb = None; w = h = None
        try:
            if ftype == "dxf":
                segs, bbox = load_dxf_segments(path)
                w = bbox[2]-bbox[0]; h = bbox[3]-bbox[1]
                thumb = draw_segments_thumbnail(segs, bbox, out_name=f"profile_{pid}")
        except Exception as e:
            print(f"⚠️ DXF normalize/thumbnail error: {e}")

        self.db.update_thumb_and_dims(pid, thumb, w, h)
        self.reload_cards()
        QMessageBox.information(self, "تم", "تمت إضافة البروفايل بنجاح ✅")
