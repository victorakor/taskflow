"""Progress tracker maths."""
from collections import Counter
from datetime import timedelta

import pandas as pd

from core import tasks as T
from core.timeutil import parse, utcnow

COLORS = {"Completed": "#22c55e", "In progress": "#6366f1", "Pending": "#f59e0b", "Incomplete": "#ef4444"}


def bucket(t, now=None) -> str:
    return {"completed": "Completed", "late": "Incomplete", "incomplete": "Incomplete",
            "pending": "Pending", "active": "In progress"}[T.status(t, now)]


def summary(tasks, now=None) -> dict:
    now = now or utcnow()
    c = Counter(bucket(t, now) for t in tasks)
    on_time, late = c["Completed"], sum(1 for t in tasks if T.status(t, now) == "late")
    closed = c["Completed"] + c["Incomplete"]
    return {**{k: c[k] for k in COLORS}, "total": len(tasks), "late": late, "closed": closed,
            "rate": round(100 * c["Completed"] / closed) if closed else None,
            "overall": round(100 * on_time / len(tasks)) if tasks else 0}


def distribution(tasks, now=None) -> pd.DataFrame:
    s = summary(tasks, now)
    return pd.DataFrame({"Status": list(COLORS), "Count": [s[k] for k in COLORS]})


def daily(tasks, tz, days=14, now=None) -> pd.DataFrame:
    """Per local day: tasks finished on time vs. tasks whose window closed unfinished."""
    now = now or utcnow()
    today = now.astimezone(tz).date()
    idx = [today - timedelta(days=i) for i in range(days - 1, -1, -1)]
    done, missed = Counter(), Counter()
    for t in tasks:
        s = T.status(t, now)
        if s == "completed" and t["completed_at"]:
            done[parse(t["completed_at"]).astimezone(tz).date()] += 1
        elif s in ("incomplete", "late"):
            missed[parse(t["end_at"]).astimezone(tz).date()] += 1
    return pd.DataFrame({"Day": [d.strftime("%a %d") for d in idx],
                         "Completed": [done[d] for d in idx], "Incomplete": [missed[d] for d in idx]})


def streak(tasks, tz, now=None) -> int:
    now = now or utcnow()
    days = {parse(t["completed_at"]).astimezone(tz).date() for t in tasks
            if T.status(t, now) == "completed" and t["completed_at"]}
    d, n = now.astimezone(tz).date(), 0
    if d not in days:
        d -= timedelta(days=1)
    while d in days:
        n, d = n + 1, d - timedelta(days=1)
    return n


def by_category(tasks, cats, now=None) -> pd.DataFrame:
    names = {c["id"]: f'{c["icon"]} {c["name"]}' for c in cats}
    rows = {}
    for t in tasks:
        r = rows.setdefault(names.get(t["category_id"], "No category"), Counter())
        r[bucket(t, now)] += 1
    data = [{"Category": k, **{s: v[s] for s in COLORS}, "Total": sum(v.values()),
             "Done %": round(100 * v["Completed"] / sum(v.values()))} for k, v in rows.items()]
    return pd.DataFrame(data, columns=["Category", *COLORS, "Total", "Done %"])


def focus_minutes_today(uid, tz, now=None) -> int:
    from core import db
    now = now or utcnow()
    rows = db.query("SELECT minutes, ended_at FROM focus_log WHERE user_id=?", (uid,))
    today = now.astimezone(tz).date()
    return sum(r["minutes"] for r in rows if parse(r["ended_at"]).astimezone(tz).date() == today)
