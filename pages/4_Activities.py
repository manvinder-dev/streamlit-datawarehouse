"""
Activities Page — LeadTrack

Log and manage calls, emails, meetings, and tasks.
All records isolated to the authenticated user.
"""

import streamlit as st
from datetime import datetime, date

from auth.authenticator  import require_auth, current_user_id
from components.sidebar  import render_sidebar
from database.connection import get_connection, fetchall, fetchone, execute

if not require_auth():
    st.stop()

render_sidebar()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
#MainMenu, footer { visibility: hidden; }
section[data-testid="stSidebar"] { background:#1A1D23 !important; border-right:1px solid #2D3139; }
section[data-testid="stSidebar"] * { color:rgba(255,255,255,0.75) !important; }
section[data-testid="stSidebar"] .stButton > button {
    background:rgba(255,255,255,0.06) !important; border:1px solid rgba(255,255,255,0.1) !important;
    color:rgba(255,255,255,0.7) !important; font-size:0.8rem !important; margin-top:0.5rem;
}
.page-title { font-size:1.5rem; font-weight:700; color:#0F172A; letter-spacing:-0.025em; }
.page-sub   { font-size:0.82rem; color:#64748B; margin-top:0.15rem; margin-bottom:1.5rem; }
.section-header {
    font-size:0.8rem; font-weight:600; color:#94A3B8;
    text-transform:uppercase; letter-spacing:0.08em;
    margin:1.25rem 0 0.75rem; padding-bottom:0.5rem;
    border-bottom:1px solid #E8EDF2;
}
</style>
""", unsafe_allow_html=True)

uid = current_user_id()
ACTIVITY_TYPES = ["Call", "Email", "Meeting", "Task"]
TYPE_COLORS = {
    "Call":    ("#DBEAFE", "#1E40AF", "C"),
    "Email":   ("#FCE7F3", "#9D174D", "E"),
    "Meeting": ("#FEF3C7", "#92400E", "M"),
    "Task":    ("#F0FDF4", "#166534", "T"),
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_activities(type_filter="All", status_filter="All", search="") -> list[dict]:
    conn = get_connection()
    rows = fetchall(conn, """
        SELECT a.*, c.name AS contact_name, d.title AS deal_title
        FROM activities a
        LEFT JOIN contacts c ON a.contact_id = c.id
        LEFT JOIN deals    d ON a.deal_id    = d.id
        WHERE a.user_id = ?
        ORDER BY a.due_date ASC, a.created_at DESC
    """, (uid,))
    conn.close()
    if type_filter != "All":
        rows = [r for r in rows if r["type"] == type_filter]
    if status_filter == "Pending":
        rows = [r for r in rows if not r["completed"]]
    elif status_filter == "Done":
        rows = [r for r in rows if r["completed"]]
    if search:
        s = search.lower()
        rows = [r for r in rows if s in (r["subject"] or "").lower()
                or s in (r.get("contact_name") or "").lower()]
    return rows


def load_linked_options() -> tuple[list, list, list, list]:
    conn = get_connection()
    contacts = fetchall(conn, "SELECT id, name FROM contacts WHERE user_id=? ORDER BY name", (uid,))
    deals    = fetchall(conn, "SELECT id, title FROM deals WHERE user_id=? ORDER BY title",  (uid,))
    conn.close()
    c_names = ["— None —"] + [c["name"]  for c in contacts]
    c_ids   = [None]       + [c["id"]    for c in contacts]
    d_names = ["— None —"] + [d["title"] for d in deals]
    d_ids   = [None]       + [d["id"]    for d in deals]
    return c_names, c_ids, d_names, d_ids


def save_activity(atype, subject, contact_id, deal_id, due_date, completed, notes, act_id=None):
    conn = get_connection()
    cid  = contact_id if contact_id else None
    did  = deal_id    if deal_id    else None
    dd   = due_date.isoformat() if due_date else None
    done = 1 if completed else 0
    if act_id:
        execute(conn, """
            UPDATE activities
            SET type=?, subject=?, contact_id=?, deal_id=?, due_date=?, completed=?, notes=?
            WHERE id=? AND user_id=?
        """, (atype, subject, cid, did, dd, done, notes, act_id, uid))
    else:
        execute(conn, """
            INSERT INTO activities (user_id, type, subject, contact_id, deal_id, due_date, completed, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (uid, atype, subject, cid, did, dd, done, notes))
    conn.commit()
    conn.close()


def toggle_complete(act_id: int, current: bool):
    conn = get_connection()
    execute(conn, "UPDATE activities SET completed=? WHERE id=? AND user_id=?",
            (0 if current else 1, act_id, uid))
    conn.commit()
    conn.close()


def delete_activity(act_id: int):
    conn = get_connection()
    execute(conn, "DELETE FROM activities WHERE id=? AND user_id=?", (act_id, uid))
    conn.commit()
    conn.close()


def get_activity(act_id: int) -> dict | None:
    conn = get_connection()
    row  = fetchone(conn, "SELECT * FROM activities WHERE id=? AND user_id=?", (act_id, uid))
    conn.close()
    return row


# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [("act_edit_id", None), ("act_show_form", False), ("act_delete_id", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Page header ──────────────────────────────────────────────────────────────
h1, h2 = st.columns([3, 1])
with h1:
    st.markdown('<div class="page-title">Activities</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Log calls, emails, meetings, and tasks</div>', unsafe_allow_html=True)
with h2:
    if st.button("+ Log Activity", type="primary", use_container_width=True):
        st.session_state.act_show_form = True
        st.session_state.act_edit_id   = None

# ── Filters ───────────────────────────────────────────────────────────────────
f1, f2, f3, _ = st.columns([3, 1.5, 1.5, 1])
with f1: search        = st.text_input("Search", placeholder="Subject or contact...", label_visibility="collapsed")
with f2: type_filter   = st.selectbox("Type",   ["All"] + ACTIVITY_TYPES, label_visibility="collapsed")
with f3: status_filter = st.selectbox("Status", ["All", "Pending", "Done"],          label_visibility="collapsed")

activities = load_activities(type_filter, status_filter, search)
c_names, c_ids, d_names, d_ids = load_linked_options()

# ── Add / Edit form ───────────────────────────────────────────────────────────
if st.session_state.act_show_form:
    edit_id = st.session_state.act_edit_id
    editing = edit_id is not None
    row     = get_activity(edit_id) if editing else {}

    with st.expander("Edit Activity" if editing else "Log New Activity", expanded=True):
        with st.form("act_form"):
            fc1, fc2 = st.columns(2)
            with fc1:
                f_type    = st.selectbox("Activity Type *", ACTIVITY_TYPES,
                                         index=ACTIVITY_TYPES.index(row["type"])
                                         if row.get("type") in ACTIVITY_TYPES else 0)
                f_subject = st.text_input("Subject *", value=row.get("subject", ""))
                f_due     = st.date_input("Due Date",
                                          value=date.fromisoformat(row["due_date"])
                                          if row.get("due_date") else date.today())
            with fc2:
                cur_cid   = row.get("contact_id")
                ci        = c_ids.index(cur_cid) if cur_cid in c_ids else 0
                f_contact = st.selectbox("Linked Contact", c_names, index=ci)

                cur_did   = row.get("deal_id")
                di        = d_ids.index(cur_did) if cur_did in d_ids else 0
                f_deal    = st.selectbox("Linked Deal",    d_names, index=di)

                f_done    = st.checkbox("Mark as completed", value=bool(row.get("completed", False)))
                f_notes   = st.text_area("Notes", value=row.get("notes", ""), height=70)

            sb1, sb2, _ = st.columns([1, 1, 3])
            with sb1: submitted = st.form_submit_button("Save Activity", type="primary", use_container_width=True)
            with sb2: cancelled = st.form_submit_button("Cancel",        use_container_width=True)

        if submitted:
            if not f_subject.strip():
                st.error("Subject is required.")
            else:
                sel_cid = c_ids[c_names.index(f_contact)]
                sel_did = d_ids[d_names.index(f_deal)]
                save_activity(f_type, f_subject.strip(), sel_cid, sel_did, f_due,
                              f_done, f_notes.strip(), edit_id if editing else None)
                st.success("Activity saved.")
                st.session_state.act_show_form = False
                st.session_state.act_edit_id   = None
                st.rerun()

        if cancelled:
            st.session_state.act_show_form = False
            st.session_state.act_edit_id   = None
            st.rerun()

# ── Delete confirmation ───────────────────────────────────────────────────────
if st.session_state.act_delete_id:
    del_id  = st.session_state.act_delete_id
    del_row = get_activity(del_id)
    if del_row:
        st.warning(f"Delete activity **{del_row['subject']}**?")
        dc1, dc2, _ = st.columns([1, 1, 5])
        with dc1:
            if st.button("Confirm Delete", type="primary"):
                delete_activity(del_id)
                st.session_state.act_delete_id = None
                st.rerun()
        with dc2:
            if st.button("Cancel"):
                st.session_state.act_delete_id = None
                st.rerun()

# ── Activity list ─────────────────────────────────────────────────────────────
pending_count = sum(1 for a in activities if not a["completed"])
done_count    = sum(1 for a in activities if a["completed"])

st.markdown(
    f'<div class="section-header">{len(activities)} Activities — '
    f'{pending_count} pending, {done_count} completed</div>',
    unsafe_allow_html=True)

if not activities:
    st.markdown(
        '<p style="color:#94A3B8;font-size:0.875rem;">No activities found. Log your first one above.</p>',
        unsafe_allow_html=True)
else:
    for act in activities:
        completed  = bool(act["completed"])
        bg, fg, icon = TYPE_COLORS.get(act["type"], ("#F1F5F9", "#475569", "A"))
        contact    = act.get("contact_name") or "—"
        deal       = act.get("deal_title")   or "—"
        due        = act.get("due_date")     or "—"

        # Overdue check — pre-compute to avoid inline conditionals in f-string
        overdue = False
        if not completed and act.get("due_date"):
            try:
                overdue = date.fromisoformat(act["due_date"]) < date.today()
            except ValueError:
                pass

        # Pre-compute all style values
        row_opacity    = "0.58" if completed else "1"
        border_color   = "#FEE2E2" if overdue else "#E8EDF2"
        text_color     = "#94A3B8" if completed else "#0F172A"
        strikethrough  = "line-through" if completed else "none"
        due_color      = "#EF4444" if overdue else "#64748B"
        due_weight     = "600" if overdue else "400"
        due_prefix     = "Overdue — " if overdue else ""
        badge_bg       = "#DCFCE7" if completed else ("#FEE2E2" if overdue else "#FEF9C3")
        badge_fg       = "#166534" if completed else ("#991B1B" if overdue else "#854D0E")
        badge_text     = "Completed" if completed else ("Overdue" if overdue else "Pending")
        toggle_label   = "Reopen" if completed else "Complete"
        toggle_bg      = "#F1F5F9" if completed else "#DCFCE7"
        toggle_fg      = "#475569" if completed else "#166534"


        card_col, btn_col = st.columns([5, 1])

        with card_col:
            st.markdown(f"""
            <div style="
                display:flex;align-items:center;gap:1rem;
                padding:0.875rem 1.1rem;
                background:#fff;
                border:1px solid {border_color};
                border-radius:10px;
                opacity:{row_opacity};
            ">
                <div style="
                    width:38px;height:38px;border-radius:9px;
                    background:{bg};color:{fg};
                    display:flex;align-items:center;justify-content:center;
                    font-weight:700;font-size:0.78rem;flex-shrink:0;
                    letter-spacing:0.03em;
                ">{act['type'][:1]}</div>
                <div style="flex:1;min-width:0;">
                    <div style="
                        font-weight:500;font-size:0.9rem;
                        color:{text_color};
                        text-decoration:{strikethrough};
                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
                    ">{act['subject']}</div>
                    <div style="
                        font-size:0.75rem;color:#94A3B8;
                        margin-top:0.2rem;display:flex;gap:0.5rem;align-items:center;
                    ">
                        <span style="
                            background:{bg};color:{fg};
                            padding:0.1em 0.45em;border-radius:4px;
                            font-size:0.68rem;font-weight:600;
                        ">{act['type']}</span>
                        <span>{contact}</span>
                        <span style="color:#CBD5E1;">|</span>
                        <span style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{deal}</span>
                    </div>
                </div>
                <div style="text-align:right;flex-shrink:0;">
                    <div style="font-size:0.72rem;color:{due_color};font-weight:{due_weight};">
                        {due_prefix}{due}
                    </div>
                    <div style="
                        display:inline-block;margin-top:0.3rem;
                        padding:0.18em 0.6em;border-radius:5px;
                        font-size:0.7rem;font-weight:600;
                        background:{badge_bg};color:{badge_fg};
                        letter-spacing:0.02em;
                    ">{badge_text}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with btn_col:
            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button(
                    toggle_label,
                    key=f"tog_{act['id']}",
                    help="Toggle completion status",
                    use_container_width=True,
                ):
                    toggle_complete(act["id"], completed)
                    st.rerun()
            with b2:
                if st.button("Edit", key=f"edit_a_{act['id']}", use_container_width=True):
                    st.session_state.act_edit_id   = act["id"]
                    st.session_state.act_show_form = True
                    st.rerun()
            with b3:
                if st.button("Delete", key=f"del_a_{act['id']}", use_container_width=True):
                    st.session_state.act_delete_id = act["id"]
                    st.rerun()
