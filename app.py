
import html

import streamlit as st

from core import auth, avatar, config, db, scheduler, stats, tasks, voice
from core.timeutil import utcnow
from views import (alarm, auth_view, browser, focus_view, notes_view, progress_view, settings_view,
                   speech, style, tasks_view)
from views.common import ring, user_tz

st.set_page_config(page_title=config.APP_NAME, page_icon=str(config.ASSETS / "favicon.png"),
                   layout="centered", initial_sidebar_state="collapsed")


@st.cache_resource
def boot():
    db.init()
    scheduler.start()  # e-mail reminders keep firing even when nobody has the app open
    return True


def current_user():
    if st.session_state.get("uid"):
        return auth.get_user(st.session_state.uid)
    try:
        signed_in = st.user.is_logged_in
    except Exception:
        signed_in = False
    if signed_in and st.user.get("email"):  # Google sign-in
        u = auth.oauth_user(st.user.email, st.user.get("name", ""), st.user.get("picture"))
    else:
        u = auth.user_from_token(st.context.cookies.get(config.COOKIE))  # remember-me cookie
    if u:
        st.session_state.uid = u["id"]
    return u


def _voice_toggled():
    uid = st.session_state.uid
    on = st.session_state.voice_on
    st.session_state.settings = auth.save_settings(uid, voice=on)
    if on:
        user = auth.get_user(uid)
        st.session_state.last_digest = utcnow().timestamp()
        speech.say(voice.brief(tasks.list_(uid), user["name"].split()[0], user_tz(user)))
    else:
        speech.stop()


NAV = {"Tasks": "task_alt", "Notes": "sticky_note_2", "Progress": "monitoring", "Focus": "timer",
       "Settings": "tune"}


def header(user, tz):
    now = utcnow()
    rows = [t for t in tasks.list_(user["id"]) if tasks_view._is_today(t, now, tz)]
    done = sum(1 for t in rows if tasks.status(t) == "completed")
    local = now.astimezone(tz)
    greet = "Good morning" if local.hour < 12 else "Good afternoon" if local.hour < 18 else "Good evening"
    st.markdown(f'<div class="hdr"><div class="av">{avatar.avatar_html(user, 46)}</div><div class="who">'
                f'<div class="eyebrow">{local:%A · %d %b}</div>'
                f'<div class="hello">{greet}, <span class="grad">{html.escape(user["name"].split()[0])}</span></div></div>'
                f'{ring(100 * done / len(rows) if rows else 0, f"{done}/{len(rows)}")}</div>', unsafe_allow_html=True)
    with st.container(key="voice"):
        st.toggle("🔊 Voice aid — reads your tasks aloud", key="voice_on", on_change=_voice_toggled,
                  help="Speaks all your tasks when switched on, and speaks reminders as they fire.")


boot()
// style injection 
style.inject()
browser.pwa()
user = current_user()
if not user:
    auth_view.render()
    st.stop()

if (tok := st.session_state.pop("pending_cookie", None)):
    browser.set_cookie(tok, config.SESSION_DAYS)
st.session_state.setdefault("settings", user["settings"])
st.session_state.setdefault("voice_on", user["settings"]["voice"])
tz = user_tz(user)

header(user, tz)
with st.container(key="navbar"):
    page = st.segmented_control("Menu", list(NAV), default="Tasks", key="nav", label_visibility="collapsed",
                                width="stretch", format_func=lambda k: f":material/{NAV[k]}: {k}") or "Tasks"
{"Tasks": tasks_view, "Notes": notes_view, "Progress": progress_view, "Focus": focus_view,
 "Settings": settings_view}[page].render(user, tz)

alarm.watcher(user, tz)
speech.flush()
