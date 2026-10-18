"""Email delivery over SMTP (Gmail, Outlook, Resend SMTP, Mailgun, ...)."""
import html
import smtplib
from email.message import EmailMessage

from core import config
from core.timeutil import human, parse, utcnow, zone


def configured() -> bool:
    return bool(config.get("SMTP_HOST") and config.get("SMTP_USER") and config.get("SMTP_PASSWORD"))


def send(to: str, subject: str, text: str, html_body: str | None = None):
    host, user = config.get("SMTP_HOST"), config.get("SMTP_USER")
    port = int(config.get("SMTP_PORT", "587") or 587)
    msg = EmailMessage()
    msg["Subject"], msg["To"] = subject, to
    msg["From"] = config.get("SMTP_FROM") or f"{config.APP_NAME} <{user}>"
    msg.set_content(text)
    if html_body:
        msg.add_alternative(html_body, subtype="html")
    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=20) as s:
            s.login(user, config.get("SMTP_PASSWORD"))
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=20) as s:
            s.starttls()
            s.login(user, config.get("SMTP_PASSWORD"))
            s.send_message(msg)


def task_email(t: dict, kind: str, tz_name: str):
    """Build (subject, text, html) for a start/end reminder."""
    tz, now = zone(tz_name), utcnow()
    at = parse(t["start_at" if kind == "start" else "end_at"])
    lead = t.get("remind_before") or 0
    verb = ("starts" if kind == "start" else "is due")
    when = f"in {lead} min ({human(at, tz, now)})" if lead else f"now ({human(at, tz, now)})"
    subject = f"{'⏰' if kind == 'start' else '⌛'} {t['title']} {verb} {'in ' + str(lead) + ' min' if lead else 'now'}"
    text = f"Hi {t['user_name']},\n\nYour task \"{t['title']}\" {verb} {when}.\n\n— {config.APP_NAME}"
    desc = f"<p style='color:#64748b'>{html.escape(t['description'])}</p>" if t.get("description") else ""
    body = (f"<div style='font-family:system-ui,sans-serif;max-width:480px;margin:auto;padding:20px;"
            f"border:1px solid #e2e8f0;border-radius:14px'><div style='font-size:13px;color:#6366f1;"
            f"font-weight:700'>{config.APP_NAME}</div><h2 style='margin:8px 0'>{html.escape(t['title'])}</h2>"
            f"<p>Task {verb} <b>{html.escape(when)}</b>.</p>{desc}</div>")
    return subject, text, body
