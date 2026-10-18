"""Ring + popup reminders. A fragment polls every few seconds while the app is open."""
import streamlit as st

from core import reminders, tasks
from core.config import ASSETS
from core.timeutil import human, parse, utcnow
from core import voice
from views import browser, speech
from views.common import esc


@st.cache_resource
def _ring() -> bytes:
    return (ASSETS / "ring.wav").read_bytes()


@st.fragment(run_every=10)
def watcher(user: dict, tz):
    uid, now = user["id"], utcnow()
    settings = st.session_state.get("settings", user["settings"])
    due = reminders.due_alarms(uid, now)
    if due:
        t, kind = due[0]
        seen = st.session_state.setdefault("seen_alarms", set())
        first = (t["id"], kind, t["snooze_until"]) not in seen
        with st.container(key="alarm_popup"):
            at = parse(t["start_at" if kind == "start" else "end_at"])
            st.markdown(f"<div style='text-align:center'><div class='bell'>🔔</div>"
                        f"<div class='eyebrow'>{'Starting' if kind == 'start' else 'Due'} · {human(at, tz, now)}</div>"
                        f"<div class='hello' style='white-space:normal;margin:.2rem 0 .6rem'>{esc(t['title'])}</div></div>", unsafe_allow_html=True)
            st.audio(_ring(), format="audio/wav", autoplay=True, loop=True)
            a, b, c = st.columns(3)
            if a.button("Done", icon=":material/check:", type="primary", width="stretch", key="al_done"):
                reminders.dismiss(uid, t["id"], kind)
                tasks.complete(uid, t["id"], tz)
                st.rerun()
            if b.button("Snooze 5m", width="stretch", key="al_snz"):
                reminders.snooze(uid, t["id"], 5)
                st.rerun(scope="fragment")
            if c.button("Dismiss", width="stretch", key="al_dis"):
                reminders.dismiss(uid, t["id"], kind)
                st.rerun(scope="fragment")
        if first:
            seen.add((t["id"], kind, t["snooze_until"]))
            browser.notify(("Starting: " if kind == "start" else "Due: ") + t["title"], "Open TaskFlow")
            if st.session_state.get("voice_on"):
                speech.say(voice.reminder(t, kind, tz, now))
    elif st.session_state.get("voice_on") and settings.get("digest_min"):  # periodic spoken digest
        last = st.session_state.setdefault("last_digest", now.timestamp())
        if now.timestamp() - last >= settings["digest_min"] * 60:
            st.session_state.last_digest = now.timestamp()
            speech.say(voice.brief(tasks.list_(uid), user["name"].split()[0], tz, now))
    speech.flush()
