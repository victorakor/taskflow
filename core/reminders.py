"""Reminder triggers shared by the email scheduler and the in-app ring/popup."""
from datetime import timedelta

from core import db
from core.timeutil import iso, parse, utcnow

KINDS = ("start", "end")
RING_WINDOW = timedelta(hours=12)    # don't ring for reminders older than this
EMAIL_WINDOW = timedelta(hours=24)   # don't email for reminders older than this


def trigger(t, kind):
    at = parse(t["start_at" if kind == "start" else "end_at"])
    return at - timedelta(minutes=t["remind_before"] or 0) if at else None


def _armed(t, kind):
    return bool(t[f"remind_{kind}"]) and trigger(t, kind) is not None


# ------------------------------------------------------------ ring + popup
def due_alarms(uid, now=None):
    now = now or utcnow()
    rows = db.query("SELECT * FROM tasks WHERE user_id=? AND completed_at IS NULL "
                    "AND remind_mode IN ('alarm','both')", (uid,))
    out = []
    for t in rows:
        if t["snooze_until"] and parse(t["snooze_until"]) > now:
            continue
        for kind in KINDS:
            trg = trigger(t, kind) if _armed(t, kind) else None
            if trg and not t[f"ring_{kind}_done"] and trg <= now and now - trg < RING_WINDOW:
                out.append((t, kind, trg))
    return [(t, k) for t, k, _ in sorted(out, key=lambda x: x[2])]


def dismiss(uid, tid, kind):
    db.execute(f"UPDATE tasks SET ring_{kind}_done=1, snooze_until=NULL WHERE id=? AND user_id=?",
               (tid, uid))


def snooze(uid, tid, minutes=5):
    db.execute("UPDATE tasks SET snooze_until=? WHERE id=? AND user_id=?",
               (iso(utcnow() + timedelta(minutes=minutes)), tid, uid))


# ------------------------------------------------------------------- email
def due_emails(now=None):
    """Yield (task+user row, kind). Stale reminders are marked sent without emailing."""
    now = now or utcnow()
    rows = db.query("""SELECT t.*, u.email AS user_email, u.name AS user_name, u.settings AS user_settings
                       FROM tasks t JOIN users u ON u.id=t.user_id
                       WHERE t.completed_at IS NULL AND t.remind_mode IN ('email','both')""")
    for t in rows:
        for kind in KINDS:
            trg = trigger(t, kind) if _armed(t, kind) else None
            if not trg or t[f"email_{kind}_sent"] or trg > now:
                continue
            if now - trg > EMAIL_WINDOW:
                mark_email_sent(t["id"], kind)
                continue
            yield t, kind


def mark_email_sent(tid, kind):
    db.execute(f"UPDATE tasks SET email_{kind}_sent=1 WHERE id=?", (tid,))
