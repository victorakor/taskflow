"""Profile pictures: uploaded photo, Google photo, or generated initials."""
import base64
import html
import io

from PIL import Image, ImageOps


def process_upload(data: bytes, size: int = 256) -> bytes:
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    img = ImageOps.fit(img, (size, size), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, "PNG", optimize=True)
    return out.getvalue()


def initials(name: str) -> str:
    parts = [p for p in name.split() if p]
    return ("".join(p[0] for p in parts[:2]) or "?").upper()


def avatar_html(user: dict, size: int = 44) -> str:
    """Return an <img>/<div> snippet (safe to embed with unsafe_allow_html)."""
    pref = user.get("avatar_pref", "auto")
    box = f"width:{size}px;height:{size}px;border-radius:50%;flex:none;"
    if user.get("avatar") and pref in ("auto", "upload"):
        src = "data:image/png;base64," + base64.b64encode(user["avatar"]).decode()
        return f'<img class="tf-avatar" src="{src}" style="{box}object-fit:cover">'
    url = user.get("avatar_url")
    if url and pref in ("auto", "google") and url.startswith("https://"):
        return (f'<img class="tf-avatar" src="{html.escape(url)}" referrerpolicy="no-referrer" '
                f'style="{box}object-fit:cover">')
    return (f'<div class="tf-avatar" style="{box}display:flex;align-items:center;justify-content:center;'
            f'background:linear-gradient(135deg,#6366f1,#a855f7);color:#fff;font-weight:700;'
            f'font-size:{size // 2.6:.0f}px">{html.escape(initials(user["name"]))}</div>')
