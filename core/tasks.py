"""Tasks: CRUD, status rules, recurrence and the quick-add parser."""
import re
from datetime import datetime, timedelta

from core import db
from core.timeutil import UTC, iso, local_to_utc, parse, shift, utcnow

PRIORITIES = {1: "Low", 2: "Normal", 3: "High"}
FIELDS = ("title", "description", "category_id", "priority", "start_at", "end_at", "remind_mode",
          "remind_start", "remind_end", "remind_before", "recurrence")
_RESET_ON_CHANGE = ("start_at", "end_at", "remind_mode", "remind_start", "remind_end", "remind_before")


def _clean(kw):
    out = {k: v for k, v in kw.items() if k in FIELDS}
    for k in ("start_at", "end_at"):
        if k in out:
            out[k] = iso(out[k])
    return out


def add(uid, title, **kw):
    kw = _clean(kw)
    now = iso(utcnow())
    cols = ["user_id", "title", "created_at", "updated_at", *[k for k in kw if k != "title"]]
    vals = [uid, title.strip(), now, now, *[v for k, v in kw.items() if k != "title"]]
    return db.execute(f"INSERT INTO tasks({','.join(cols)}) VALUES({','.join('?' * len(cols))})", vals)


def get(uid, tid):
    return db.one("SELECT * FROM tasks WHERE id=? AND user_id=?", (tid, uid))


def update(uid, tid, **kw):
    kw, cur = _clean(kw), get(uid, tid)
    if not cur or not kw:
        return
    sets = dict(kw, updated_at=iso(utcnow()))
    if any(k in kw and kw[k] != cur[k] for k in _RESET_ON_CHANGE):  # new schedule => re-arm reminders
        sets.update(email_start_sent=0, email_end_sent=0, ring_start_done=0, ring_end_done=0,
                    snooze_until=None)
    db.execute(f"UPDATE tasks SET {','.join(c + '=?' for c in sets)} WHERE id=? AND user_id=?",
               (*sets.values(), tid, uid))


def delete(uid, tid):
    db.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (tid, uid))


def list_(uid, category_id=None, q=None):
    sql, args = "SELECT * FROM tasks WHERE user_id=?", [uid]
    if category_id:
        sql += " AND category_id=?"
        args.append(category_id)
    if q:
        sql += " AND (title LIKE ? OR description LIKE ?)"
        args += [f"%{q}%"] * 2
    return db.query(sql, args)


def complete(uid, tid, tz=UTC):
    t = get(uid, tid)
    if not t or t["completed_at"]:
        return
    now = utcnow()
    db.execute("UPDATE tasks SET completed_at=?, updated_at=? WHERE id=? AND user_id=?",
               (iso(now), iso(now), tid, uid))
    if t["recurrence"] != "none" and t["start_at"]:
        _spawn_next(t, now, tz)


def reopen(uid, tid):
    db.execute("UPDATE tasks SET completed_at=NULL, updated_at=? WHERE id=? AND user_id=?",
               (iso(utcnow()), tid, uid))


def _spawn_next(t, now, tz):
    start, end = parse(t["start_at"]), parse(t["end_at"])
    for _ in range(400):  # skip occurrences that are already in the past
        start = shift(start, t["recurrence"], tz)
        end = shift(end, t["recurrence"], tz) if end else None
        if (end or start) > now:
            break
    add(t["user_id"], t["title"], description=t["description"], category_id=t["category_id"],
        priority=t["priority"], start_at=start, end_at=end, remind_mode=t["remind_mode"],
        remind_start=t["remind_start"], remind_end=t["remind_end"],
        remind_before=t["remind_before"], recurrence=t["recurrence"])


def status(t, now=None) -> str:
    """completed | late | incomplete | pending | active

    completed  - finished inside its window (or unscheduled)
    late       - finished after the end time (counts as incomplete in the tracker)
    incomplete - end time passed and never finished
    pending    - start time is still in the future
    active     - in progress (window open) or an open task with no schedule
    """
    now = now or utcnow()
    start, end, done = parse(t["start_at"]), parse(t["end_at"]), parse(t["completed_at"])
    if done:
        return "late" if end and done > end else "completed"
    if end and now > end:
        return "incomplete"
    if start and now < start:
        return "pending"
    return "active"


_ORDER = {"active": 0, "pending": 1, "incomplete": 2, "late": 3, "completed": 4}


def sort_key(t, now=None):
    s = status(t, now)
    ref = t["completed_at"] if t["completed_at"] else (t["start_at"] or t["end_at"] or "9999")
    if s in ("completed", "late"):  # newest finished first
        ref = "".join(chr(255 - ord(c)) if c.isdigit() else c for c in ref)
    return _ORDER[s], ref, -t["priority"]


# ---------------------------------------------------------------- quick add
_DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def parse_quick(text: str, tz, now: datetime | None = None) -> dict:
    """'Call mom tomorrow 5pm for 30m #family !high' -> fields for add()."""
    now = (now or utcnow()).astimezone(tz)
    out = {"category": None, "priority": 2, "start_at": None, "end_at": None}

    def grab(pattern, flags=re.I):
        nonlocal text
        m = re.search(pattern, text, flags)
        if m:
            text = (text[:m.start()] + " " + text[m.end():]).strip()
        return m

    if m := grab(r"(?:^|\s)#([\w-]+)"):
        out["category"] = m.group(1).replace("-", " ").title()
    if m := grab(r"(?:^|\s)!(high|med|normal|low|[123])\b"):
        out["priority"] = {"high": 3, "3": 3, "low": 1, "1": 1}.get(m.group(1).lower(), 2)
    dur = None
    if m := grab(r"\bfor\s+(\d+(?:\.\d+)?)\s*(h|hr|hrs|hours?|m|min|mins|minutes?)\b"):
        n = float(m.group(1))
        dur = timedelta(hours=n) if m.group(2).lower().startswith("h") else timedelta(minutes=n)
    day = None
    if m := grab(r"\b(\d{4}-\d{2}-\d{2})\b"):
        day = datetime.strptime(m.group(1), "%Y-%m-%d").date()
    elif grab(r"\btoday\b"):
        day = now.date()
    elif grab(r"\btomorrow\b"):
        day = now.date() + timedelta(days=1)
    elif m := grab(r"\b(?:on\s+)?(mon|tue|wed|thu|fri|sat|sun)[a-z]*\b"):
        ahead = (_DAYS.index(m.group(1).lower()) - now.weekday()) % 7 or 7
        day = now.date() + timedelta(days=ahead)
    clock = None
    if m := grab(r"\b(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b"):
        h, mi = int(m.group(1)) % 12, int(m.group(2) or 0)
        clock = (h + (12 if m.group(3).lower() == "pm" else 0), mi)
    elif m := grab(r"\b(?:at\s+)?([01]?\d|2[0-3]):([0-5]\d)\b"):
        clock = (int(m.group(1)), int(m.group(2)))
    if day or clock:
        h, mi = clock or (9, 0)
        start = datetime.combine(day or now.date(), datetime.min.time()).replace(hour=h, minute=mi)
        if not day and local_to_utc(start, tz) <= now:  # a bare time already passed => tomorrow
            start += timedelta(days=1)
        out["start_at"] = local_to_utc(start, tz)
        out["end_at"] = out["start_at"] + (dur or timedelta(hours=1))
    out["title"] = re.sub(r"\s+", " ", text).strip(" ,.-")
    return out
