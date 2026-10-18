"""Categories group related tasks AND notes (e.g. 'Wedding', 'Exam prep')."""
from core import db


def list_(uid):
    return db.query(
        """SELECT c.*, (SELECT COUNT(*) FROM tasks t WHERE t.category_id=c.id) AS n_tasks,
                  (SELECT COUNT(*) FROM notes n WHERE n.category_id=c.id) AS n_notes
           FROM categories c WHERE c.user_id=? ORDER BY c.name COLLATE NOCASE""", (uid,))


def get_or_create(uid, name, color="#6366f1", icon="📁"):
    name = name.strip()
    row = db.one("SELECT id FROM categories WHERE user_id=? AND name=? COLLATE NOCASE", (uid, name))
    return row["id"] if row else db.execute(
        "INSERT INTO categories(user_id,name,color,icon) VALUES(?,?,?,?)", (uid, name, color, icon))


def update(uid, cid, name, color, icon):
    db.execute("UPDATE categories SET name=?, color=?, icon=? WHERE id=? AND user_id=?",
               (name.strip(), color, icon or "📁", cid, uid))


def delete(uid, cid):
    db.execute("DELETE FROM categories WHERE id=? AND user_id=?", (cid, uid))
