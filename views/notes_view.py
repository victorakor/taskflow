import streamlit as st

from core import categories, notes
from core.timeutil import human, parse
from views.common import category_options, chip, esc


@st.dialog("Note")
def note_dialog(uid, cats, n=None):
    ids, fmt = category_options(cats)
    with st.form("note_form", border=False):
        title = st.text_input("Title", value=n["title"] if n else "", max_chars=120)
        c1, c2 = st.columns(2)
        cat = c1.selectbox("Category", ids, format_func=fmt, index=ids.index(n["category_id"]) if n else 0)
        new_cat = c2.text_input("…or new category", placeholder="e.g. Wedding")
        body = st.text_area("Write your note (Markdown supported)", value=n["body"] if n else "", height=220)
        pinned = st.checkbox("📌 Pin to top", value=bool(n and n["pinned"]))
        if st.form_submit_button("Save note", type="primary", width="stretch"):
            if not title.strip():
                return st.error("Give the note a title.")
            if new_cat.strip():
                cat = categories.get_or_create(uid, new_cat)
            if n:
                notes.update(uid, n["id"], title=title.strip(), body=body, category_id=cat, pinned=int(pinned))
            else:
                notes.add(uid, title, body, cat, pinned)
            st.rerun()


def render(user, tz):
    uid = user["id"]
    cats = categories.list_(uid)
    by_id = {c["id"]: c for c in cats}
    ids, fmt = category_options(cats)
    with st.container(key="row_filters"):
        a, b = st.columns(2)
        cat = a.selectbox("Category", ids, format_func=lambda i: "All categories" if i is None else fmt(i),
                          key="n_cat", label_visibility="collapsed")
        q = b.text_input("Search notes", placeholder="🔍 Search notes", key="n_q", label_visibility="collapsed")
    if st.button("＋", key="fab", type="primary", help="New note"):
        note_dialog(uid, cats)
    rows = notes.list_(uid, cat, q or None)
    if not rows:
        return st.info("No notes yet — tap ＋ to capture ideas, links and meeting notes.")
    cols = st.columns(2)
    for i, n in enumerate(rows):
        c = by_id.get(n["category_id"])
        chips = (chip(f'{c["icon"]} {c["name"]}', c["color"]) if c else "") + chip(human(parse(n["updated_at"]), tz), plain=True)
        with cols[i % 2], st.container(key=f"note_{n['id']}"):
            st.markdown(f'<div class="ncard"><div class="tt">{"📌 " if n["pinned"] else ""}{esc(n["title"])}</div>'
                        f'<div class="meta">{chips}</div></div>', unsafe_allow_html=True)
            body = n["body"]
            st.markdown(body[:360] + ("…" if len(body) > 360 else ""))
            with st.popover("⋯"):
                if st.button("Edit", key=f"ne_{n['id']}", icon=":material/edit:", width="stretch"):
                    note_dialog(uid, cats, n)
                if st.button("Unpin" if n["pinned"] else "Pin", key=f"np_{n['id']}", icon=":material/push_pin:", width="stretch"):
                    notes.update(uid, n["id"], pinned=int(not n["pinned"]))
                    st.rerun()
                if st.button("Delete", key=f"nd_{n['id']}", icon=":material/delete:", width="stretch"):
                    notes.delete(uid, n["id"])
                    st.rerun()
