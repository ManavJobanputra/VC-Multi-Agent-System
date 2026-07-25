import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras

# Hosted Postgres (Neon/Supabase free tier) - survives redeploys and works
# across multiple instances, unlike the SQLite file this used to be.
DATABASE_URL = os.environ["DATABASE_URL"]


class _ConnWrapper:
    """Thin shim so callers can keep using sqlite3's conn.execute(sql, params)
    -> cursor pattern against a real psycopg2 connection."""

    def __init__(self, pg_conn):
        self._conn = pg_conn

    def execute(self, sql, params=()):
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql.replace("?", "%s"), params)
        return cur


@contextmanager
def get_conn():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        wrapper = _ConnWrapper(conn)
        yield wrapper
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        # One-time cleanup: magic-link sign-in was replaced by password auth
        # and this table was never read from again - drop the leftover.
        conn.execute("DROP TABLE IF EXISTS magic_link_tokens")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                password_hash TEXT,
                free_session_used INTEGER NOT NULL DEFAULT 0,
                credits INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                token TEXT PRIMARY KEY,
                email TEXT NOT NULL REFERENCES users(email),
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_email ON user_sessions(email)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_sessions (
                token TEXT PRIMARY KEY,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                razorpay_order_id TEXT NOT NULL,
                razorpay_payment_id TEXT,
                pack TEXT NOT NULL,
                amount_inr INTEGER NOT NULL,
                credits_granted INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'created',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_email TEXT NOT NULL,
                company_name TEXT,
                industry TEXT,
                stage TEXT,
                persona_id TEXT,
                persona_name TEXT,
                pitch_data TEXT,
                analysis TEXT,
                investment_score INTEGER,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS session_messages (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES sessions(session_id),
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_email ON sessions(user_email)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_session_messages_session_id ON session_messages(session_id)")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_payments_razorpay_order_id ON payments(razorpay_order_id)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS progress_reports (
                user_email TEXT PRIMARY KEY,
                report_json TEXT NOT NULL,
                session_count INTEGER NOT NULL,
                generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
