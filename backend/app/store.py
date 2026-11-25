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

    def create_thread(self, title: str, focus: str) -> str:
        tid = uuid.uuid4().hex[:16]
        now = time.time()
        with self._lock:
            self._db.execute("INSERT INTO threads VALUES (?,?,?,?,?)", (tid, title[:120], focus, now, now))
            self._db.commit()
        return tid

    def exists(self, tid: str) -> bool:
        return self._db.execute("SELECT 1 FROM threads WHERE id=?", (tid,)).fetchone() is not None

    def add_turn(self, tid: str, question: str, answer: str, sources: list, followups: list, meta: dict) -> None:
        now = time.time()
        with self._lock:
            self._db.execute(
                "INSERT INTO turns(thread_id,question,answer,sources,followups,meta,created_at) VALUES (?,?,?,?,?,?,?)",
                (tid, question, answer, json.dumps(sources), json.dumps(followups), json.dumps(meta), now))
            self._db.execute("UPDATE threads SET updated_at=? WHERE id=?", (now, tid))
            self._db.commit()

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
