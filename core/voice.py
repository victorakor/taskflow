"""Builds the sentences the voice aid speaks (speech itself happens in the browser)."""
from core import tasks as T
from core.timeutil import clock, human, parse, utcnow


def _when(t, tz, now):
    s, e = parse(t["start_at"]), parse(t["end_at"])
    if s and e:
        return f"from {human(s, tz, now)} to {clock(e.astimezone(tz))}"
    return f"at {human(s or e, tz, now)}" if (s or e) else ""


def brief(tasks, name, tz, now=None, limit=12) -> str:
    """Spoken overview of every open task, grouped by state."""
    now = now or utcnow()
    groups = {"active": [], "pending": [], "incomplete": [], "late": []}
    done = 0
    for t in tasks:
        s = T.status(t, now)
        if s == "completed":
            done += 1
        elif s in groups:
            groups[s].append(t)
    groups["incomplete"] += groups.pop("late")
    open_n = sum(len(v) for v in groups.values())
    if not tasks:
        return f"Hello {name}. You have no tasks yet. Add one to get started."
    parts = [f"Hello {name}. You have {open_n} open {'task' if open_n == 1 else 'tasks'} "
             f"and {done} completed."]
    labels = {"active": "In progress", "pending": "Coming up", "incomplete": "Missed"}
    left = limit
    for key, label in labels.items():
        items = sorted(groups[key], key=lambda t: T.sort_key(t, now))[:left]
        left -= len(items)
        if items:
            parts.append(f"{label}: " + "; ".join(f"{t['title']} {_when(t, tz, now)}".strip() for t in items) + ".")
    if open_n > limit:
        parts.append(f"And {open_n - limit} more.")
    return " ".join(parts)


def reminder(t, kind, tz, now=None) -> str:
    now = now or utcnow()
    if kind == "start":
        return f"Reminder. {t['title']} starts {_when(t, tz, now) or 'now'}."
    return f"Reminder. {t['title']} is due {human(parse(t['end_at']), tz, now)}."
