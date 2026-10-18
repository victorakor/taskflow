"""Export / import: JSON backup, CSV export, and import of the legacy task.json."""
import csv
import io
import json

from core import categories, db, notes, tasks
from core.timeutil import iso, parse, utcnow

VERSION = 1


def export_json(uid) -> bytes:
    cats = db.query("SELECT id,name,color,icon FROM categories WHERE user_id=?", (uid,))
    data = {"app": "taskflow", "version": VERSION,
            "categories": cats,
            "tasks": db.query("SELECT * FROM tasks WHERE user_id=?", (uid,)),
            "notes": db.query("SELECT * FROM notes WHERE user_id=?", (uid,))}
    return json.dumps(data, indent=2, default=str).encode()


def export_csv(uid, tz) -> bytes:
    names = {c["id"]: c["name"] for c in categories.list_(uid)}
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["title", "category", "priority", "status", "start", "end", "completed", "description"])
    for t in tasks.list_(uid):
        def f(s):
            d = parse(s)
            return d.astimezone(tz).strftime("%Y-%m-%d %H:%M") if d else ""
        w.writerow([t["title"], names.get(t["category_id"], ""), tasks.PRIORITIES[t["priority"]],
                    tasks.status(t), f(t["start_at"]), f(t["end_at"]), f(t["completed_at"]), t["description"]])
    return out.getvalue().encode()


def import_json(uid, raw: bytes) -> tuple[int, int]:
    """Returns (tasks, notes) imported. Accepts TaskFlow backups and the legacy list format."""
    data = json.loads(raw)
    if isinstance(data, list):
        return _legacy(uid, data), 0
    if data.get("app") != "taskflow":
        raise ValueError("This file is not a TaskFlow backup.")
    cmap = {c["id"]: categories.get_or_create(uid, c["name"], c.get("color", "#6366f1"), c.get("icon", "📁"))
            for c in data.get("categories", [])}
    for t in data.get("tasks", []):
        tid = tasks.add(uid, t["title"], description=t.get("description", ""),
                        category_id=cmap.get(t.get("category_id")), priority=t.get("priority", 2),
                        start_at=t.get("start_at"), end_at=t.get("end_at"),
                        remind_mode=t.get("remind_mode", "none"), remind_start=t.get("remind_start", 1),
                        remind_end=t.get("remind_end", 1), remind_before=t.get("remind_before", 0),
                        recurrence=t.get("recurrence", "none"))
        if t.get("completed_at"):
            db.execute("UPDATE tasks SET completed_at=? WHERE id=?", (t["completed_at"], tid))
    for n in data.get("notes", []):
        notes.add(uid, n["title"], n.get("body", ""), cmap.get(n.get("category_id")), bool(n.get("pinned")))
    return len(data.get("tasks", [])), len(data.get("notes", []))


def _legacy(uid, items) -> int:
    """Old CLI format: ID, TITLE, STATUS, CREATED_AT, MODIFIED_AT (local, naive timestamps)."""
    n = 0
    for it in items:
        if not isinstance(it, dict) or "TITLE" not in it:
            raise ValueError("Unrecognised file format.")
        tid = tasks.add(uid, it["TITLE"])
        if str(it.get("STATUS", "")).lower() == "completed":
            done = it.get("MODIFIED_AT", "")
            try:
                from datetime import datetime
                done = iso(datetime.strptime(done, "%Y-%m-%d %H:%M:%S"))
            except ValueError:
                done = iso(utcnow())
            db.execute("UPDATE tasks SET completed_at=? WHERE id=?", (done, tid))
        n += 1
    return n
