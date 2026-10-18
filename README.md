# ✅ TaskFlow

A compact, futuristic **Streamlit** app for tasks, notes, reminders and progress tracking — dark glass design with neon accents, bottom navigation and a floating “＋” button, built mobile-first and installable on your phone.

## Features

| | |
|---|---|
| **Tasks** | Title, details, priority, category, start & end time, repeat (daily/weekly/monthly), search and filters |
| **Quick add** | Type `Call mom tomorrow 5pm for 30m #family !high` and it fills everything in |
| **Notes** | Markdown notes with pinning, search and categories |
| **Categories** | One set of named groups shared by tasks *and* notes — create them anywhere (“Wedding”, “Exam prep”) |
| **Reminders** | Per task: 📧 **email** at start/end time, 🔔 **ring + popup** at start/end time, or both. Optional “minutes before”, snooze, done |
| **Voice aid** | Toggle on to hear all your tasks read out, spoken reminders, and an optional periodic digest |
| **Progress tracker** | Completed · In progress · Pending · Incomplete, on-time rate, streak, 14-day chart, per-category breakdown |
| **Focus timer** | Pomodoro sessions linked to a task, logged to your progress |
| **Profile** | Upload a photo or use your Google photo (Sign in with Google); initials otherwise |
| **Data** | Accounts with hashed passwords, remember-me sessions, JSON backup / CSV export / import |
| **Mobile** | Installable PWA + Capacitor wrapper for a real Android/iOS app |

### How the tracker classifies tasks

- **Completed** – finished *within* its start–end window.
- **Pending** – the start time hasn't arrived yet.
- **Incomplete** – the end time passed without finishing, *or* it was finished after the end time (shown as “Done late”).
- **In progress** – inside its window now, or open with no schedule.

On-time rate = Completed ÷ (Completed + Incomplete), i.e. only windows that have closed.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Create an account on the first screen. Data lives in `./data/taskflow.db` (SQLite, git-ignored).

Your old `task.json`? Open **Settings → Your data → Import** and upload it.

## Email setup (for email reminders)

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in the SMTP block (or set the same names as environment variables — see `.env.example`). For Gmail use an [App Password](https://myaccount.google.com/apppasswords). Then **Settings → Send me a test email**.

A background thread checks every 30 s and emails the account’s address at each task’s start/end time. It only runs while the server process is running — see *Hosting* below.

## Sign in with Google (optional)

Gives one-click login and your Google profile picture. Create an OAuth client in Google Cloud Console, add redirect URI `https://YOUR-APP-URL/oauth2callback`, and fill the `[auth]` blocks in the secrets example. If a password account already uses that email, it is linked automatically.

## Hosting

TaskFlow needs an **always-on server with a persistent disk** (SQLite file + email scheduler).

| Option | Notes |
|---|---|
| **Render** | `render.yaml` included (Docker + 1 GB disk). Paid plan needed for the disk and no sleeping |
| **Railway / Fly.io / VPS** | Use the `Dockerfile`; mount a volume at `/data` |
| **Docker anywhere** | `cp .env.example .env && docker compose up -d` |
| Streamlit Community Cloud | Works for trying it out, but apps sleep and the disk is wiped on restart: **no emails while asleep, data not durable** |

Put it behind HTTPS (all of the above do). Set `ALLOW_SIGNUP=false` after creating your accounts if it’s private.

## Mobile app

1. **Quick (PWA):** open your hosted URL on the phone → Android Chrome *Install app* / iPhone Safari *Share → Add to Home Screen*.
2. **Native shell (Capacitor):** a thin Android/iOS wrapper around your hosted app.
   ```bash
   cd mobile
   # edit capacitor.config.json -> server.url = your hosted URL
   npm install
   npx cap add android      # (iOS: npx cap add ios — needs a Mac + Xcode)
   npx cap sync
   npx cap open android     # build the APK/AAB in Android Studio
   ```

Mobile notes:
- Email reminders work everywhere (they come from the server).
- Ring/popup and voice only run while the app is open on screen — a web-view app cannot wake itself in the background. Use email reminders for “app closed” alerts.
- Google blocks sign-in inside embedded web views, so in the native app use email + password (same account, same data).

## Project layout

```
app.py              entry point (header, navigation, wiring)
core/               logic, no UI: db, auth, tasks, reminders, stats, voice text, email, scheduler, backup
views/              Streamlit screens + small JS bridges (speech, cookies, notifications)
static/             PWA manifest + icons (served at /app/static)
assets/             ringtone + favicon        scripts/make_assets.py regenerates them
mobile/             Capacitor wrapper         tests/  pytest suite
```

Run tests: `pip install -r requirements-dev.txt && pytest`.
Standalone email worker (optional, instead of the built-in thread): `TASKFLOW_DISABLE_SCHEDULER=1 streamlit run app.py` plus `python -m core.scheduler`.

## Known limits

- Browsers may block auto-playing the ringtone until you’ve tapped/clicked the page once.
- Voice uses your device’s built-in speech engine; voices differ per device.
- The theme is dark by design (`.streamlit/config.toml` + `views/style.py`). Fonts load from Google Fonts and fall back to system fonts offline.
- Single SQLite file: great for personal/small-team use, not for thousands of concurrent users.

MIT licensed.
