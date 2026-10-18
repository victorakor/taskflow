"""Tiny SQLite layer (one short-lived connection per call, thread-safe)."""
import sqlite3
import threading
from contextlib import contextmanager

from core.config import DATA_DIR, DB_PATH

_lock = threading.RLock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
  pw_hash TEXT, pw_salt TEXT, avatar BLOB, avatar_url TEXT,
  avatar_pref TEXT DEFAULT 'auto', settings TEXT DEFAULT '{}', created_at TEXT);
CREATE TABLE IF NOT EXISTS sessions(
  token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS categories(
  id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL, color TEXT DEFAULT '#6366f1', icon TEXT DEFAULT '📁',
  UNIQUE(user_id, name COLLATE NOCASE));
CREATE TABLE IF NOT EXISTS tasks(
  id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL, description TEXT DEFAULT '',
  category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
  priority INTEGER DEFAULT 2, start_at TEXT, end_at TEXT, completed_at TEXT,
  remind_mode TEXT DEFAULT 'none', remind_start INTEGER DEFAULT 1, remind_end INTEGER DEFAULT 1,
  remind_before INTEGER DEFAULT 0, recurrence TEXT DEFAULT 'none',
  email_start_sent INTEGER DEFAULT 0, email_end_sent INTEGER DEFAULT 0,
  ring_start_done INTEGER DEFAULT 0, ring_end_done INTEGER DEFAULT 0, snooze_until TEXT,
  created_at TEXT, updated_at TEXT);
CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id, completed_at);
CREATE TABLE IF NOT EXISTS notes(
  id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL, body TEXT DEFAULT '',
  category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
  pinned INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT);
CREATE TABLE IF NOT EXISTS focus_log(
  id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  task_id INTEGER, minutes INTEGER NOT NULL, ended_at TEXT NOT NULL);
"""


@contextmanager
def tx():
    with _lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()


def query(sql, args=()):
    with tx() as con:
        return [dict(r) for r in con.execute(sql, args).fetchall()]


def one(sql, args=()):
    rows = query(sql, args)
    return rows[0] if rows else None


def execute(sql, args=()):
    with tx() as con:
        return con.execute(sql, args).lastrowid


def init():
    with tx() as con:
        con.execute("PRAGMA journal_mode=WAL")
        con.executescript(SCHEMA)
