"""SQLite persistence for conversation threads (search history)."""
from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS threads (
    id TEXT PRIMARY KEY, title TEXT NOT NULL, focus TEXT NOT NULL,
    created_at REAL NOT NULL, updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT, thread_id TEXT NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    question TEXT NOT NULL, answer TEXT NOT NULL, sources TEXT NOT NULL, followups TEXT NOT NULL,
    meta TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_turns_thread ON turns(thread_id);
"""


class ThreadStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        self._db.executescript(SCHEMA)
        cols = {r["name"] for r in self._db.execute("PRAGMA table_info(threads)")}
        if "lang" not in cols:   # migration: answer language chosen for the thread
            self._db.execute("ALTER TABLE threads ADD COLUMN lang TEXT")
            self._db.commit()

    def create_thread(self, title: str, focus: str, lang: str | None = None) -> str:
        tid = uuid.uuid4().hex[:16]
        now = time.time()
        with self._lock:
            self._db.execute("INSERT INTO threads(id,title,focus,created_at,updated_at,lang) VALUES (?,?,?,?,?,?)",
                             (tid, title[:120], focus, now, now, lang))
            self._db.commit()
        return tid

    def exists(self, tid: str) -> bool:
        return self._db.execute("SELECT 1 FROM threads WHERE id=?", (tid,)).fetchone() is not None

    def get_lang(self, tid: str) -> str | None:
        r = self._db.execute("SELECT lang FROM threads WHERE id=?", (tid,)).fetchone()
        return r["lang"] if r else None

    def set_lang(self, tid: str, lang: str) -> None:
        with self._lock:
            self._db.execute("UPDATE threads SET lang=? WHERE id=?", (lang, tid))
            self._db.commit()

    def get_turn(self, turn_id: int) -> dict | None:
        r = self._db.execute("SELECT * FROM turns WHERE id=?", (turn_id,)).fetchone()
        return dict(r) | {"sources": json.loads(r["sources"]), "meta": json.loads(r["meta"])} if r else None

    def save_translation(self, turn_id: int, lang: str, text: str) -> None:
        """Cache a turn's answer rendered in another language (meta.translations[lang])."""
        with self._lock:
            r = self._db.execute("SELECT meta FROM turns WHERE id=?", (turn_id,)).fetchone()
            if not r:
                return
            meta = json.loads(r["meta"])
            meta.setdefault("translations", {})[lang] = text
            meta["shown_lang"] = lang
            self._db.execute("UPDATE turns SET meta=? WHERE id=?", (json.dumps(meta), turn_id))
            self._db.commit()

    def add_turn(self, tid: str, question: str, answer: str, sources: list, followups: list, meta: dict) -> int:
        now = time.time()
        with self._lock:
            cur = self._db.execute(
                "INSERT INTO turns(thread_id,question,answer,sources,followups,meta,created_at) VALUES (?,?,?,?,?,?,?)",
                (tid, question, answer, json.dumps(sources), json.dumps(followups), json.dumps(meta), now))
            self._db.execute("UPDATE threads SET updated_at=? WHERE id=?", (now, tid))
            self._db.commit()
        return cur.lastrowid

    def history(self, tid: str, last: int = 3) -> list[dict]:
        rows = self._db.execute(
            "SELECT question, answer FROM turns WHERE thread_id=? ORDER BY id DESC LIMIT ?", (tid, last)).fetchall()
        return [dict(r) for r in reversed(rows)]

    def list_threads(self, limit: int = 50) -> list[dict]:
        rows = self._db.execute("SELECT * FROM threads ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def get_thread(self, tid: str) -> dict | None:
        t = self._db.execute("SELECT * FROM threads WHERE id=?", (tid,)).fetchone()
        if not t:
            return None
        turns = self._db.execute("SELECT * FROM turns WHERE thread_id=? ORDER BY id", (tid,)).fetchall()
        return dict(t) | {"turns": [
            dict(r) | {"sources": json.loads(r["sources"]), "followups": json.loads(r["followups"]),
                       "meta": json.loads(r["meta"])} for r in turns]}

    def delete_thread(self, tid: str) -> bool:
        with self._lock:
            cur = self._db.execute("DELETE FROM threads WHERE id=?", (tid,))
            self._db.commit()
        return cur.rowcount > 0
