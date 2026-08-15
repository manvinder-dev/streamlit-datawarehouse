"""
Deals Page — LeadTrack

Full CRUD for deals with pipeline stage view. All records isolated to
the authenticated user.
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
.deal-card {
    background:#fff;
    border:1px solid #E8EDF2;
    border-radius:10px;
    padding:1rem 1.1rem;
    margin-bottom:0.75rem;
    box-shadow:0 1px 3px rgba(0,0,0,0.04);
    transition:box-shadow 0.15s;
}
.deal-card:hover { box-shadow:0 4px 12px rgba(0,0,0,0.08); }
</style>
""", unsafe_allow_html=True)

uid = current_user_id()

STAGES = ["Prospect", "Qualified", "Proposal", "Won", "Lost"]
STAGE_COLORS = {
    "Prospect":  ("#F1F5F9", "#475569"),
    "Qualified": ("#DBEAFE", "#1E40AF"),
    "Proposal":  ("#FEF9C3", "#854D0E"),
    "Won":       ("#DCFCE7", "#166534"),
    "Lost":      ("#FEE2E2", "#991B1B"),
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_contacts_for_user() -> list[dict]:
    conn = get_connection()
    rows = fetchall(conn, "SELECT id, name FROM contacts WHERE user_id=? ORDER BY name", (uid,))
    conn.close()
    return rows


def load_deals(stage_filter="All", search="") -> list[dict]:
    conn = get_connection()
    rows = fetchall(conn, """
        SELECT d.*, c.name AS contact_name
        FROM deals d
        LEFT JOIN contacts c ON d.contact_id = c.id
        WHERE d.user_id = ?
        ORDER BY d.created_at DESC
    """, (uid,))
    conn.close()
    if stage_filter != "All":
        rows = [r for r in rows if r["stage"] == stage_filter]
    if search:
        s = search.lower()
        rows = [r for r in rows if s in (r["title"] or "").lower()
                or s in (r.get("contact_name") or "").lower()]
    return rows


def save_deal(title, value, stage, contact_id, close_date, notes, deal_id=None):
    conn = get_connection()
    now  = datetime.utcnow().isoformat()
    cid  = contact_id if contact_id else None
    cd   = close_date.isoformat() if close_date else None
    if deal_id:
        execute(conn, """
            UPDATE deals SET title=?, value=?, stage=?, contact_id=?,
            close_date=?, notes=?, updated_at=? WHERE id=? AND user_id=?
        """, (title, value, stage, cid, cd, notes, now, deal_id, uid))
    else:
        execute(conn, """
            INSERT INTO deals (user_id, contact_id, title, value, stage, close_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (uid, cid, title, value, stage, cd, notes))
    conn.commit()
    conn.close()


def delete_deal(deal_id: int):
    conn = get_connection()
    execute(conn, "DELETE FROM deals WHERE id=? AND user_id=?", (deal_id, uid))
    conn.commit()
    conn.close()


def get_deal(deal_id: int) -> dict | None:
    conn = get_connection()
    row  = fetchone(conn, "SELECT * FROM deals WHERE id=? AND user_id=?", (deal_id, uid))
    conn.close()
    return row


# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [("deal_edit_id", None), ("deal_show_form", False), ("deal_delete_id", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Page header ──────────────────────────────────────────────────────────────
h1, h2 = st.columns([3, 1])
with h1:
    st.markdown('<div class="page-title">Deals</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Track your pipeline and opportunities</div>', unsafe_allow_html=True)
with h2:
    if st.button("+ Add Deal", type="primary", use_container_width=True):
        st.session_state.deal_show_form = True
        st.session_state.deal_edit_id   = None

# ── Filters ───────────────────────────────────────────────────────────────────
f1, f2, _ = st.columns([3, 2, 2])
with f1: search       = st.text_input("Search", placeholder="Deal title or contact name...", label_visibility="collapsed")
with f2: stage_filter = st.selectbox("Stage", ["All"] + STAGES, label_visibility="collapsed")

deals            = load_deals(stage_filter, search)
contact_list     = load_contacts_for_user()
contact_map      = {c["id"]: c["name"] for c in contact_list}
contact_names    = ["— None —"] + [c["name"] for c in contact_list]
contact_id_list  = [None]       + [c["id"]   for c in contact_list]

# ── Add / Edit form ───────────────────────────────────────────────────────────
if st.session_state.deal_show_form:
    edit_id = st.session_state.deal_edit_id
    editing = edit_id is not None
    row     = get_deal(edit_id) if editing else {}

    with st.expander("Deal Details" if editing else "New Deal", expanded=True):
        with st.form("deal_form"):
            fc1, fc2 = st.columns(2)
            with fc1:
                f_title = st.text_input("Deal Title *", value=row.get("title", ""))
                f_value = st.number_input("Value ($)", min_value=0.0, step=500.0,
                                          value=float(row.get("value", 0)))
                f_stage = st.selectbox("Stage", STAGES,
                                       index=STAGES.index(row["stage"]) if row.get("stage") in STAGES else 0)
            with fc2:
                # Contact selector
                current_cid = row.get("contact_id")
                cid_index   = contact_id_list.index(current_cid) if current_cid in contact_id_list else 0
                f_contact   = st.selectbox("Linked Contact", contact_names, index=cid_index)
                f_close     = st.date_input("Expected Close Date",
                                            value=date.fromisoformat(row["close_date"])
                                            if row.get("close_date") else date.today())
                f_notes     = st.text_area("Notes", value=row.get("notes", ""), height=80)

            sb1, sb2, _ = st.columns([1, 1, 3])
            with sb1: submitted = st.form_submit_button("Save Deal", type="primary", use_container_width=True)
            with sb2: cancelled = st.form_submit_button("Cancel",    use_container_width=True)

        if submitted:
            if not f_title.strip():
                st.error("Deal title is required.")
            else:
                sel_cid = contact_id_list[contact_names.index(f_contact)]
                save_deal(f_title.strip(), f_value, f_stage, sel_cid, f_close, f_notes.strip(),
                          edit_id if editing else None)
                st.success("Deal saved.")
                st.session_state.deal_show_form = False
                st.session_state.deal_edit_id   = None
                st.rerun()

        if cancelled:
            st.session_state.deal_show_form = False
            st.session_state.deal_edit_id   = None
            st.rerun()

# ── Delete confirmation ───────────────────────────────────────────────────────
if st.session_state.deal_delete_id:
    del_id  = st.session_state.deal_delete_id
    del_row = get_deal(del_id)
    if del_row:
        st.warning(f"Delete deal **{del_row['title']}**?")
        dc1, dc2, _ = st.columns([1, 1, 5])
        with dc1:
            if st.button("Confirm Delete", type="primary"):
                delete_deal(del_id)
                st.session_state.deal_delete_id = None
                st.success("Deal deleted.")
                st.rerun()
        with dc2:
            if st.button("Cancel"):
                st.session_state.deal_delete_id = None
                st.rerun()

# ── Pipeline summary strip ────────────────────────────────────────────────────
st.markdown('<div class="section-header">Pipeline Overview</div>', unsafe_allow_html=True)
all_deals    = load_deals()
stage_totals = {s: {"count": 0, "value": 0.0} for s in STAGES}
for d in all_deals:
    s = d["stage"]
    if s in stage_totals:
        stage_totals[s]["count"] += 1
        stage_totals[s]["value"] += d["value"]

pcols = st.columns(5)
for i, stage in enumerate(STAGES):
    bg, fg = STAGE_COLORS[stage]
    data   = stage_totals[stage]
    with pcols[i]:
        st.markdown(f"""
        <div style="background:{bg};border-radius:8px;padding:0.75rem;text-align:center;">
            <div style="font-size:0.68rem;font-weight:600;text-transform:uppercase;
                letter-spacing:0.07em;color:{fg};margin-bottom:0.3rem;">{stage}</div>
            <div style="font-size:1.4rem;font-weight:700;color:#0F172A;">{data['count']}</div>
            <div style="font-size:0.72rem;color:#64748B;">${data['value']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Deals table ───────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-header">{len(deals)} Deal{"s" if len(deals)!=1 else ""}</div>',
            unsafe_allow_html=True)

if not deals:
    st.markdown(
        '<p style="color:#94A3B8;font-size:0.875rem;">No deals found. Click "+ Add Deal" to create one.</p>',
        unsafe_allow_html=True)
else:
    hdr_cols = st.columns([3, 2, 1.5, 1.5, 1.5, 1.5])
    for h, label in zip(hdr_cols, ["Deal Title", "Contact", "Value", "Stage", "Close Date", "Actions"]):
        h.markdown(f'<div style="font-size:0.72rem;font-weight:600;text-transform:uppercase;'
                   f'letter-spacing:0.07em;color:#94A3B8;padding:0.5rem 0;">{label}</div>',
                   unsafe_allow_html=True)

    st.markdown('<hr style="margin:0 0 0.5rem;border:none;border-top:1px solid #E8EDF2;">', unsafe_allow_html=True)

    for d in deals:
        bg, fg = STAGE_COLORS.get(d["stage"], ("#F1F5F9", "#475569"))
        row_cols = st.columns([3, 2, 1.5, 1.5, 1.5, 1.5])

        row_cols[0].markdown(
            f'<div style="font-weight:500;font-size:0.875rem;color:#0F172A;padding:0.5rem 0;">{d["title"]}</div>',
            unsafe_allow_html=True)
        row_cols[1].markdown(
            f'<div style="font-size:0.8rem;color:#64748B;padding:0.5rem 0;">{d.get("contact_name") or "—"}</div>',
            unsafe_allow_html=True)
        row_cols[2].markdown(
            f'<div style="font-size:0.875rem;font-weight:500;color:#0F172A;padding:0.5rem 0;">${d["value"]:,.0f}</div>',
            unsafe_allow_html=True)
        row_cols[3].markdown(
            f'<span style="display:inline-block;padding:0.2em 0.65em;border-radius:4px;'
            f'font-size:0.72rem;font-weight:500;background:{bg};color:{fg};margin-top:0.5rem;">'
            f'{d["stage"]}</span>',
            unsafe_allow_html=True)
        row_cols[4].markdown(
            f'<div style="font-size:0.8rem;color:#64748B;padding:0.5rem 0;">{d.get("close_date") or "—"}</div>',
            unsafe_allow_html=True)

        with row_cols[5]:
            ce, cd = st.columns(2)
            with ce:
                if st.button("Edit", key=f"edit_d_{d['id']}"):
                    st.session_state.deal_edit_id   = d["id"]
                    st.session_state.deal_show_form = True
                    st.rerun()
            with cd:
                if st.button("Del", key=f"del_d_{d['id']}"):
                    st.session_state.deal_delete_id = d["id"]
                    st.rerun()

        st.markdown('<hr style="margin:0;border:none;border-top:1px solid #F1F5F9;">', unsafe_allow_html=True)
