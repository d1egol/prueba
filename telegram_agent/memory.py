"""
Persistencia de conversaciones en SQLite.

- Historial sobrevive reinicios (fix #1)
- Ventana deslizante CONTEXT_WINDOW mensajes (fix #2)
- Acceso async via asyncio.to_thread (no bloquea event loop)
"""

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).parent / "conversations.db"


# ─── Inicialización ────────────────────────────────────────────────────────────

def _init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT    NOT NULL,
            role       TEXT    NOT NULL,
            content    TEXT    NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_session ON messages(session_id, id)"
    )
    conn.commit()
    conn.close()


_init_db()


# ─── Operaciones síncronas (se ejecutan en thread pool) ───────────────────────

def _get_history_sync(session_id: str, limit: int) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            """SELECT role, content FROM messages
               WHERE session_id = ?
               ORDER BY id DESC LIMIT ?""",
            (session_id, limit),
        ).fetchall()
        # Revertir para orden cronológico
        return [{"role": r, "content": json.loads(c)} for r, c in reversed(rows)]
    finally:
        conn.close()


def _add_message_sync(session_id: str, role: str, content: Any) -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, json.dumps(content, default=str)),
        )
        conn.commit()
    finally:
        conn.close()


def _clear_history_sync(session_id: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.commit()
    finally:
        conn.close()


def _get_stats_sync() -> dict:
    conn = sqlite3.connect(DB_PATH)
    try:
        sessions = conn.execute(
            "SELECT COUNT(DISTINCT session_id) FROM messages"
        ).fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        return {"active_sessions": sessions, "total_messages": total}
    finally:
        conn.close()


# ─── API async pública ─────────────────────────────────────────────────────────

async def get_history(session_id: str, limit: int = 40) -> list[dict]:
    """Retorna los últimos `limit` mensajes en orden cronológico."""
    return await asyncio.to_thread(_get_history_sync, session_id, limit)


async def add_message(session_id: str, role: str, content: Any) -> None:
    """Persiste un mensaje en la base de datos."""
    await asyncio.to_thread(_add_message_sync, session_id, role, content)


async def clear_history(session_id: str) -> None:
    """Borra todo el historial de una sesión."""
    await asyncio.to_thread(_clear_history_sync, session_id)


async def get_stats() -> dict:
    """Retorna estadísticas globales (sesiones activas, mensajes totales)."""
    return await asyncio.to_thread(_get_stats_sync)
