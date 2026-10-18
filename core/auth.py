"""Accounts: email + password (PBKDF2), optional Google sign-in, remember-me sessions."""
import hashlib
import hmac
import json
import re
import secrets
import time
from datetime import timedelta

from core import db
from core.config import SESSION_DAYS
from core.timeutil import iso, parse, utcnow

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DEFAULT_CATEGORIES = [("Personal", "#6366f1", "🏠"), ("Work", "#0ea5e9", "💼"),
                      ("Study", "#f59e0b", "📚"), ("Health", "#22c55e", "💪")]
DEFAULT_SETTINGS = {"tz": "auto", "voice": False, "digest_min": 0}
_fails: dict[str, tuple[int, float]] = {}


def _hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000).hex()


def _seed(uid: int):
    for name, color, icon in DEFAULT_CATEGORIES:
        db.execute("INSERT OR IGNORE INTO categories(user_id,name,color,icon) VALUES(?,?,?,?)",
                   (uid, name, color, icon))


def register(email: str, name: str, password: str) -> dict:
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        raise ValueError("Enter a valid email address.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    if not name.strip():
        raise ValueError("Enter your name.")
    if db.one("SELECT id FROM users WHERE email=?", (email,)):
        raise ValueError("An account with this email already exists.")
    salt = secrets.token_hex(16)
    uid = db.execute(
        "INSERT INTO users(email,name,pw_hash,pw_salt,settings,created_at) VALUES(?,?,?,?,?,?)",
        (email, name.strip(), _hash(password, salt), salt, json.dumps(DEFAULT_SETTINGS), iso(utcnow())))
    _seed(uid)
    return get_user(uid)


def login(email: str, password: str) -> dict:
    email = email.strip().lower()
    count, until = _fails.get(email, (0, 0))
    if count >= 5 and time.time() < until:
        raise ValueError("Too many attempts. Try again in a few minutes.")
    u = db.one("SELECT * FROM users WHERE email=?", (email,))
    ok = bool(u and u["pw_hash"] and hmac.compare_digest(u["pw_hash"], _hash(password, u["pw_salt"])))
    if not ok:
        _fails[email] = (count + 1, time.time() + 300)
        raise ValueError("Incorrect email or password.")
    _fails.pop(email, None)
    return get_user(u["id"])


def oauth_user(email: str, name: str, picture: str | None) -> dict:
    """Sign in (or create) an account from a verified Google identity.
    Existing password accounts with the same email are linked automatically."""
    email = email.strip().lower()
    u = db.one("SELECT id FROM users WHERE email=?", (email,))
    if u:
        db.execute("UPDATE users SET avatar_url=? WHERE id=?", (picture, u["id"]))
        return get_user(u["id"])
    uid = db.execute("INSERT INTO users(email,name,avatar_url,settings,created_at) VALUES(?,?,?,?,?)",
                     (email, name or email.split("@")[0], picture, json.dumps(DEFAULT_SETTINGS),
                      iso(utcnow())))
    _seed(uid)
    return get_user(uid)


def get_user(uid: int):
    u = db.one("SELECT * FROM users WHERE id=?", (uid,))
    if u:
        u["settings"] = {**DEFAULT_SETTINGS, **json.loads(u["settings"] or "{}")}
    return u


def update_user(uid: int, **fields):
    allowed = {"name", "avatar", "avatar_url", "avatar_pref"}
    cols = [k for k in fields if k in allowed]
    if cols:
        db.execute(f"UPDATE users SET {','.join(c + '=?' for c in cols)} WHERE id=?",
                   (*[fields[c] for c in cols], uid))


def save_settings(uid: int, **changes):
    s = get_user(uid)["settings"]
    s.update(changes)
    db.execute("UPDATE users SET settings=? WHERE id=?", (json.dumps(s), uid))
    return s


def change_password(uid: int, old: str, new: str):
    u = db.one("SELECT * FROM users WHERE id=?", (uid,))
    if u["pw_hash"] and not hmac.compare_digest(u["pw_hash"], _hash(old, u["pw_salt"])):
        raise ValueError("Current password is incorrect.")
    if len(new) < 8:
        raise ValueError("New password must be at least 8 characters.")
    salt = secrets.token_hex(16)
    db.execute("UPDATE users SET pw_hash=?, pw_salt=? WHERE id=?", (_hash(new, salt), salt, uid))


# --- remember-me sessions (token stored hashed; cookie holds the raw token) ---
def _th(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(uid: int) -> str:
    token = secrets.token_urlsafe(32)
    db.execute("DELETE FROM sessions WHERE expires_at < ?", (iso(utcnow()),))
    db.execute("INSERT INTO sessions VALUES(?,?,?)",
               (_th(token), uid, iso(utcnow() + timedelta(days=SESSION_DAYS))))
    return token


def user_from_token(token):
    if not token or not isinstance(token, str):
        return None
    row = db.one("SELECT * FROM sessions WHERE token_hash=?", (_th(token),))
    if not row or parse(row["expires_at"]) < utcnow():
        return None
    return get_user(row["user_id"])


def end_session(token):
    if token and isinstance(token, str):
        db.execute("DELETE FROM sessions WHERE token_hash=?", (_th(token),))
