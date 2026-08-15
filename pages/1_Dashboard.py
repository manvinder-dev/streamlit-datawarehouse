"""
Dashboard Page — LeadTrack

Shows per-user KPI summary cards and a recent activity feed.
All data is strictly filtered to the authenticated user's ID.
"""

import streamlit as st
import pandas as pd
from datetime import date

from auth.authenticator import require_auth, current_user, current_user_id
from components.sidebar  import render_sidebar
from database.connection import get_connection, fetchall, fetchone

if not require_auth():
    st.stop()

render_sidebar()

# ── Shared CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
#MainMenu, footer { visibility: hidden; }

/* Sidebar dark theme */
section[data-testid="stSidebar"] {
    background: #1A1D23 !important;
    border-right: 1px solid #2D3139;
}
section[data-testid="stSidebar"] * { color: rgba(255,255,255,0.75) !important; }
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: rgba(255,255,255,0.7) !important;
    font-size: 0.8rem !important;
    margin-top: 0.5rem;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.12) !important;
}

/* Metric cards */
.metric-card {
    background: #fff;
    border: 1px solid #E8EDF2;
    border-radius: 10px;
    padding: 1.25rem 1.5rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    transition: box-shadow 0.15s ease;
}
.metric-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
.metric-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94A3B8;
    font-weight: 500;
    margin-bottom: 0.5rem;
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #0F172A;
    letter-spacing: -0.03em;
    line-height: 1;
}
.metric-sub {
    font-size: 0.78rem;
    color: #64748B;
    margin-top: 0.35rem;
}
.metric-accent {
    position: absolute;
    top: 0; right: 0;
    width: 4px; height: 100%;
}

/* Section headers */
.section-header {
    font-size: 1rem;
    font-weight: 600;
    color: #0F172A;
    letter-spacing: -0.01em;
    margin: 1.75rem 0 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #E8EDF2;
}

/* Status badges */
.badge {
    display: inline-block;
    padding: 0.2em 0.65em;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.02em;
}
.badge-won      { background: #DCFCE7; color: #166534; }
.badge-proposal { background: #FEF9C3; color: #854D0E; }
.badge-qualified{ background: #DBEAFE; color: #1E40AF; }
.badge-prospect { background: #F1F5F9; color: #475569; }
.badge-lost     { background: #FEE2E2; color: #991B1B; }
</style>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
user    = current_user()
uid     = current_user_id()
conn    = get_connection()

contacts   = fetchall(conn, "SELECT * FROM contacts WHERE user_id = ?", (uid,))
deals      = fetchall(conn, "SELECT * FROM deals    WHERE user_id = ?", (uid,))
activities = fetchall(conn, "SELECT a.*, c.name AS contact_name, d.title AS deal_title "
                           "FROM activities a "
                           "LEFT JOIN contacts c ON a.contact_id = c.id "
                           "LEFT JOIN deals    d ON a.deal_id    = d.id "
                           "WHERE a.user_id = ? "
                           "ORDER BY a.created_at DESC LIMIT 10", (uid,))
conn.close()

# ── KPI calculations ──────────────────────────────────────────────────────────
total_contacts   = len(contacts)
total_deals      = len(deals)
won_deals        = [d for d in deals if d["stage"] == "Won"]
open_deals       = [d for d in deals if d["stage"] not in ("Won", "Lost")]
pipeline_value   = sum(d["value"] for d in open_deals)
total_revenue    = sum(d["value"] for d in won_deals)
pending_tasks    = sum(1 for a in activities if not a["completed"])

# ── Page header ──────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="
    display: flex; align-items: center; justify-content: space-between;
    padding: 1.5rem 0 1rem;
    border-bottom: 1px solid #E8EDF2;
    margin-bottom: 1.5rem;
">
    <div>
        <div style="font-size:1.5rem;font-weight:700;color:#0F172A;letter-spacing:-0.025em;">
            Dashboard
        </div>
        <div style="font-size:0.82rem;color:#64748B;margin-top:0.15rem;">
            Welcome back, {user['full_name']}
        </div>
    </div>
    <div style="font-size:0.8rem;color:#94A3B8;">{date.today().strftime('%B %d, %Y')}</div>
</div>
""", unsafe_allow_html=True)

# ── KPI Cards ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

cards = [
    (c1, "Total Contacts",    str(total_contacts),      f"{sum(1 for c in contacts if c['status']=='Lead')} leads",          "#2563EB"),
    (c2, "Active Deals",      str(len(open_deals)),     f"{total_deals} deals total",                                        "#0EA5E9"),
    (c3, "Pipeline Value",    f"${pipeline_value:,.0f}", f"{len(open_deals)} open opportunities",                             "#8B5CF6"),
    (c4, "Revenue Closed",    f"${total_revenue:,.0f}",  f"{len(won_deals)} won deal{'s' if len(won_deals)!=1 else ''}",     "#10B981"),
]

for col, label, value, sub, accent in cards:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-accent" style="background:{accent};"></div>
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Deal Pipeline by Stage ───────────────────────────────────────────────────
st.markdown('<div class="section-header">Deal Pipeline</div>', unsafe_allow_html=True)

stages      = ["Prospect", "Qualified", "Proposal", "Won", "Lost"]
stage_data  = {s: {"count": 0, "value": 0.0} for s in stages}
for d in deals:
    s = d["stage"]
    if s in stage_data:
        stage_data[s]["count"] += 1
        stage_data[s]["value"] += d["value"]

stage_cols = st.columns(5)
stage_colors = {
    "Prospect":  ("#F1F5F9", "#475569"),
    "Qualified": ("#DBEAFE", "#1E40AF"),
    "Proposal":  ("#FEF9C3", "#854D0E"),
    "Won":       ("#DCFCE7", "#166534"),
    "Lost":      ("#FEE2E2", "#991B1B"),
}

for i, stage in enumerate(stages):
    data  = stage_data[stage]
    bg, fg = stage_colors[stage]
    with stage_cols[i]:
        st.markdown(f"""
        <div style="
            background:{bg};
            border-radius:8px;
            padding:1rem;
            text-align:center;
        ">
            <div style="font-size:0.7rem;font-weight:500;text-transform:uppercase;
                letter-spacing:0.07em;color:{fg};margin-bottom:0.4rem;">{stage}</div>
            <div style="font-size:1.6rem;font-weight:700;color:#0F172A;letter-spacing:-0.03em;">
                {data['count']}
            </div>
            <div style="font-size:0.75rem;color:#64748B;margin-top:0.15rem;">
                ${data['value']:,.0f}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── Recent Activity ───────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Recent Activity</div>', unsafe_allow_html=True)

if not activities:
    st.markdown(
        '<p style="color:#94A3B8;font-size:0.875rem;">No activities logged yet. '
        'Head to the Activities page to add your first one.</p>',
        unsafe_allow_html=True,
    )
else:
    type_icons = {"Call": "C", "Email": "E", "Meeting": "M", "Task": "T"}
    type_colors = {
        "Call":    ("#DBEAFE", "#1E40AF"),
        "Email":   ("#FCE7F3", "#9D174D"),
        "Meeting": ("#FEF3C7", "#92400E"),
        "Task":    ("#F0FDF4", "#166534"),
    }

    for act in activities:
        completed = bool(act["completed"])
        icon      = type_icons.get(act["type"], "A")
        bg, fg    = type_colors.get(act["type"], ("#F1F5F9", "#475569"))
        contact   = act.get("contact_name") or "—"
        deal      = act.get("deal_title") or "—"
        due       = act.get("due_date") or "—"
        status_col = "#10B981" if completed else "#F59E0B"
        status_txt = "Done" if completed else "Pending"

        st.markdown(f"""
        <div style="
            display:flex; align-items:center; gap:1rem;
            padding:0.75rem 1rem;
            background:#fff;
            border:1px solid #E8EDF2;
            border-radius:8px;
            margin-bottom:0.5rem;
        ">
            <div style="
                width:36px; height:36px; border-radius:8px;
                background:{bg}; color:{fg};
                display:flex; align-items:center; justify-content:center;
                font-weight:700; font-size:0.75rem; flex-shrink:0;
            ">{icon}</div>
            <div style="flex:1; min-width:0;">
                <div style="font-weight:500;font-size:0.875rem;color:#0F172A;
                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                    {act['subject']}
                </div>
                <div style="font-size:0.75rem;color:#64748B;margin-top:0.1rem;">
                    {act['type']} &nbsp;·&nbsp; {contact} &nbsp;·&nbsp; {deal}
                </div>
            </div>
            <div style="text-align:right;flex-shrink:0;">
                <div style="font-size:0.72rem;color:#94A3B8;">{due}</div>
                <div style="
                    display:inline-block;
                    margin-top:0.25rem;
                    padding:0.15em 0.55em;
                    border-radius:4px;
                    font-size:0.68rem;
                    font-weight:500;
                    background:{'#DCFCE7' if completed else '#FEF9C3'};
                    color:{status_col};
                ">{status_txt}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
