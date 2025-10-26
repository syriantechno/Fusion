# -*- coding: utf-8 -*-
"""
📦 Profile Database Manager (SQLite)
يدير قاعدة بيانات البروفايلات:
- إنشاء قاعدة البيانات عند أول تشغيل
- إضافة / قراءة البروفايلات
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path

# تحديد مسار القاعدة داخل مجلد المشروع
DB_PATH = Path(__file__).parent / "profiles.db"

# -----------------------------------------------------------
def init_db():
    """تهيئة القاعدة وإنشاء الجدول إن لم يكن موجوداً"""
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            code TEXT,
            company TEXT,
            size TEXT,
            file_path TEXT,
            thumb_path TEXT,
            source TEXT,
            date_added TEXT
        )
    """)
    conn.commit()
    conn.close()
    print(f"🧱 [DB] Ready at: {DB_PATH}")

# -----------------------------------------------------------
def add_profile(data: dict):
    """إضافة سجل بروفايل جديد"""
    init_db()

    # 🧩 تصحيح المسارات لتكون مطلقة
    file_path = str(Path(data.get("file_path", "")).resolve())
    thumb_path = str(Path(data.get("thumb_path", "")).resolve())

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO profiles (name, code, company, size, file_path, thumb_path, source, date_added)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("name", ""),
        data.get("code", ""),
        data.get("company", ""),
        data.get("size", ""),
        file_path,
        thumb_path,
        data.get("source", "DXF"),
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ))
    conn.commit()
    conn.close()

    print(f"💾 [DB] Added Profile: {data.get('name')} | Thumb={thumb_path}")

# -----------------------------------------------------------
def get_all_profiles():
    """جلب جميع البروفايلات"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, code, company, size, file_path, thumb_path, source, date_added
        FROM profiles ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows
