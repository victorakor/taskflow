from datetime import timedelta

import altair as alt
import streamlit as st

from core import categories, stats, tasks
from core.timeutil import human, parse, utcnow
from views.common import STATUS_META, ring, tiles

RANGES = {"7 days": 7, "30 days": 30, "All time": None}


def _ref(t):
    return parse(t["end_at"] or t["start_at"] or t["created_at"])


def render(user, tz):
    uid, now = user["id"], utcnow()
    rng = st.pills("Range", list(RANGES), default="30 days", label_visibility="collapsed") or "30 days"
    days = RANGES[rng]
    everything = tasks.list_(uid)
    rows = [t for t in everything if not days or now - timedelta(days=days) <= _ref(t) <= now + timedelta(days=days)]
    s = stats.summary(rows, now)

    if not rows:
        return st.info("Complete or schedule a few tasks and your progress shows up here.")

    rate = s["rate"]
    st.markdown(f'<div class="hero">{ring(rate or 0, f"{rate}%" if rate is not None else "—", "#22c55e", "mid")}'
                f'<div><div class="big">On-time completion</div><div class="sub">Finished inside the set time window, out of '
                f'every task whose window has closed.</div></div></div>', unsafe_allow_html=True)
    st.markdown(tiles([(k, s[k], c) for k, c in stats.COLORS.items()]), unsafe_allow_html=True)
    st.markdown(tiles([("🔥 Streak", f"{stats.streak(everything, tz, now)}d", "#f97316"),
                       ("⏱ Focus today", f"{stats.focus_minutes_today(uid, tz, now)}m", "#22d3ee"),
                       ("Finished late", s["late"], "#ec4899")], three=True), unsafe_allow_html=True)

    if True:
        left = right = st.container()
    with left:
        st.markdown("### Breakdown")
        df = stats.distribution(rows, now)
        st.altair_chart(alt.Chart(df).mark_arc(innerRadius=52, outerRadius=88).encode(
            theta="Count:Q", color=alt.Color("Status:N", legend=alt.Legend(orient="bottom", title=None),
                                            scale=alt.Scale(domain=list(stats.COLORS), range=list(stats.COLORS.values()))),
            tooltip=["Status", "Count"]).properties(height=230), width="stretch")
    with right:
        st.markdown("### Last 14 days")
        d = stats.daily(everything, tz, 14, now).melt("Day", var_name="Status", value_name="Tasks")
        st.altair_chart(alt.Chart(d).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
            x=alt.X("Day:N", sort=None, title=None, axis=alt.Axis(labelAngle=-60)), y=alt.Y("Tasks:Q", title=None),
            color=alt.Color("Status:N", legend=alt.Legend(orient="bottom", title=None),
                            scale=alt.Scale(domain=["Completed", "Incomplete"], range=["#22c55e", "#ef4444"])),
            tooltip=["Day", "Status", "Tasks"]).properties(height=220), width="stretch")

    cat_df = stats.by_category(rows, categories.list_(uid), now)
    with st.expander("By category", expanded=True):
        st.dataframe(cat_df, hide_index=True, width="stretch", column_config={
            "Done %": st.column_config.ProgressColumn("Done %", min_value=0, max_value=100, format="%d%%")})

    missed = sorted([t for t in rows if tasks.status(t, now) in ("incomplete", "late")], key=lambda t: t["end_at"] or "", reverse=True)
    if missed:
        with st.expander(f"Missed windows ({len(missed)})"):
            for t in missed[:30]:
                label = STATUS_META[tasks.status(t, now)][0]
                a, b = st.columns([5, 2], vertical_alignment="center")
                a.markdown(f"**{t['title']}**  \n<span class='sub'>{label} · was due {human(parse(t['end_at']), tz, now)}</span>"
                           if t["end_at"] else f"**{t['title']}**", unsafe_allow_html=True)
                if not t["completed_at"] and b.button("Mark done", key=f"md_{t['id']}", width="stretch"):
                    tasks.complete(uid, t["id"], tz)
                    st.rerun()
