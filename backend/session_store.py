import json
from typing import Any, Dict, List, Optional

from db import get_conn


def create_session(session_id: str, user_email: str, pitch_data: Dict[str, Any], persona: Optional[Dict[str, Any]]) -> None:
    persona = persona or {}
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO sessions (
                session_id, user_email, company_name, industry, stage,
                persona_id, persona_name, pitch_data, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """,
            (
                session_id,
                user_email,
                pitch_data.get("company_name") or pitch_data.get("companyName"),
                pitch_data.get("industry"),
                pitch_data.get("stage") or pitch_data.get("currentStage"),
                persona.get("id"),
                persona.get("name"),
                json.dumps(pitch_data),
            ),
        )


def owns_session(session_id: str, user_email: str) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM sessions WHERE session_id = ? AND user_email = ?",
            (session_id, user_email),
        ).fetchone()
        return row is not None


def add_message(session_id: str, role: str, content: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO session_messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )
        conn.execute(
            "UPDATE sessions SET updated_at = datetime('now') WHERE session_id = ?",
            (session_id,),
        )


def save_analysis(session_id: str, analysis: Dict[str, Any], investment_score: Optional[int]) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE sessions
            SET analysis = ?, investment_score = ?, status = 'completed', updated_at = datetime('now')
            WHERE session_id = ?
            """,
            (json.dumps(analysis), investment_score, session_id),
        )


def get_user_sessions(user_email: str) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT session_id, company_name, industry, stage, persona_name,
                   investment_score, status, created_at, updated_at
            FROM sessions
            WHERE user_email = ?
            ORDER BY created_at DESC
            """,
            (user_email,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_completed_sessions_for_progress(user_email: str) -> List[Dict[str, Any]]:
    """All completed (memo-generated) sessions for a user, oldest first, so
    a cross-session report can reason about improvement over time."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT session_id, company_name, industry, stage, persona_name,
                   pitch_data, analysis, investment_score, created_at
            FROM sessions
            WHERE user_email = ? AND status = 'completed' AND analysis IS NOT NULL
            ORDER BY created_at ASC
            """,
            (user_email,),
        ).fetchall()

        sessions = []
        for row in rows:
            session = dict(row)
            session["pitch_data"] = json.loads(session["pitch_data"]) if session["pitch_data"] else {}
            session["analysis"] = json.loads(session["analysis"]) if session["analysis"] else {}
            sessions.append(session)
        return sessions


def get_session_detail(session_id: str, user_email: str) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        session_row = conn.execute(
            "SELECT * FROM sessions WHERE session_id = ? AND user_email = ?",
            (session_id, user_email),
        ).fetchone()
        if session_row is None:
            return None

        message_rows = conn.execute(
            "SELECT role, content, created_at FROM session_messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()

        session = dict(session_row)
        session["pitch_data"] = json.loads(session["pitch_data"]) if session["pitch_data"] else None
        session["analysis"] = json.loads(session["analysis"]) if session["analysis"] else None
        session["messages"] = [dict(row) for row in message_rows]
        return session
