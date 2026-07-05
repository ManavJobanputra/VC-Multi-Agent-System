import os
import sqlite3
from contextlib import contextmanager

# SQLite for now - simplest thing that works locally. NOTE: this has the
# exact same problem embedded Chroma had before the Pinecone migration -
# local disk doesn't survive deployment to platforms with ephemeral
# filesystems or multiple instances. Before taking real payments in
# production, this needs to move to a hosted Postgres (Supabase/Neon free
# tier are the natural fits) so paid users never lose their credits on a
# redeploy. Fine for local development and testing the flow end-to-end now.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'app.db')


@contextmanager
def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                free_session_used INTEGER NOT NULL DEFAULT 0,
                credits INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS magic_link_tokens (
                token TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
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
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
