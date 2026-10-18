import zoneinfo

import streamlit as st

from core import auth, avatar, backup, categories, config, notifier
from core.timeutil import utcnow
from views import auth_view, browser, speech
from views.common import MODES


def _profile(user):
    st.subheader("Profile")
    st.markdown(f'<div style="display:flex;justify-content:center"><div class="av" style="padding:3px;border-radius:50%;'
                f'background:linear-gradient(135deg,#8b5cf6,#22d3ee);box-shadow:0 0 28px rgba(139,92,246,.6)">'
                f'{avatar.avatar_html(user, 84)}</div></div>', unsafe_allow_html=True)
    name = st.text_input("Name", user["name"])
    options = {"auto": "Automatic", "upload": "Uploaded photo", "google": "Google photo", "none": "Initials"}
    avail = [k for k in options if k in ("auto", "none") or (k == "upload" and user["avatar"])
             or (k == "google" and user["avatar_url"])]
    pref = st.radio("Picture", avail, format_func=options.get, horizontal=True,
                    index=avail.index(user["avatar_pref"]) if user["avatar_pref"] in avail else 0)
    up = st.file_uploader("Upload a profile photo", type=["png", "jpg", "jpeg", "webp"])
    if st.button("Save profile", type="primary"):
        fields = {"name": name.strip() or user["name"], "avatar_pref": pref}
        if up:
            fields.update(avatar=avatar.process_upload(up.getvalue()), avatar_pref="upload")
        auth.update_user(user["id"], **fields)
        st.rerun()
    if not user["avatar_url"] and auth_view.google_enabled():
        st.caption("Tip: sign out and use “Continue with Google” with this same email to link your Google photo.")


def _prefs(user):
    st.subheader("Preferences")
    zones = ["auto"] + sorted(zoneinfo.available_timezones())
    cur = user["settings"]["tz"]
    tz = st.selectbox("Timezone", zones, index=zones.index(cur) if cur in zones else 0,
                      format_func=lambda z: "Automatic (from your device)" if z == "auto" else z)
    digest = st.select_slider("Spoken digest while voice aid is on", [0, 15, 30, 60, 120],
                              value=user["settings"]["digest_min"],
                              format_func=lambda m: "Off" if m == 0 else f"every {m} min")
    if st.button("Save preferences"):
        st.session_state.settings = auth.save_settings(user["id"], tz=tz, digest_min=digest)
        st.rerun()


def _notifications(user):
    st.subheader("Notifications")
    if notifier.configured():
        st.success(f"Email reminders are on and will be sent to **{user['email']}**.")
        if st.button("Send me a test email"):
            try:
                notifier.send(user["email"], "TaskFlow test ✅", "Email reminders are working.")
                st.toast("Test email sent", icon="📧")
            except Exception as e:
                st.error(f"Could not send: {e}")
    else:
        st.warning("Email reminders need SMTP settings on the server (see README → Email setup).")
    st.caption("Ring + popup reminders play in this app while it's open. System notifications are optional:")
    browser.permission_button()
    if st.button("Test ring & voice", icon=":material/volume_up:"):
        speech.say("This is your TaskFlow voice aid.")
        st.session_state.test_ring = True
    if st.session_state.pop("test_ring", False):
        from views.alarm import _ring
        st.audio(_ring(), format="audio/wav", autoplay=True)


def _categories(user):
    uid = user["id"]
    with st.expander("Categories"):
        for c in categories.list_(uid):
            a, b, d = st.columns([1, 4, 2], vertical_alignment="bottom")
            icon = a.text_input("Icon", c["icon"], key=f"ci{c['id']}", max_chars=2)
            name = b.text_input(f"{c['n_tasks']} tasks · {c['n_notes']} notes", c["name"], key=f"cn{c['id']}")
            color = d.color_picker("Colour", c["color"], key=f"cc{c['id']}")
            s, x = st.columns(2)
            if s.button("Save", key=f"cs{c['id']}", width="stretch"):
                try:
                    categories.update(uid, c["id"], name, color, icon)
                    st.rerun()
                except Exception:
                    st.error("A category with that name already exists.")
            if x.button("Delete", key=f"cx{c['id']}", width="stretch"):
                categories.delete(uid, c["id"])
                st.rerun()
            st.divider()
        with st.form("new_cat", clear_on_submit=True, border=False):
            n1, n2 = st.columns([3, 1], vertical_alignment="bottom")
            new = n1.text_input("New category")
            if n2.form_submit_button("Add", width="stretch") and new.strip():
                categories.get_or_create(uid, new)
                st.rerun()


def _data(user, tz):
    uid = user["id"]
    st.subheader("Your data")
    a, b = st.columns(2)
    a.download_button("Backup (JSON)", backup.export_json(uid), "taskflow-backup.json", "application/json",
                      width="stretch", icon=":material/download:")
    b.download_button("Tasks (CSV)", backup.export_csv(uid, tz), "taskflow-tasks.csv", "text/csv",
                      width="stretch", icon=":material/table:")
    up = st.file_uploader("Restore a backup, or import your old task.json", type=["json"], key="imp")
    if up and st.button("Import file"):
        try:
            t, n = backup.import_json(uid, up.getvalue())
            st.success(f"Imported {t} tasks and {n} notes.")
        except Exception as e:
            st.error(f"Import failed: {e}")


def render(user, tz):
    _profile(user)
    _prefs(user)
    _notifications(user)
    _categories(user)
    _data(user, tz)
    if user["pw_hash"]:
        with st.expander("Change password"), st.form("pw", border=False):
            old, new = st.text_input("Current password", type="password"), st.text_input("New password", type="password")
            if st.form_submit_button("Update password"):
                try:
                    auth.change_password(user["id"], old, new)
                    st.success("Password updated.")
                except ValueError as e:
                    st.error(str(e))
    with st.expander("Install as a phone app"):
        st.markdown("**Android (Chrome):** menu ⋮ → *Install app*.  \n**iPhone (Safari):** Share → *Add to Home Screen*.  \n"
                    "A native Android/iOS build is described in the README (`mobile/`).")
    if st.button("Sign out", icon=":material/logout:", width="stretch"):
        auth.end_session(st.context.cookies.get(config.COOKIE))
        for k in list(st.session_state):
            del st.session_state[k]
        st.session_state.clear_cookie = True
        if getattr(st.user, "is_logged_in", False):
            st.logout()
        st.rerun()
