"""Per-session speech queue; flushed once at the end of a script/fragment run."""
import streamlit as st

from views import browser


def say(text: str):
    st.session_state.setdefault("speech", []).append(text)


def stop():
    st.session_state["speech_stop"] = True


def flush():
    if st.session_state.pop("speech_stop", False):
        browser.stop_speaking()
    queue = st.session_state.pop("speech", [])
    if queue:
        browser.speak(" ".join(queue))
