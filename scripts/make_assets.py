"""Regenerate the ringtone and app icons:  python scripts/make_assets.py"""
import math
import struct
import wave
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent


def ringtone(path, rate=22050):
    """Two-pulse phone-style ring (~3 s) designed to loop."""
    frames = bytearray()
    def tone(freqs, dur, vol=0.35):
        for i in range(int(rate * dur)):
            env = min(1, i / 400, (rate * dur - i) / 800)
            v = sum(math.sin(2 * math.pi * f * i / rate) for f in freqs) / len(freqs)
            frames.extend(struct.pack("<h", int(32767 * vol * env * v)))
    def silence(dur):
        frames.extend(b"\x00\x00" * int(rate * dur))
    for _ in range(2):
        for _ in range(4):
            tone([880, 1320], 0.09); silence(0.05)
        silence(0.45)
    silence(0.9)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(bytes(frames))


def icon(path, size, maskable=False):
    s = size * 4
    img = Image.new("RGB", (s, s))
    px = ImageDraw.Draw(img)
    for y in range(s):  # indigo -> violet gradient
        t = y / s
        px.line([(0, y), (s, y)], fill=(int(99 + 70 * t), int(102 - 20 * t), int(241 + 6 * t)))
    mask = Image.new("L", (s, s), 0)
    r = 0 if maskable else int(s * 0.22)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s, s], r, fill=255)
    k = 0.6 if maskable else 1.0  # keep the glyph inside the maskable safe zone
    c, u = s / 2, s * 0.22 * k
    ImageDraw.Draw(img).line([(c - 1.4 * u, c), (c - 0.35 * u, c + 1.0 * u), (c + 1.5 * u, c - 1.1 * u)],
                             fill="white", width=int(s * 0.085 * k), joint="curve")
    out = Image.new("RGBA", (s, s)); out.paste(img, mask=mask)
    out.resize((size, size), Image.LANCZOS).save(path)


if __name__ == "__main__":
    (ROOT / "assets").mkdir(exist_ok=True); (ROOT / "static").mkdir(exist_ok=True)
    ringtone(ROOT / "assets" / "ring.wav")
    icon(ROOT / "static" / "icon-192.png", 192)
    icon(ROOT / "static" / "icon-512.png", 512)
    icon(ROOT / "static" / "icon-maskable-512.png", 512, maskable=True)
    icon(ROOT / "assets" / "favicon.png", 64)
    print("assets written")
