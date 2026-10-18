from core import db
from core.timeutil import iso, utcnow


def add(uid, title, body="", category_id=None, pinned=False):
    now = iso(utcnow())
    return db.execute(
        "INSERT INTO notes(user_id,title,body,category_id,pinned,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
        (uid, title.strip(), body, category_id, int(pinned), now, now))


def update(uid, nid, **kw):
    cols = [k for k in kw if k in ("title", "body", "category_id", "pinned")]
    if cols:
        db.execute(f"UPDATE notes SET {','.join(c + '=?' for c in cols)}, updated_at=? "
                   "WHERE id=? AND user_id=?", (*[kw[c] for c in cols], iso(utcnow()), nid, uid))


def delete(uid, nid):
    db.execute("DELETE FROM notes WHERE id=? AND user_id=?", (nid, uid))


def list_(uid, category_id=None, q=None):
    sql, args = "SELECT * FROM notes WHERE user_id=?", [uid]
    if category_id:
        sql += " AND category_id=?"
        args.append(category_id)
    if q:
        sql += " AND (title LIKE ? OR body LIKE ?)"
        args += [f"%{q}%"] * 2
    return db.query(sql + " ORDER BY pinned DESC, updated_at DESC", args)
