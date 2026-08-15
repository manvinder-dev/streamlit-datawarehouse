"""
Seed script — inserts 3 test users with realistic CRM data.

Safe to run multiple times (skips if already seeded by checking contacts count).

Test accounts:
  username: alice   password: Demo1234!
  username: bob     password: Demo1234!
  username: carol   password: Demo1234!
"""

import bcrypt
from datetime import date, timedelta
from database.connection import get_connection, execute, fetchone, fetchall, is_postgres


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


USERS = [
    ("alice",  "alice@example.com",  "Demo1234!", "Alice Johnson"),
    ("bob",    "bob@example.com",    "Demo1234!", "Bob Chen"),
    ("carol",  "carol@example.com",  "Demo1234!", "Carol Davis"),
]

ALICE_CONTACTS = [
    ("Priya Sharma",    "priya@novacorp.com",     "+1 415-001-0001", "Nova Corp",      "Customer"),
    ("James Okafor",    "james@brightwave.io",    "+1 415-001-0002", "Bright Wave",    "Lead"),
    ("Sofia Reyes",     "sofia@meridiantech.com", "+1 415-001-0003", "Meridian Tech",  "Prospect"),
    ("Liam Nakamura",   "liam@alpharise.co",      "+1 415-001-0004", "Alpha Rise",     "Customer"),
    ("Amara Diallo",    "amara@sunbridgeco.com",  "+1 415-001-0005", "Sunbridge Co",   "Lead"),
    ("Ethan Kowalski",  "ethan@ironvault.net",    "+1 415-001-0006", "Iron Vault",     "Prospect"),
    ("Fatima Hassan",   "fatima@cellulink.com",   "+1 415-001-0007", "Cellu Link",     "Customer"),
    ("Noah Bergstrom",  "noah@pinnacleai.io",     "+1 415-001-0008", "Pinnacle AI",    "Lead"),
    ("Isabella Torres", "isa@stratumsoft.com",    "+1 415-001-0009", "Stratum Soft",   "Prospect"),
    ("Marcus Adeyemi",  "marcus@clearpath.io",    "+1 415-001-0010", "Clear Path",     "Customer"),
    ("Yuki Tanaka",     "yuki@nexuslab.co",       "+1 415-001-0011", "Nexus Lab",      "Lead"),
    ("Chloe Moreau",    "chloe@verticalsys.fr",   "+1 415-001-0012", "Vertical Sys",   "Prospect"),
]

BOB_CONTACTS = [
    ("Daniel Owusu",   "daniel@redrock.co",     "+44 20-001-0001", "Red Rock Co",  "Customer"),
    ("Mei Lin",        "mei@crystaldata.ai",    "+44 20-001-0002", "Crystal Data", "Prospect"),
    ("Tariq Hussain",  "tariq@peakforce.io",    "+44 20-001-0003", "Peak Force",   "Lead"),
    ("Zara Johnson",   "zara@brightedge.co.uk", "+44 20-001-0004", "Bright Edge",  "Customer"),
    ("Leon Dubois",    "leon@vanguardnet.eu",   "+44 20-001-0005", "Vanguard Net", "Prospect"),
    ("Anika Patel",    "anika@solarpulse.in",   "+44 20-001-0006", "Solar Pulse",  "Lead"),
    ("Oscar Lindqvist","oscar@nordicsys.se",    "+44 20-001-0007", "Nordic Sys",   "Customer"),
]


def _upsert_user(conn, username, email, password, full_name) -> int:
    """Insert user if not exists. Return user id."""
    row = fetchone(conn, "SELECT id FROM users WHERE username = ?", (username,))
    if row:
        return row["id"]
    pw_hash = _hash(password)
    execute(conn, """
        INSERT INTO users (username, email, password_hash, full_name)
        VALUES (?, ?, ?, ?)
    """, (username, email, pw_hash, full_name))
    conn.commit()
    row = fetchone(conn, "SELECT id FROM users WHERE username = ?", (username,))
    return row["id"]


def _insert_contact(conn, user_id, name, email, phone, company, status) -> int:
    execute(conn, """
        INSERT INTO contacts (user_id, name, email, phone, company, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, name, email, phone, company, status))
    conn.commit()
    row = fetchone(conn, """
        SELECT id FROM contacts
        WHERE user_id = ? AND name = ? AND email = ?
        ORDER BY id DESC LIMIT 1
    """, (user_id, name, email))
    return row["id"]


def _insert_deal(conn, user_id, contact_id, title, value, stage, days_offset) -> int:
    close = (date.today() + timedelta(days=days_offset)).isoformat()
    execute(conn, """
        INSERT INTO deals (user_id, contact_id, title, value, stage, close_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, contact_id, title, value, stage, close))
    conn.commit()
    row = fetchone(conn, """
        SELECT id FROM deals
        WHERE user_id = ? AND title = ?
        ORDER BY id DESC LIMIT 1
    """, (user_id, title))
    return row["id"]


def _insert_activity(conn, user_id, contact_id, deal_id, atype, subject, days_offset, completed):
    due = (date.today() + timedelta(days=days_offset)).isoformat()
    execute(conn, """
        INSERT INTO activities (user_id, contact_id, deal_id, type, subject, due_date, completed)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, contact_id, deal_id, atype, subject, due, 1 if completed else 0))
    conn.commit()


def seed_data() -> None:
    conn = get_connection()
    try:
        # ── Upsert users ───────────────────────────────────────────────────────
        alice_id = _upsert_user(conn, *USERS[0])
        bob_id   = _upsert_user(conn, *USERS[1])
        _upsert_user(conn, *USERS[2])  # Carol — empty account

        # ── Skip if already seeded ──────────────────────────────────────────
        if fetchall(conn, "SELECT id FROM contacts WHERE user_id = ? LIMIT 1", (alice_id,)):
            return

        # ── Alice's contacts ─────────────────────────────────────────────────
        ac = []
        for c in ALICE_CONTACTS:
            ac.append(_insert_contact(conn, alice_id, *c))

        # ── Alice's deals ────────────────────────────────────────────────────
        d1 = _insert_deal(conn, alice_id, ac[0],  "Nova Corp Enterprise Licence",  48000, "Proposal",   30)
        d2 = _insert_deal(conn, alice_id, ac[3],  "Alpha Rise Expansion Pack",      22000, "Won",        -5)
        d3 = _insert_deal(conn, alice_id, ac[2],  "Meridian Platform Onboarding",   15000, "Qualified",  45)
        d4 = _insert_deal(conn, alice_id, ac[6],  "Cellu Link Annual Renewal",      31000, "Won",        -10)
        d5 = _insert_deal(conn, alice_id, ac[9],  "Clear Path Starter Deal",         9500, "Prospect",   60)
        _insert_deal(conn, alice_id, ac[1],  "Bright Wave Pilot",               5500, "Lost",       -20)

        # ── Alice's activities ───────────────────────────────────────────────
        _insert_activity(conn, alice_id, ac[0], d1, "Call",    "Discovery call re: pricing",      -2,  True)
        _insert_activity(conn, alice_id, ac[0], d1, "Email",   "Send proposal deck",               1,  False)
        _insert_activity(conn, alice_id, ac[3], d2, "Meeting", "Contract signing meeting",         -5,  True)
        _insert_activity(conn, alice_id, ac[2], d3, "Call",    "Follow-up on demo feedback",        3,  False)
        _insert_activity(conn, alice_id, ac[6], d4, "Email",   "Renewal confirmation email",       -10, True)
        _insert_activity(conn, alice_id, ac[9], d5, "Meeting", "Initial intro meeting",             7,  False)
        _insert_activity(conn, alice_id, ac[7], None,"Email",  "Welcome email to new lead",        -1,  True)
        _insert_activity(conn, alice_id, ac[4], None,"Call",   "Qualify budget and timeline",       5,  False)

        # ── Bob's contacts ───────────────────────────────────────────────────
        bc = []
        for c in BOB_CONTACTS:
            bc.append(_insert_contact(conn, bob_id, *c))

        # ── Bob's deals ──────────────────────────────────────────────────────
        b1 = _insert_deal(conn, bob_id, bc[0], "Red Rock Infrastructure Deal",  72000, "Proposal",  20)
        b2 = _insert_deal(conn, bob_id, bc[3], "Bright Edge Cloud Migration",    38000, "Won",       -3)
        b3 = _insert_deal(conn, bob_id, bc[1], "Crystal Data Analytics Suite",  19500, "Qualified", 35)
        b4 = _insert_deal(conn, bob_id, bc[6], "Nordic Sys Consulting",           8000, "Prospect",  50)

        # ── Bob's activities ─────────────────────────────────────────────────
        _insert_activity(conn, bob_id, bc[0], b1, "Meeting", "Exec presentation",               2, False)
        _insert_activity(conn, bob_id, bc[3], b2, "Call",    "Post-close check-in",            -3, True)
        _insert_activity(conn, bob_id, bc[1], b3, "Email",   "Technical requirements document", 4, False)
        _insert_activity(conn, bob_id, bc[6], b4, "Call",    "Scope discussion",                6, False)
        _insert_activity(conn, bob_id, bc[2], None,"Email",  "Intro and capabilities overview",-1, True)

    finally:
        conn.close()
