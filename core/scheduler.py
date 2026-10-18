"""Background worker that emails reminders at task start/end time.

It runs as a daemon thread inside the Streamlit server (started once per process),
or stand-alone:  python -m core.scheduler
"""
import json
import logging
import threading
import time

from core import config, db, notifier, reminders

log = logging.getLogger("taskflow.scheduler")
_started = threading.Event()
INTERVAL = 30


def run_once() -> int:
    if not notifier.configured():
        return 0
    sent = 0
    for t, kind in reminders.due_emails():
        try:
            tz = json.loads(t["user_settings"] or "{}").get("tz_seen") or "UTC"
            notifier.send(t["user_email"], *notifier.task_email(t, kind, tz))
            reminders.mark_email_sent(t["id"], kind)
            sent += 1
        except Exception as exc:  # retry on the next tick
            log.warning("email failed for task %s: %s", t["id"], exc)
    return sent


def _loop():
    while True:
        try:
            run_once()
        except Exception as exc:
            log.warning("scheduler tick failed: %s", exc)
        time.sleep(INTERVAL)


def start():
    if config.flag("TASKFLOW_DISABLE_SCHEDULER") or _started.is_set():
        return
    _started.set()
    threading.Thread(target=_loop, name="taskflow-scheduler", daemon=True).start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db.init()
    _loop()
