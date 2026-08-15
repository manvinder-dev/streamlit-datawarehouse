"""
Contacts Page — LeadTrack

Full CRUD for contacts. All records are isolated to the authenticated user.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from auth.authenticator  import require_auth, current_user_id
from components.sidebar  import render_sidebar
from database.connection import get_connection, fetchall, fetchone, execute

if not require_auth():
    st.stop()

render_sidebar()

# ── Shared CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
#MainMenu, footer { visibility: hidden; }
section[data-testid="stSidebar"] { background:#1A1D23 !important; border-right:1px solid #2D3139; }
section[data-testid="stSidebar"] * { color:rgba(255,255,255,0.75) !important; }
section[data-testid="stSidebar"] .stButton > button {
    background:rgba(255,255,255,0.06) !important;
    border:1px solid rgba(255,255,255,0.1) !important;
    color:rgba(255,255,255,0.7) !important;
    font-size:0.8rem !important;
    margin-top:0.5rem;
}
.page-title { font-size:1.5rem; font-weight:700; color:#0F172A; letter-spacing:-0.025em; }
.page-sub   { font-size:0.82rem; color:#64748B; margin-top:0.15rem; margin-bottom:1.5rem; }
.section-header {
    font-size:0.8rem; font-weight:600; color:#94A3B8;
    text-transform:uppercase; letter-spacing:0.08em;
    margin:1.25rem 0 0.75rem; padding-bottom:0.5rem;
    border-bottom:1px solid #E8EDF2;
}
.stDataFrame { border-radius:8px !important; }
</style>
""", unsafe_allow_html=True)

uid = current_user_id()

STATUS_OPTIONS = ["Lead", "Prospect", "Customer", "Churned"]

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_contacts(search: str = "", status_filter: str = "All") -> list[dict]:
    conn = get_connection()
    rows = fetchall(conn, "SELECT * FROM contacts WHERE user_id = ? ORDER BY created_at DESC", (uid,))
    conn.close()
    if search:
        s = search.lower()
        rows = [r for r in rows if
                s in (r["name"] or "").lower() or
                s in (r["email"] or "").lower() or
                s in (r["company"] or "").lower()]
    if status_filter != "All":
        rows = [r for r in rows if r["status"] == status_filter]
    return rows


def save_contact(name, email, phone, company, status, notes, contact_id=None):
    conn = get_connection()
    now  = datetime.utcnow().isoformat()
    if contact_id:
        execute(conn, """
            UPDATE contacts
            SET name=?, email=?, phone=?, company=?, status=?, notes=?, updated_at=?
            WHERE id=? AND user_id=?
        """, (name, email, phone, company, status, notes, now, contact_id, uid))
    else:
        execute(conn, """
            INSERT INTO contacts (user_id, name, email, phone, company, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (uid, name, email, phone, company, status, notes))
    conn.commit()
    conn.close()


def delete_contact(contact_id: int):
    conn = get_connection()
    execute(conn, "DELETE FROM contacts WHERE id=? AND user_id=?", (contact_id, uid))
    conn.commit()
    conn.close()


def get_contact(contact_id: int) -> dict | None:
    conn = get_connection()
    row  = fetchone(conn, "SELECT * FROM contacts WHERE id=? AND user_id=?", (contact_id, uid))
    conn.close()
    return row


# ── Session state initialisation ─────────────────────────────────────────────
if "contact_edit_id"   not in st.session_state: st.session_state.contact_edit_id   = None
if "contact_show_form" not in st.session_state: st.session_state.contact_show_form = False
if "contact_delete_id" not in st.session_state: st.session_state.contact_delete_id = None

# ── Page header ──────────────────────────────────────────────────────────────
header_left, header_right = st.columns([3, 1])
with header_left:
    st.markdown('<div class="page-title">Contacts</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Manage your contacts and relationships</div>', unsafe_allow_html=True)
with header_right:
    if st.button("+ Add Contact", type="primary", use_container_width=True):
        st.session_state.contact_show_form = True
        st.session_state.contact_edit_id   = None

# ── Filter bar ───────────────────────────────────────────────────────────────
f1, f2, f3 = st.columns([3, 1.5, 1])
with f1: search        = st.text_input("Search", placeholder="Name, email, or company...", label_visibility="collapsed")
with f2: status_filter = st.selectbox("Status", ["All"] + STATUS_OPTIONS, label_visibility="collapsed")
with f3: st.write("")

contacts = load_contacts(search, status_filter)

# ── Add / Edit form (inline panel) ────────────────────────────────────────────
if st.session_state.contact_show_form:
    edit_id = st.session_state.contact_edit_id
    editing = edit_id is not None
    row     = get_contact(edit_id) if editing else {}

    with st.expander("Contact Details" if editing else "New Contact", expanded=True):
        with st.form("contact_form"):
            fc1, fc2 = st.columns(2)
            with fc1:
                f_name    = st.text_input("Full Name *", value=row.get("name", ""))
                f_email   = st.text_input("Email",       value=row.get("email", ""))
                f_phone   = st.text_input("Phone",       value=row.get("phone", ""))
            with fc2:
                f_company = st.text_input("Company",     value=row.get("company", ""))
                f_status  = st.selectbox("Status",       STATUS_OPTIONS,
                                          index=STATUS_OPTIONS.index(row["status"])
                                          if row.get("status") in STATUS_OPTIONS else 0)
                f_notes   = st.text_area("Notes",        value=row.get("notes", ""), height=80)

            sb1, sb2, _ = st.columns([1, 1, 3])
            with sb1: submitted = st.form_submit_button("Save Contact",  type="primary", use_container_width=True)
            with sb2: cancelled = st.form_submit_button("Cancel",        use_container_width=True)

        if submitted:
            if not f_name.strip():
                st.error("Full name is required.")
            else:
                save_contact(f_name.strip(), f_email.strip(), f_phone.strip(),
                             f_company.strip(), f_status, f_notes.strip(),
                             edit_id if editing else None)
                st.success("Contact saved.")
                st.session_state.contact_show_form = False
                st.session_state.contact_edit_id   = None
                st.rerun()

        if cancelled:
            st.session_state.contact_show_form = False
            st.session_state.contact_edit_id   = None
            st.rerun()

# ── Delete confirmation ───────────────────────────────────────────────────────
if st.session_state.contact_delete_id:
    del_id  = st.session_state.contact_delete_id
    del_row = get_contact(del_id)
    if del_row:
        st.warning(f"Delete **{del_row['name']}**? This will also remove any linked deals and activities.")
        dc1, dc2, _ = st.columns([1, 1, 5])
        with dc1:
            if st.button("Confirm Delete", type="primary"):
                delete_contact(del_id)
                st.session_state.contact_delete_id = None
                st.success("Contact deleted.")
                st.rerun()
        with dc2:
            if st.button("Cancel"):
                st.session_state.contact_delete_id = None
                st.rerun()

# ── Contact table ─────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-header">{len(contacts)} Contact{"s" if len(contacts) != 1 else ""}</div>',
            unsafe_allow_html=True)

STATUS_BADGE = {
    "Lead":     ("F1F5F9", "475569"),
    "Prospect": ("DBEAFE", "1E40AF"),
    "Customer": ("DCFCE7", "166534"),
    "Churned":  ("FEE2E2", "991B1B"),
}

if not contacts:
    st.markdown(
        '<p style="color:#94A3B8;font-size:0.875rem;">No contacts found. Click "+ Add Contact" to create your first one.</p>',
        unsafe_allow_html=True,
    )
else:
    # Column headers
    hdr = st.columns([3, 2.5, 2, 2, 1.5, 1.5])
    for h, label in zip(hdr, ["Name", "Email", "Company", "Phone", "Status", "Actions"]):
        h.markdown(f'<div style="font-size:0.72rem;font-weight:600;text-transform:uppercase;'
                   f'letter-spacing:0.07em;color:#94A3B8;padding:0.5rem 0;">{label}</div>',
                   unsafe_allow_html=True)

    st.markdown('<hr style="margin:0 0 0.5rem;border:none;border-top:1px solid #E8EDF2;">', unsafe_allow_html=True)

    for c in contacts:
        bg, fg = STATUS_BADGE.get(c["status"], ("F1F5F9", "475569"))
        row_cols = st.columns([3, 2.5, 2, 2, 1.5, 1.5])

        row_cols[0].markdown(
            f'<div style="font-weight:500;font-size:0.875rem;color:#0F172A;padding:0.5rem 0;">{c["name"]}</div>',
            unsafe_allow_html=True)
        row_cols[1].markdown(
            f'<div style="font-size:0.8rem;color:#64748B;padding:0.5rem 0;">{c["email"] or "—"}</div>',
            unsafe_allow_html=True)
        row_cols[2].markdown(
            f'<div style="font-size:0.8rem;color:#64748B;padding:0.5rem 0;">{c["company"] or "—"}</div>',
            unsafe_allow_html=True)
        row_cols[3].markdown(
            f'<div style="font-size:0.8rem;color:#64748B;padding:0.5rem 0;">{c["phone"] or "—"}</div>',
            unsafe_allow_html=True)
        row_cols[4].markdown(
            f'<span style="display:inline-block;padding:0.2em 0.65em;border-radius:4px;'
            f'font-size:0.72rem;font-weight:500;background:#{bg};color:#{fg};margin-top:0.5rem;">'
            f'{c["status"]}</span>',
            unsafe_allow_html=True)

        with row_cols[5]:
            col_e, col_d = st.columns(2)
            with col_e:
                if st.button("Edit", key=f"edit_c_{c['id']}"):
                    st.session_state.contact_edit_id   = c["id"]
                    st.session_state.contact_show_form = True
                    st.rerun()
            with col_d:
                if st.button("Del", key=f"del_c_{c['id']}"):
                    st.session_state.contact_delete_id = c["id"]
                    st.rerun()

        st.markdown('<hr style="margin:0;border:none;border-top:1px solid #F1F5F9;">', unsafe_allow_html=True)
