"""Pomodoro-style focus timer tied to a task."""
import time

import streamlit as st

from core import db, tasks
from core.timeutil import iso, utcnow
from views import alarm, speech
from views.common import esc, ring


@st.fragment(run_every=1)
def _timer(uid):
    f = st.session_state.get("focus")
    if not f:
        return
    left = f["end"] - time.time()
    if left <= 0:
        db.execute("INSERT INTO focus_log(user_id,task_id,minutes,ended_at) VALUES(?,?,?,?)",
                   (uid, f["task"], f["mins"], iso(utcnow())))
        st.session_state.focus_done = f
        st.session_state.focus = None
        if st.session_state.get("voice_on"):
            speech.say(f"Focus session complete. Great work on {f['title']}.")
        st.rerun()
    m, s = divmod(int(left), 60)
    pct = 100 * (1 - left / (f["mins"] * 60))
    st.markdown(f'<div class="timer-wrap">{ring(pct, f"{m:02d}:{s:02d}", "#8b5cf6", "big")}</div>'
                f'<div class="sub" style="text-align:center">Focusing on <b>{esc(f["title"])}</b></div>',
                unsafe_allow_html=True)


def render(user, tz):
    uid = user["id"]
    if done := st.session_state.pop("focus_done", None):
        st.balloons()
        st.success(f"Session complete — {done['mins']} minutes on “{done['title']}”.")
        st.audio(alarm._ring(), format="audio/wav", autoplay=True)
    if st.session_state.get("focus"):
        _timer(uid)
        if st.button("Stop session", icon=":material/stop:", width="stretch"):
            st.session_state.focus = None
            st.rerun()
        return
    open_tasks = [t for t in tasks.list_(uid) if tasks.status(t) in ("active", "pending")]
    ids = [None] + [t["id"] for t in open_tasks]
    names = {t["id"]: t["title"] for t in open_tasks}
    pre = st.session_state.pop("focus_task", None)
    task = st.selectbox("What are you focusing on?", ids, index=ids.index(pre) if pre in ids else 0,
                        format_func=lambda i: "Free focus" if i is None else names[i])
    mins = st.pills("Minutes", [15, 25, 45, 60], default=25) or 25
    if st.button("Start focus", icon=":material/play_arrow:", type="primary", width="stretch"):
        st.session_state.focus = {"end": time.time() + mins * 60, "mins": mins, "task": task,
                                  "title": names.get(task, "free focus")}
        st.rerun()
    st.caption(f"Today: {stats_minutes(uid, tz)} focused minutes. Keep this tab open while the timer runs.")


def stats_minutes(uid, tz):
    from core import stats
    return stats.focus_minutes_today(uid, tz)
