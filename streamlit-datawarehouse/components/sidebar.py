"""
Shared sidebar component.

Renders the user profile block, navigation hint, and logout button at the
top of every page sidebar. Call render_sidebar() at the start of each page.
"""

import streamlit as st
from auth.authenticator import current_user, logout


def render_sidebar() -> None:
    """Inject sidebar content — user info + logout button."""
    user = current_user()
    if not user:
        return

    with st.sidebar:
        st.markdown(
            f"""
            <div style="
                padding: 1rem 0.5rem 1.25rem;
                border-bottom: 1px solid rgba(255,255,255,0.08);
                margin-bottom: 1rem;
            ">
                <div style="
                    font-size: 0.7rem;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                    color: rgba(255,255,255,0.45);
                    margin-bottom: 0.4rem;
                ">Signed in as</div>
                <div style="
                    font-weight: 600;
                    font-size: 0.95rem;
                    color: #fff;
                    line-height: 1.2;
                ">{user['full_name']}</div>
                <div style="
                    font-size: 0.78rem;
                    color: rgba(255,255,255,0.5);
                    margin-top: 0.15rem;
                ">@{user['username']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Sign Out", key="sidebar_logout", use_container_width=True):
            logout()
            st.rerun()
