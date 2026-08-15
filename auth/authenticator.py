"""
Authentication module.

Provides login, registration, logout, and session management.
Passwords are hashed with bcrypt. Data isolation is enforced at the
SQL layer by always filtering on the authenticated user_id.
"""

import bcrypt
import streamlit as st
import re
from database.connection import get_connection, fetchone, execute


# ─── Session State Keys ───────────────────────────────────────────────────────

_KEY_AUTH   = "auth_authenticated"
_KEY_UID    = "auth_user_id"
_KEY_UNAME  = "auth_username"
_KEY_NAME   = "auth_full_name"
_KEY_EMAIL  = "auth_email"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def _validate_password_strength(password: str) -> list[str]:
    """Return a list of validation errors (empty = valid)."""
    errors = []
    if len(password) < 8:
        errors.append("At least 8 characters required.")
    if not re.search(r"[A-Z]", password):
        errors.append("At least one uppercase letter required.")
    if not re.search(r"[0-9]", password):
        errors.append("At least one digit required.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("At least one special character required.")
    return errors


def _validate_email(email: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email))


# ─── Public API ───────────────────────────────────────────────────────────────

def is_authenticated() -> bool:
    return st.session_state.get(_KEY_AUTH, False)


def current_user() -> dict | None:
    """Return a dict with id, username, full_name, email — or None."""
    if not is_authenticated():
        return None
    return {
        "id":        st.session_state[_KEY_UID],
        "username":  st.session_state[_KEY_UNAME],
        "full_name": st.session_state[_KEY_NAME],
        "email":     st.session_state[_KEY_EMAIL],
    }


def current_user_id() -> int | None:
    return st.session_state.get(_KEY_UID)


def login(username: str, password: str) -> tuple[bool, str]:
    """
    Attempt login. Returns (success, error_message).
    On success, sets session state.
    """
    username = username.strip().lower()
    if not username or not password:
        return False, "Please enter both username and password."

    conn = get_connection()
    try:
        row = fetchone(conn, "SELECT * FROM users WHERE username = ?", (username,))
    finally:
        conn.close()

    if not row:
        return False, "Invalid username or password."
    if not _verify_password(password, row["password_hash"]):
        return False, "Invalid username or password."

    st.session_state[_KEY_AUTH]  = True
    st.session_state[_KEY_UID]   = row["id"]
    st.session_state[_KEY_UNAME] = row["username"]
    st.session_state[_KEY_NAME]  = row["full_name"]
    st.session_state[_KEY_EMAIL] = row["email"]
    return True, ""


def register(
    username: str,
    email: str,
    password: str,
    confirm_password: str,
    full_name: str,
) -> tuple[bool, str]:
    """
    Register a new user. Returns (success, message).
    """
    username  = username.strip().lower()
    email     = email.strip().lower()
    full_name = full_name.strip()

    if not all([username, email, password, confirm_password, full_name]):
        return False, "All fields are required."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if not re.match(r"^[a-z0-9_]+$", username):
        return False, "Username may only contain lowercase letters, digits, and underscores."
    if not _validate_email(email):
        return False, "Please enter a valid email address."
    if password != confirm_password:
        return False, "Passwords do not match."

    pw_errors = _validate_password_strength(password)
    if pw_errors:
        return False, " ".join(pw_errors)

    conn = get_connection()
    try:
        if fetchone(conn, "SELECT id FROM users WHERE username = ?", (username,)):
            return False, "Username is already taken."
        if fetchone(conn, "SELECT id FROM users WHERE email = ?", (email,)):
            return False, "An account with that email address already exists."

        pw_hash = _hash_password(password)
        execute(conn, """
            INSERT INTO users (username, email, password_hash, full_name)
            VALUES (?, ?, ?, ?)
        """, (username, email, pw_hash, full_name))
        conn.commit()
    finally:
        conn.close()

    return True, "Account created successfully. You can now log in."


def logout() -> None:
    """Clear all auth-related session state keys."""
    for key in [_KEY_AUTH, _KEY_UID, _KEY_UNAME, _KEY_NAME, _KEY_EMAIL]:
        st.session_state.pop(key, None)


def change_password(
    user_id: int,
    current_password: str,
    new_password: str,
    confirm_new_password: str,
) -> tuple[bool, str]:
    """
    Change a user's password. Returns (success, message).
    """
    if not all([current_password, new_password, confirm_new_password]):
        return False, "All fields are required."
    if new_password != confirm_new_password:
        return False, "New passwords do not match."

    pw_errors = _validate_password_strength(new_password)
    if pw_errors:
        return False, " ".join(pw_errors)

    conn = get_connection()
    try:
        row = fetchone(conn, "SELECT password_hash FROM users WHERE id = ?", (user_id,))
        if not row or not _verify_password(current_password, row["password_hash"]):
            return False, "Current password is incorrect."

        new_hash = _hash_password(new_password)
        execute(conn, "UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
        conn.commit()
    finally:
        conn.close()

    return True, "Password updated successfully."


def update_profile(
    user_id: int,
    full_name: str,
    email: str,
) -> tuple[bool, str]:
    """Update display name and email."""
    full_name = full_name.strip()
    email     = email.strip().lower()

    if not full_name:
        return False, "Display name cannot be empty."
    if not _validate_email(email):
        return False, "Please enter a valid email address."

    conn = get_connection()
    try:
        conflict = fetchone(
            conn,
            "SELECT id FROM users WHERE email = ? AND id != ?",
            (email, user_id),
        )
        if conflict:
            return False, "That email address is already in use by another account."

        execute(conn, """
            UPDATE users SET full_name = ?, email = ? WHERE id = ?
        """, (full_name, email, user_id))
        conn.commit()
    finally:
        conn.close()

    # Refresh session state
    st.session_state[_KEY_NAME]  = full_name
    st.session_state[_KEY_EMAIL] = email
    return True, "Profile updated successfully."


def require_auth() -> bool:
    """
    Guard function — call at the top of every protected page.
    Returns True if authenticated; if not, shows a redirect notice and
    returns False (caller should st.stop()).
    """
    if is_authenticated():
        return True
    st.error("Please log in to access this page.")
    st.markdown("[Go to Login](/) ")
    return False
