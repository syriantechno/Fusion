# -*- coding: utf-8 -*-
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "profiles.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
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

def add_profile(data):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO profiles (name, code, company, size, file_path, thumb_path, source, date_added)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("name", ""), data.get("code", ""), data.get("company", ""), data.get("size", ""),
        data.get("file_path", ""), data.get("thumb_path", ""), data.get("source", "DXF"),
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ))
    conn.commit()
    conn.close()

def get_all_profiles():
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
