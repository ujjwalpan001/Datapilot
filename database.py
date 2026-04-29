"""Database module — SQLite persistence for chat sessions and messages."""

import os
import sqlite3
import json
import time
from datetime import datetime


DB_PATH = os.getenv("DB_PATH", "./datapilot.db")


def get_connection():
    """Get a SQLite connection with WAL mode for concurrency."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL DEFAULT 'New Session',
            filename TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            chart_url TEXT,
            chart_json TEXT,
            export_url TEXT,
            tool_calls TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()


def create_session(title: str = "New Session", filename: str = None) -> dict:
    """Create a new chat session."""
    import uuid
    session_id = str(uuid.uuid4())[:8]
    now = datetime.utcnow().isoformat()

    conn = get_connection()
    conn.execute(
        "INSERT INTO sessions (id, title, filename, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, title, filename, now, now),
    )
    conn.commit()
    conn.close()

    return {"id": session_id, "title": title, "filename": filename, "created_at": now}


def list_sessions() -> list:
    """List all sessions ordered by most recent."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, title, filename, created_at, updated_at FROM sessions ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_session(session_id: str) -> dict | None:
    """Get a specific session by ID."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, title, filename, created_at, updated_at FROM sessions WHERE id = ?",
        (session_id,),
    ).fetchone()
    conn.close()

    return dict(row) if row else None


def update_session(session_id: str, title: str = None, filename: str = None):
    """Update a session's title or filename."""
    conn = get_connection()
    now = datetime.utcnow().isoformat()

    if title:
        conn.execute("UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?", (title, now, session_id))
    if filename:
        conn.execute("UPDATE sessions SET filename = ?, updated_at = ? WHERE id = ?", (filename, now, session_id))

    conn.commit()
    conn.close()


def delete_session(session_id: str):
    """Delete a session and all its messages."""
    conn = get_connection()
    conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def save_message(
    session_id: str,
    role: str,
    content: str,
    chart_url: str = None,
    chart_json: str = None,
    export_url: str = None,
    tool_calls: list = None,
) -> dict:
    """Save a message to a session."""
    now = datetime.utcnow().isoformat()
    tool_calls_json = json.dumps(tool_calls) if tool_calls else None

    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO messages (session_id, role, content, chart_url, chart_json, export_url, tool_calls, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (session_id, role, content, chart_url, chart_json, export_url, tool_calls_json, now),
    )
    msg_id = cursor.lastrowid

    # Update session timestamp
    conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
    conn.commit()
    conn.close()

    return {
        "id": msg_id,
        "session_id": session_id,
        "role": role,
        "content": content,
        "chart_url": chart_url,
        "export_url": export_url,
        "created_at": now,
    }


def get_session_messages(session_id: str) -> list:
    """Get all messages for a session."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, session_id, role, content, chart_url, chart_json, export_url, tool_calls, created_at
           FROM messages WHERE session_id = ? ORDER BY created_at ASC""",
        (session_id,),
    ).fetchall()
    conn.close()

    messages = []
    for row in rows:
        msg = dict(row)
        if msg["tool_calls"]:
            msg["tool_calls"] = json.loads(msg["tool_calls"])
        messages.append(msg)

    return messages


# Initialize DB on import
init_db()
