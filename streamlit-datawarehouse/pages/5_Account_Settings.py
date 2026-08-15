"""
Account Settings Page — LeadTrack

Allows the authenticated user to update their profile and change password.
"""

import streamlit as st

from auth.authenticator  import require_auth, current_user, current_user_id, update_profile, change_password
from components.sidebar  import render_sidebar

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
.page-sub   { font-size:0.82rem; color:#64748B; margin-top:0.15rem; margin-bottom:2rem; }
.settings-card {
    background:#fff;
    border:1px solid #E8EDF2;
    border-radius:12px;
    padding:1.75rem;
    margin-bottom:1.5rem;
    box-shadow:0 1px 4px rgba(0,0,0,0.04);
}
.card-title {
    font-size:1rem;
    font-weight:600;
    color:#0F172A;
    margin-bottom:0.25rem;
}
.card-desc {
    font-size:0.8rem;
    color:#64748B;
    margin-bottom:1.25rem;
    padding-bottom:1rem;
    border-bottom:1px solid #F1F5F9;
}
.pw-rule {
    font-size:0.75rem;
    color:#94A3B8;
    margin-top:0.25rem;
    line-height:1.6;
}
</style>
""", unsafe_allow_html=True)

user = current_user()
uid  = current_user_id()

st.markdown('<div class="page-title">Account Settings</div>', unsafe_allow_html=True)
st.markdown(f'<div class="page-sub">Manage your profile and security settings</div>', unsafe_allow_html=True)

left, _, right = st.columns([2, 0.25, 2])

# ── Profile card ──────────────────────────────────────────────────────────────
with left:
    st.markdown("""
    <div class="settings-card">
        <div class="card-title">Profile Information</div>
        <div class="card-desc">Update your display name and email address</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("profile_form"):
        p_name  = st.text_input("Full Name",     value=user["full_name"])
        p_email = st.text_input("Email Address", value=user["email"])
        st.markdown(
            f'<div style="font-size:0.78rem;color:#94A3B8;margin-top:-0.5rem;margin-bottom:0.75rem;">'
            f'Username: <strong>@{user["username"]}</strong> (cannot be changed)</div>',
            unsafe_allow_html=True)
        p_submit = st.form_submit_button("Save Profile", type="primary", use_container_width=True)

    if p_submit:
        ok, msg = update_profile(uid, p_name, p_email)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

# ── Password card ─────────────────────────────────────────────────────────────
with right:
    st.markdown("""
    <div class="settings-card">
        <div class="card-title">Change Password</div>
        <div class="card-desc">Choose a strong password to keep your account secure</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("password_form"):
        pw_current  = st.text_input("Current Password",     type="password")
        pw_new      = st.text_input("New Password",         type="password")
        pw_confirm  = st.text_input("Confirm New Password", type="password")
        st.markdown(
            '<div class="pw-rule">Min 8 characters · 1 uppercase · 1 digit · 1 special character</div>',
            unsafe_allow_html=True)
        pw_submit = st.form_submit_button("Update Password", type="primary", use_container_width=True)

    if pw_submit:
        ok, msg = change_password(uid, pw_current, pw_new, pw_confirm)
        if ok:
            st.success(msg)
        else:
            st.error(msg)
