"""
Database schema creation.

Run this once on startup (idempotent — uses CREATE TABLE IF NOT EXISTS).
Works for both SQLite and PostgreSQL.
"""

from database.connection import get_connection, is_postgres


def _autoincrement() -> str:
    """Return the right auto-increment syntax for the active backend."""
    return "SERIAL PRIMARY KEY" if is_postgres() else "INTEGER PRIMARY KEY AUTOINCREMENT"


def create_tables() -> None:
    """Create all CRM tables if they do not already exist."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        ai = _autoincrement()

        # ── Users ────────────────────────────────────────────────────────────
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS users (
                id          {ai},
                username    TEXT NOT NULL UNIQUE,
                email       TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name   TEXT NOT NULL,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── Contacts ─────────────────────────────────────────────────────────
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS contacts (
                id          {ai},
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name        TEXT NOT NULL,
                email       TEXT,
                phone       TEXT,
                company     TEXT,
                status      TEXT DEFAULT 'Lead',
                notes       TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── Deals ────────────────────────────────────────────────────────────
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS deals (
                id          {ai},
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                contact_id  INTEGER REFERENCES contacts(id) ON DELETE SET NULL,
                title       TEXT NOT NULL,
                value       REAL DEFAULT 0,
                stage       TEXT DEFAULT 'Prospect',
                close_date  DATE,
                notes       TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── Activities ───────────────────────────────────────────────────────
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS activities (
                id          {ai},
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                contact_id  INTEGER REFERENCES contacts(id) ON DELETE SET NULL,
                deal_id     INTEGER REFERENCES deals(id) ON DELETE SET NULL,
                type        TEXT NOT NULL DEFAULT 'Call',
                subject     TEXT NOT NULL,
                due_date    DATE,
                completed   INTEGER DEFAULT 0,
                notes       TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── Indices (skip on conflict — idempotent) ───────────────────────────
        index_stmts = [
            "CREATE INDEX IF NOT EXISTS idx_contacts_user ON contacts(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_deals_user    ON deals(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_activities_user ON activities(user_id)",
        ]
        for stmt in index_stmts:
            cur.execute(stmt)

        conn.commit()
    finally:
        conn.close()
