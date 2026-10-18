from datetime import datetime, timedelta

import streamlit as st

from core import categories, notifier, stats, tasks
from core.timeutil import human, local_to_utc, parse, utcnow
from views.common import (MODES, PRIO_META, RECUR, STATUS_META, category_options, chip, esc, tiles)

FILTERS = ["All", "Today", "Pending", "In progress", "Completed", "Incomplete"]
_MATCH = {"Pending": {"pending"}, "In progress": {"active"}, "Completed": {"completed"},
          "Incomplete": {"incomplete", "late"}}


def _is_today(t, now, tz):
    today = now.astimezone(tz).date()
    s, e, d = parse(t["start_at"]), parse(t["end_at"]), parse(t["completed_at"])
    if d:
        return d.astimezone(tz).date() == today
    if not (s or e):
        return True
    lo = (s or e).astimezone(tz).date()
    hi = (e or s).astimezone(tz).date()
    return lo <= today <= hi


def _toggle(uid, t, tz):
    if t["completed_at"]:
        tasks.reopen(uid, t["id"])
    else:
        tasks.complete(uid, t["id"], tz)


@st.dialog("Task")
def task_dialog(user, tz, cats, t=None):
    uid, now = user["id"], utcnow().astimezone(tz)
    s0 = parse(t["start_at"]) if t else None
    e0 = parse(t["end_at"]) if t else None
    if not s0:
        s0 = (now + timedelta(minutes=5 - now.minute % 5)).replace(second=0)
    s0 = s0.astimezone(tz)
    e0 = (e0 or s0 + timedelta(hours=1)).astimezone(tz)
    ids, fmt = category_options(cats)
    with st.form("task_form", border=False):
        title = st.text_input("Title", value=t["title"] if t else "", max_chars=120)
        desc = st.text_area("Details", value=t["description"] if t else "", height=70)
        c1, c2 = st.columns(2)
        cat = c1.selectbox("Category", ids, format_func=fmt, index=ids.index(t["category_id"]) if t else 0)
        new_cat = c2.text_input("…or new category", placeholder="e.g. Wedding")
        prio = st.segmented_control("Priority", [1, 2, 3], default=t["priority"] if t else 2,
                                    format_func=lambda p: PRIO_META[p][0])
        sched = st.checkbox("Schedule with start & end time", value=bool(t and t["start_at"]))
        a, b, c, d = st.columns(4)
        sd, stt = a.date_input("Start date", s0.date()), b.time_input("Start", s0.time(), step=300)
        ed, ett = c.date_input("End date", e0.date()), d.time_input("End", e0.time(), step=300)
        mode = st.radio("Remind me", list(MODES), format_func=MODES.get, horizontal=True,
                        index=list(MODES).index(t["remind_mode"]) if t else 0)
        r1, r2, r3 = st.columns(3)
        r_s = r1.checkbox("At start", value=bool(t["remind_start"]) if t else True)
        r_e = r2.checkbox("At end", value=bool(t["remind_end"]) if t else True)
        before = r3.selectbox("Minutes before", [0, 5, 10, 15, 30, 60],
                              index=[0, 5, 10, 15, 30, 60].index(t["remind_before"]) if t else 0)
        rec = st.selectbox("Repeat", list(RECUR), format_func=RECUR.get,
                           index=list(RECUR).index(t["recurrence"]) if t else 0)
        if mode in ("email", "both") and not notifier.configured():
            st.caption("⚠️ Email isn't configured on this server yet — see the README (SMTP settings).")
        if st.form_submit_button("Save task", type="primary", width="stretch"):
            if not title.strip():
                return st.error("Give the task a title.")
            start = end = None
            if sched:
                start = local_to_utc(datetime.combine(sd, stt), tz)
                end = local_to_utc(datetime.combine(ed, ett), tz)
                if end <= start:
                    return st.error("End time must be after the start time.")
            elif mode != "none" or rec != "none":
                return st.error("Reminders and repeats need a schedule — tick “Schedule”.")
            if new_cat.strip():
                cat = categories.get_or_create(uid, new_cat)
            data = dict(title=title, description=desc, category_id=cat, priority=prio or 2, start_at=start,
                        end_at=end, remind_mode=mode, remind_start=int(r_s), remind_end=int(r_e),
                        remind_before=before, recurrence=rec)
            tasks.update(uid, t["id"], **data) if t else tasks.add(uid, **data)
            st.rerun()


def _goto_focus(tid):
    st.session_state.focus_task = tid
    st.session_state.nav = "Focus"


def _row(user, tz, t, cats_by_id, now):
    uid, s = user["id"], tasks.status(t, now)
    label, color = STATUS_META[s]
    done = bool(t["completed_at"])
    chips = [chip(label, color)]
    if (c := cats_by_id.get(t["category_id"])):
        chips.append(chip(f'{c["icon"]} {c["name"]}', c["color"]))
    if t["priority"] == 3:
        chips.append(chip("High", PRIO_META[3][1]))
    if t["start_at"]:
        chips.append(chip(f'🕒 {human(parse(t["start_at"]), tz, now)} → {human(parse(t["end_at"]), tz, now)}', plain=True))
    if t["remind_mode"] != "none":
        chips.append(chip({"email": "📧", "alarm": "🔔", "both": "📧🔔"}[t["remind_mode"]], plain=True))
    if t["recurrence"] != "none":
        chips.append(chip("🔁 " + t["recurrence"], plain=True))
    desc = f'<div class="desc">{esc(t["description"])}</div>' if t["description"] else ""
    with st.container(key=f"task_{t['id']}"):
        st.checkbox("done", value=done, key=f"chk_{t['id']}_{int(done)}", label_visibility="collapsed",
                    on_change=_toggle, args=(uid, t, tz))
        st.markdown(f'<div class="tcard" style="--c:{color}"><div class="tt{" done" if done else ""}">'
                    f'{esc(t["title"])}</div>{desc}<div class="meta">{"".join(chips)}</div></div>',
                    unsafe_allow_html=True)
        with st.popover("⋯"):
            if st.button("Edit", key=f"ed_{t['id']}", icon=":material/edit:", width="stretch"):
                task_dialog(user, tz, list(cats_by_id.values()), t)
            if not done:
                st.button("Focus", key=f"fo_{t['id']}", icon=":material/timer:", width="stretch",
                          on_click=_goto_focus, args=(t["id"],))
            if st.button("Delete", key=f"dl_{t['id']}", icon=":material/delete:", width="stretch"):
                tasks.delete(uid, t["id"])
                st.rerun()


def render(user, tz):
    uid, now = user["id"], utcnow()
    cats = categories.list_(uid)
    by_id = {c["id"]: c for c in cats}

    with st.container(key="row_quick"), st.form("quick", clear_on_submit=True, border=False):
        q, go = st.columns([6, 1], vertical_alignment="center")
        text = q.text_input("Quick add", placeholder="Quick add — “Call mom tomorrow 5pm #family !high”",
                            label_visibility="collapsed")
        if go.form_submit_button("＋", type="primary", width="stretch") and text.strip():
            p = tasks.parse_quick(text, tz, now)
            if p["title"]:
                cid = categories.get_or_create(uid, p["category"]) if p["category"] else None
                tasks.add(uid, p["title"], category_id=cid, priority=p["priority"],
                          start_at=p["start_at"], end_at=p["end_at"])
                st.toast(f"Added “{p['title']}”", icon="✅")
                st.rerun()

    allt = tasks.list_(uid)
    s = stats.summary(allt, now)
    st.markdown(tiles([("Pending", s["Pending"], "#f59e0b"), ("In progress", s["In progress"], "#8b5cf6"),
                       ("Completed", s["Completed"], "#22c55e"), ("Incomplete", s["Incomplete"], "#ef4444")]),
                unsafe_allow_html=True)

    flt = st.pills("Show", FILTERS, default="All", key="t_flt", label_visibility="collapsed") or "All"
    ids, fmt = category_options(cats)
    with st.container(key="row_filters"):
        f1, f2 = st.columns(2)
        cat = f1.selectbox("Category", ids, format_func=lambda i: "All categories" if i is None else fmt(i),
                           key="t_cat", label_visibility="collapsed")
        search = f2.text_input("Search", placeholder="🔍 Search", key="t_q", label_visibility="collapsed")

    rows = tasks.list_(uid, cat, search or None)
    if flt == "Today":
        rows = [t for t in rows if _is_today(t, now, tz)]
    elif flt in _MATCH:
        rows = [t for t in rows if tasks.status(t, now) in _MATCH[flt]]
    rows.sort(key=lambda t: tasks.sort_key(t, now))
    if not rows:
        st.info("Nothing here yet — tap ＋ to add a task." if not allt else "No tasks match this filter.")
    for t in rows:
        _row(user, tz, t, by_id, now)

    if st.button("＋", key="fab", type="primary", help="New task with reminders, repeat & category"):
        task_dialog(user, tz, cats)
