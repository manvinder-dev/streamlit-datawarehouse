import streamlit as st

#Page config
st.set_page_config(
    page_title="LeadTrack",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Bootstrap database
from database.schema import create_tables
from database.seed   import seed_data

create_tables()
seed_data()

#Auth
from auth.authenticator import is_authenticated

#Global CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ── Dark sidebar ── */
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

/* ── Streamlit nav link styling ── */
[data-testid="stSidebarNavLink"] {
    border-radius: 6px !important;
    font-size: 0.855rem !important;
    font-weight: 500 !important;
    padding: 0.45rem 0.75rem !important;
    color: rgba(255,255,255,0.65) !important;
}
[data-testid="stSidebarNavLink"]:hover {
    background: rgba(255,255,255,0.07) !important;
    color: #fff !important;
}
[data-testid="stSidebarNavLink"][aria-selected="true"] {
    background: rgba(37,99,235,0.25) !important;
    color: #93C5FD !important;
}

/* ── Hide default chrome on login page ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Auth card ── */
.auth-logo {
    font-size: 1.75rem;
    font-weight: 700;
    color: #0F172A;
    letter-spacing: -0.03em;
    margin-bottom: 0.2rem;
}
.auth-tagline {
    font-size: 0.85rem;
    color: #64748B;
    margin-bottom: 2rem;
}
.test-accounts {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 0.875rem 1rem;
    margin-top: 1.25rem;
}
.test-accounts h4 {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94A3B8;
    margin: 0 0 0.5rem;
}
.test-accounts code {
    display: block;
    font-size: 0.8rem;
    color: #334155;
    line-height: 1.9;
}

/* ── Inputs ── */
.stTextInput input, .stPasswordInput input {
    border-radius: 8px !important;
    border: 1px solid #CBD5E1 !important;
    font-size: 0.875rem !important;
    padding: 0.625rem 0.875rem !important;
    transition: border-color 0.15s ease;
}
.stTextInput input:focus, .stPasswordInput input:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.08) !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    transition: all 0.15s ease !important;
}
.stButton > button[kind="primary"] {
    background: #2563EB !important;
    border: none !important;
}
.stButton > button[kind="primary"]:hover {
    background: #1D4ED8 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(37,99,235,0.3) !important;
}

/* ── Metric / content page globals ── */
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

# ── Navigation ────────────────────────────────────────────────────────────────
if is_authenticated():
    # Expand sidebar for authenticated users
    st.session_state["sidebar_state"] = "expanded"

    pg = st.navigation(
        {
            "": [
                st.Page("pages/1_Dashboard.py",       title="Dashboard",        url_path="dashboard"),
                st.Page("pages/2_Contacts.py",        title="Contacts",         url_path="contacts"),
                st.Page("pages/3_Deals.py",           title="Deals",            url_path="deals"),
                st.Page("pages/4_Activities.py",      title="Activities",       url_path="activities"),
            ],
            "Account": [
                st.Page("pages/5_Account_Settings.py", title="Settings",        url_path="settings"),
            ],
        },
        position="sidebar",
    )
else:
    pg = st.navigation(
        [st.Page("pages/0_Login.py", title="LeadTrack", url_path="login")],
        position="hidden",
    )

pg.run()
