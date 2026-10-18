import streamlit as st

from core import auth, config
from views import browser


def google_enabled() -> bool:
    try:
        return "google" in st.secrets.get("auth", {})
    except Exception:
        return False


def _enter(user, remember):
    st.session_state.uid = user["id"]
    st.session_state.pending_cookie = auth.create_session(user["id"]) if remember else None
    st.rerun()


def render():
    if st.session_state.pop("clear_cookie", False):
        browser.clear_cookie()
    st.markdown("<div style='text-align:center;margin:2rem 0 .8rem'>"
                "<div style='width:74px;height:74px;margin:auto;border-radius:22px;display:grid;place-items:center;"
                "font-size:2.2rem;background:linear-gradient(135deg,#8b5cf6,#22d3ee);box-shadow:0 0 50px rgba(139,92,246,.7)'>✓</div>"
                "<div class='hello grad' style='font-size:2rem;margin-top:.8rem'>TaskFlow</div>"
                "<div class='eyebrow'>Tasks · Notes · Reminders · Progress</div></div>", unsafe_allow_html=True)
    with st.container(key="authbox"):
        _forms()


def _forms():
    if google_enabled():
        st.button("Continue with Google", icon=":material/account_circle:", width="stretch",
                  type="primary", on_click=st.login, args=("google",))
        st.caption("Uses your Google name and profile picture. Not available inside the Android app.")
        st.divider()
    tab_in, tab_up = st.tabs(["Sign in", "Create account"])
    with tab_in, st.form("login"):
        email = st.text_input("Email")
        pw = st.text_input("Password", type="password")
        remember = st.checkbox("Keep me signed in on this device", value=True)
        if st.form_submit_button("Sign in", type="primary", width="stretch"):
            try:
                _enter(auth.login(email, pw), remember)
            except ValueError as e:
                st.error(str(e))
    with tab_up:
        if not config.flag("ALLOW_SIGNUP", True):
            st.info("Sign-ups are closed on this server.")
        else:
            with st.form("signup"):
                name = st.text_input("Your name")
                email = st.text_input("Email", key="su_email")
                pw = st.text_input("Password (8+ characters)", type="password", key="su_pw")
                if st.form_submit_button("Create account", type="primary", width="stretch"):
                    try:
                        _enter(auth.register(email, name, pw), True)
                    except ValueError as e:
                        st.error(str(e))
