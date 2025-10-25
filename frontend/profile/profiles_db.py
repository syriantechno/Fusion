# frontend/profile/profiles_db.py
# -*- coding: utf-8 -*-
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Tuple

DB_PATH = Path("data/profiles.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

@dataclass
class ProfileItem:
    id: Optional[int]
    name: str
    code: str
    file_path: str
    file_type: str  # dxf/brep/step/svg/...
    thumbnail_path: Optional[str]
    width_mm: Optional[float]
    height_mm: Optional[float]
    notes: Optional[str]

class ProfilesDB:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._ensure_schema()

    def _connect(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _ensure_schema(self):
        with self._connect() as c:
            c.execute("""
            CREATE TABLE IF NOT EXISTS profiles(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              code TEXT NOT NULL,
              file_path TEXT NOT NULL,
              file_type TEXT NOT NULL,
              thumbnail_path TEXT,
              width_mm REAL,
              height_mm REAL,
              notes TEXT,
              created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_profiles_code ON profiles(code)")
        print("✅ [ProfilesDB] schema ok")

    def add(self, item: ProfileItem) -> int:
        with self._connect() as c:
            cur = c.execute("""
              INSERT INTO profiles(name, code, file_path, file_type, thumbnail_path, width_mm, height_mm, notes)
              VALUES(?,?,?,?,?,?,?,?)
            """, (item.name, item.code, item.file_path, item.file_type, item.thumbnail_path,
                  item.width_mm, item.height_mm, item.notes))
            new_id = cur.lastrowid
        print(f"🟢 [ProfilesDB] added id={new_id} code={item.code}")
        return new_id

    def update_thumb_and_dims(self, pid: int, thumb: Optional[str], w: Optional[float], h: Optional[float]):
        with self._connect() as c:
            c.execute("UPDATE profiles SET thumbnail_path=?, width_mm=?, height_mm=? WHERE id=?",
                      (thumb, w, h, pid))
        print(f"🟡 [ProfilesDB] updated thumb/dims for id={pid}")

    def list_all(self) -> List[ProfileItem]:
        with self._connect() as c:
            rows = c.execute("SELECT id,name,code,file_path,file_type,thumbnail_path,width_mm,height_mm,notes FROM profiles ORDER BY created_at DESC").fetchall()
        return [ProfileItem(*r) for r in rows]

    def get(self, pid: int) -> Optional[ProfileItem]:
        with self._connect() as c:
            r = c.execute("SELECT id,name,code,file_path,file_type,thumbnail_path,width_mm,height_mm,notes FROM profiles WHERE id=?", (pid,)).fetchone()
        return ProfileItem(*r) if r else None

    def delete(self, pid: int):
        with self._connect() as c:
            c.execute("DELETE FROM profiles WHERE id=?", (pid,))
        print(f"🗑️ [ProfilesDB] deleted id={pid}")
