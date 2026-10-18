import html

import streamlit as st

from core import auth
from core.timeutil import zone

STATUS_META = {  # status -> (label, colour)
    "completed": ("Completed", "#22c55e"), "late": ("Done late", "#f97316"),
    "incomplete": ("Incomplete", "#ef4444"), "pending": ("Pending", "#f59e0b"),
    "active": ("In progress", "#6366f1")}
PRIO_META = {1: ("Low", "#64748b"), 2: ("Normal", "#0ea5e9"), 3: ("High", "#ef4444")}
MODES = {"none": "No reminder", "email": "📧 Email", "alarm": "🔔 Ring + popup", "both": "📧🔔 Both"}
RECUR = {"none": "Doesn't repeat", "daily": "Daily", "weekly": "Weekly", "monthly": "Monthly"}


def user_tz(user: dict):
    """Timezone: explicit setting, else the browser's, else UTC. Also remembers it for email reminders."""
    name = user["settings"].get("tz", "auto")
    if name == "auto":
        name = getattr(st.context, "timezone", None) or "UTC"
        if user["settings"].get("tz_seen") != name:
            auth.save_settings(user["id"], tz_seen=name)
    elif user["settings"].get("tz_seen") != name:
        auth.save_settings(user["id"], tz_seen=name)
    return zone(name)


def esc(s) -> str:
    return html.escape(str(s or ""))


def chip(text, color=None, plain=False) -> str:
    style = f' style="--c:{color}"' if color else ""
    return f'<span class="chip{" plain" if plain else ""}"{style}>{esc(text)}</span>'


def category_options(cats):
    ids = [None] + [c["id"] for c in cats]
    by_id = {c["id"]: c for c in cats}
    fmt = lambda i: "— none —" if i is None else f'{by_id[i]["icon"]} {by_id[i]["name"]}'
    return ids, fmt


def tiles(items, three=False) -> str:
    """items: [(label, value, color)] -> responsive grid that never stacks into tall blocks."""
    body = "".join(f'<div class="tile" style="--c:{c}"><b>{v}</b><span>{l}</span></div>' for l, v, c in items)
    return f'<div class="tiles{" three" if three else ""}">{body}</div>'


def ring(pct, label, color="#22d3ee", size=""):
    return f'<div class="ring {size}" style="--p:{max(0, min(100, pct))};--a:{color}"><span>{label}</span></div>'
