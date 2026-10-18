from datetime import datetime, timedelta

import pytest

from core import auth, backup, categories, notes, reminders, stats, tasks, voice
from core.timeutil import UTC, iso, parse, utcnow, zone

LAGOS = zone("Africa/Lagos")


def mk(uid, title, start=None, end=None, **kw):
    return tasks.get(uid, tasks.add(uid, title, start_at=start, end_at=end, **kw))


def test_auth_flow(user):
    assert auth.login("ADA@example.com", "password123")["id"] == user["id"]
    with pytest.raises(ValueError):
        auth.login("ada@example.com", "wrong-pass")
    with pytest.raises(ValueError):
        auth.register("ada@example.com", "Dup", "password123")
    tok = auth.create_session(user["id"])
    assert auth.user_from_token(tok)["id"] == user["id"]
    auth.end_session(tok)
    assert auth.user_from_token(tok) is None
    assert len(categories.list_(user["id"])) == 4


def test_google_signin_links_existing_account(user):
    u = auth.oauth_user("ada@example.com", "Ada", "https://x/pic.png")
    assert u["id"] == user["id"] and u["avatar_url"] == "https://x/pic.png"


def test_status_rules(user):
    now, u = utcnow(), user["id"]
    h = timedelta(hours=1)
    assert tasks.status(mk(u, "a", now + h, now + 2 * h), now) == "pending"
    assert tasks.status(mk(u, "b", now - h, now + h), now) == "active"
    assert tasks.status(mk(u, "c", now - 2 * h, now - h), now) == "incomplete"
    assert tasks.status(mk(u, "d"), now) == "active"
    t = mk(u, "e", now - 2 * h, now + h)
    tasks.complete(u, t["id"])
    assert tasks.status(tasks.get(u, t["id"]), now) == "completed"
    late = mk(u, "f", now - 3 * h, now - 2 * h)
    tasks.complete(u, late["id"])
    assert tasks.status(tasks.get(u, late["id"])) == "late"


def test_stats_buckets(user):
    u, now, h = user["id"], utcnow(), timedelta(hours=1)
    ok = mk(u, "ok", now - h, now + h)
    tasks.complete(u, ok["id"])
    mk(u, "missed", now - 3 * h, now - 2 * h)
    mk(u, "soon", now + h, now + 2 * h)
    mk(u, "now", now - h, now + h)
    s = stats.summary(tasks.list_(u))
    assert (s["Completed"], s["Incomplete"], s["Pending"], s["In progress"]) == (1, 1, 1, 1)
    assert s["rate"] == 50
    assert stats.streak(tasks.list_(u), UTC) == 1


def test_recurrence_spawns_next(user):
    u, now = user["id"], utcnow()
    t = mk(u, "daily", now - timedelta(hours=1), now + timedelta(hours=1), recurrence="daily")
    tasks.complete(u, t["id"], LAGOS)
    rows = tasks.list_(u)
    assert len(rows) == 2
    nxt = [r for r in rows if not r["completed_at"]][0]
    assert parse(nxt["start_at"]) - parse(t["start_at"]) == timedelta(days=1)


def test_editing_schedule_rearms_reminders(user):
    u, now = user["id"], utcnow()
    t = mk(u, "x", now, now + timedelta(hours=1), remind_mode="alarm")
    reminders.dismiss(u, t["id"], "start")
    assert tasks.get(u, t["id"])["ring_start_done"] == 1
    tasks.update(u, t["id"], title="renamed")
    assert tasks.get(u, t["id"])["ring_start_done"] == 1          # unrelated edit keeps state
    tasks.update(u, t["id"], start_at=now + timedelta(hours=2))
    assert tasks.get(u, t["id"])["ring_start_done"] == 0          # new time re-arms


def test_alarm_due_dismiss_snooze(user):
    u, now = user["id"], utcnow()
    mk(u, "future", now + timedelta(hours=2), now + timedelta(hours=3), remind_mode="alarm")
    t = mk(u, "ring", now - timedelta(minutes=1), now + timedelta(hours=1), remind_mode="both")
    due = reminders.due_alarms(u)
    assert [(d[0]["id"], d[1]) for d in due] == [(t["id"], "start")]
    reminders.snooze(u, t["id"], 5)
    assert reminders.due_alarms(u) == []
    reminders.dismiss(u, t["id"], "start")
    assert reminders.due_alarms(u) == []


def test_email_reminders_due_and_marked(user):
    u, now = user["id"], utcnow()
    t = mk(u, "mail", now - timedelta(minutes=2), now + timedelta(hours=1), remind_mode="email", remind_end=0)
    mk(u, "stale", now - timedelta(days=3), now + timedelta(hours=1), remind_mode="email")
    due = list(reminders.due_emails())
    assert [(d["id"], k) for d, k in due] == [(t["id"], "start")]
    reminders.mark_email_sent(t["id"], "start")
    assert list(reminders.due_emails()) == []   # stale one was silently marked, not emailed


def test_quick_add_parser():
    now = datetime(2026, 10, 16, 12, 0, tzinfo=UTC)
    r = tasks.parse_quick("Call mom tomorrow 5pm for 30m #family !high", LAGOS, now)
    assert r["title"] == "Call mom" and r["category"] == "Family" and r["priority"] == 3
    assert r["start_at"].astimezone(LAGOS).strftime("%Y-%m-%d %H:%M") == "2026-10-17 17:00"
    assert r["end_at"] - r["start_at"] == timedelta(minutes=30)
    assert tasks.parse_quick("Buy milk", LAGOS, now)["start_at"] is None
    r = tasks.parse_quick("Gym at 6:00", LAGOS, now)       # 13:00 Lagos now => 6:00 is tomorrow
    assert r["start_at"].astimezone(LAGOS).day == 17


def test_notes_and_categories(user):
    u = user["id"]
    cid = categories.get_or_create(u, "Wedding")
    assert categories.get_or_create(u, "wedding") == cid
    notes.add(u, "Venue ideas", "- a\n- b", cid)
    mk(u, "Book venue", category_id=cid)
    c = [c for c in categories.list_(u) if c["id"] == cid][0]
    assert (c["n_tasks"], c["n_notes"]) == (1, 1)
    assert len(notes.list_(u, q="venue")) == 1
    categories.delete(u, cid)
    assert tasks.list_(u)[0]["category_id"] is None


def test_backup_roundtrip_and_legacy(user):
    u = user["id"]
    mk(u, "keep me", utcnow(), utcnow() + timedelta(hours=1))
    notes.add(u, "n", "body")
    raw = backup.export_json(u)
    assert backup.import_json(u, raw) == (1, 1)
    legacy = b'[{"ID":"T001","TITLE":"washing plate","STATUS":"completed","CREATED_AT":"2026-10-16 12:59:13","MODIFIED_AT":"2026-10-16 13:37:40"},{"ID":"T002","TITLE":"reading","STATUS":"created","CREATED_AT":"x","MODIFIED_AT":"y"}]'
    assert backup.import_json(u, legacy) == (2, 0)
    assert b"washing plate" in backup.export_csv(u, LAGOS)


def test_voice_brief(user):
    u, now = user["id"], utcnow()
    mk(u, "Write report", now - timedelta(hours=1), now + timedelta(hours=1))
    mk(u, "Gym", now + timedelta(hours=3), now + timedelta(hours=4))
    text = voice.brief(tasks.list_(u), "Ada", LAGOS, now)
    assert "Ada" in text and "Write report" in text and "Gym" in text and "2 open tasks" in text
