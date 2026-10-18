"""All datetimes are stored as UTC ISO strings and shown in the user's zone."""
import calendar
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

FMT = "%Y-%m-%dT%H:%M:%S"
UTC = timezone.utc


def utcnow() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def iso(dt):
    if dt is None or isinstance(dt, str):
        return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime(FMT)


def parse(s):
    return datetime.strptime(s, FMT).replace(tzinfo=UTC) if s else None


def zone(name):
    try:
        return ZoneInfo(name) if name and name != "auto" else UTC
    except Exception:
        return UTC


def local_to_utc(naive: datetime, tz) -> datetime:
    return naive.replace(tzinfo=tz).astimezone(UTC)


def clock(dt: datetime) -> str:
    return dt.strftime("%I:%M %p").lstrip("0")


def human(dt, tz, now=None) -> str:
    """'Today 5:30 PM', 'Tomorrow 9:00 AM', 'Mon 20 Oct 9:00 AM'."""
    if dt is None:
        return ""
    loc = dt.astimezone(tz)
    today = (now or utcnow()).astimezone(tz).date()
    delta = (loc.date() - today).days
    day = {0: "Today", 1: "Tomorrow", -1: "Yesterday"}.get(delta) or f"{loc:%a %d %b}"
    return f"{day} {clock(loc)}"


def add_months(dt: datetime, n: int = 1) -> datetime:
    m = dt.month - 1 + n
    y, m = dt.year + m // 12, m % 12 + 1
    return dt.replace(year=y, month=m, day=min(dt.day, calendar.monthrange(y, m)[1]))


def shift(dt: datetime, recurrence: str, tz) -> datetime:
    """Move a UTC datetime to its next occurrence, keeping local wall-clock time."""
    loc = dt.astimezone(tz).replace(tzinfo=None)
    if recurrence == "daily":
        loc += timedelta(days=1)
    elif recurrence == "weekly":
        loc += timedelta(weeks=1)
    else:
        loc = add_months(loc, 1)
    return local_to_utc(loc, tz)
