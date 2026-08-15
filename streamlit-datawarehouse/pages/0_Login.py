"""
Login / Register page — LeadTrack
Shown when the user is not authenticated.
"""

import streamlit as st
from auth.authenticator import login, register

# ── Auth UI ───────────────────────────────────────────────────────────────────
col_l, col_c, col_r = st.columns([1, 1.2, 1])

with col_c:
    st.markdown("""
    <div style="padding: 3rem 0 1.5rem;">
        <div class="auth-logo">LeadTrack</div>
        <div class="auth-tagline">Manage your contacts, deals, and pipeline</div>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

    # ── Login tab ─────────────────────────────────────────────────────────────
    with tab_login:
        with st.form("login_form", clear_on_submit=False):
            username_input = st.text_input("Username", placeholder="your_username")
            password_input = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

        if submitted:
            ok, err = login(username_input, password_input)
            if ok:
                st.success("Signing in...")
                st.rerun()
            else:
                st.error(err)

        st.markdown("""
        <div class="test-accounts">
            <h4>Test Accounts</h4>
            <code>
                alice / Demo1234!<br>
                bob / Demo1234!<br>
                carol / Demo1234!
            </code>
        </div>
        """, unsafe_allow_html=True)

    # ── Register tab ──────────────────────────────────────────────────────────
    with tab_register:
        with st.form("register_form", clear_on_submit=True):
            reg_name     = st.text_input("Full Name",        placeholder="Jane Smith")
            reg_username = st.text_input("Username",         placeholder="janesmith")
            reg_email    = st.text_input("Email Address",    placeholder="jane@company.com")
            reg_password = st.text_input("Password",         type="password",
                                         placeholder="Min 8 chars, 1 uppercase, 1 digit, 1 symbol")
            reg_confirm  = st.text_input("Confirm Password", type="password", placeholder="••••••••")
            reg_submit   = st.form_submit_button("Create Account", use_container_width=True, type="primary")

        if reg_submit:
            ok, msg = register(reg_username, reg_email, reg_password, reg_confirm, reg_name)
            if ok:
                st.success(msg + " Please sign in above.")
            else:
                st.error(msg)
