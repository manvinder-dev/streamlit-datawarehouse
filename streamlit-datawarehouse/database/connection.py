"""
Database connection factory.

Returns a SQLite connection in local development and a PostgreSQL
connection on Streamlit Community Cloud (when secrets.database.postgres_url
is set).

All connections use the same API surface (via sqlite3 / psycopg2) so the
rest of the app stays database-agnostic. A thin adapter normalises the
minor dialect differences (placeholder style, AUTOINCREMENT vs SERIAL).

Note: streamlit is imported lazily so this module can be imported outside
of a running Streamlit app (e.g., for CLI verification scripts).
"""

import sqlite3
import os


def _get_postgres_url() -> str | None:
    """Return the PostgreSQL URL from Streamlit secrets or env var, or None."""
    # Check environment variable first (useful for non-Streamlit runners)
    env_url = os.environ.get("POSTGRES_URL", "")
    if env_url:
        return env_url

    # Try Streamlit secrets
    try:
        import streamlit as st
        url = st.secrets["database"].get("postgres_url", "")
        return url if url else None
    except Exception:
        return None


def _get_sqlite_path() -> str:
    """Return the SQLite database file path."""
    env_path = os.environ.get("SQLITE_PATH", "")
    if env_path:
        return env_path
    try:
        import streamlit as st
        return st.secrets["database"].get("sqlite_path", "crm_local.db")
    except Exception:
        return "crm_local.db"


def is_postgres() -> bool:
    """True when running against PostgreSQL (production)."""
    return _get_postgres_url() is not None


def get_connection():
    """
    Return an open database connection.

    Callers are responsible for closing the connection (or using it as a
    context manager where supported).
    """
    pg_url = _get_postgres_url()
    if pg_url:
        import psycopg2
        conn = psycopg2.connect(pg_url)
        conn.autocommit = False
        return conn
    else:
        path = _get_sqlite_path()
        conn = sqlite3.connect(path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn


def placeholder() -> str:
    """Return the SQL placeholder for the active backend (%s or ?)."""
    return "%s" if is_postgres() else "?"


def execute(conn, sql: str, params: tuple = ()):
    """
    Execute a single statement, normalising placeholders automatically.

    Always use '?' in the SQL you write — this function rewrites to '%s'
    when running against PostgreSQL.
    """
    if is_postgres():
        sql = sql.replace("?", "%s")
    cur = conn.cursor()
    cur.execute(sql, params)
    return cur


def executemany(conn, sql: str, params_list):
    """Execute a statement for each set of params."""
    if is_postgres():
        sql = sql.replace("?", "%s")
    cur = conn.cursor()
    cur.executemany(sql, params_list)
    return cur


def fetchall(conn, sql: str, params: tuple = ()) -> list[dict]:
    """Execute a SELECT and return rows as a list of dicts."""
    if is_postgres():
        sql = sql.replace("?", "%s")
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    return [dict(r) for r in rows]


def fetchone(conn, sql: str, params: tuple = ()) -> dict | None:
    """Execute a SELECT and return the first row as a dict, or None."""
    if is_postgres():
        sql = sql.replace("?", "%s")
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    if row is None:
        return None
    return dict(row)
