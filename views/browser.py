"""Small JavaScript bridges: PWA install tags, cookies, speech, system notifications."""
import json

import streamlit as st

from core.config import COOKIE


def _embed(html: str, height: int):
    """st.iframe on current Streamlit; components.html on older releases."""
    if hasattr(st, "iframe"):
        st.iframe(html, height=max(height, 1))
    else:  # pragma: no cover
        import streamlit.components.v1 as components
        components.html(html, height=height)


def _js(code: str):
    _embed(f"<script>(function(){{try{{{code}}}catch(e){{}}}})();</script>", 0)


def pwa():
    _js("""const d=window.parent.document;if(d.querySelector('link[rel=manifest]'))return;
    const add=(t,a)=>{const e=d.createElement(t);for(const k in a)e.setAttribute(k,a[k]);d.head.appendChild(e)};
    add('link',{rel:'manifest',href:'/app/static/manifest.json'});
    add('meta',{name:'theme-color',content:'#6366f1'});
    add('meta',{name:'mobile-web-app-capable',content:'yes'});
    add('meta',{name:'apple-mobile-web-app-capable',content:'yes'});
    add('meta',{name:'apple-mobile-web-app-title',content:'TaskFlow'});
    add('link',{rel:'apple-touch-icon',href:'/app/static/icon-192.png'});""")


def set_cookie(token: str, days: int):
    _js(f"const p=window.parent;p.document.cookie={json.dumps(COOKIE)}+'='+{json.dumps(token)}"
        f"+';max-age={days * 86400};path=/;SameSite=Lax'+(p.location.protocol=='https:'?';Secure':'');")


def clear_cookie():
    _js(f"window.parent.document.cookie={json.dumps(COOKIE)}+'=;max-age=0;path=/';")


def speak(text: str):
    t = json.dumps(text).replace("</", "<\\/")
    _js(f"const s=window.parent.speechSynthesis;s.cancel();const u=new SpeechSynthesisUtterance({t});"
        "u.rate=1;u.pitch=1;s.speak(u);")


def stop_speaking():
    _js("window.parent.speechSynthesis.cancel();")


def notify(title: str, body: str):
    _js(f"const P=window.parent;if(P.Notification&&P.Notification.permission==='granted'){{"
        f"new P.Notification({json.dumps(title)},{{body:{json.dumps(body)},icon:'/app/static/icon-192.png'}});}}"
        "if(P.navigator.vibrate)P.navigator.vibrate([300,150,300]);")


def permission_button():
    _embed("""<button onclick="Notification.requestPermission().then(p=>{this.textContent=
    p==='granted'?'✅ Notifications enabled':'Blocked — allow them in browser settings'})"
    style="font:600 14px system-ui;padding:8px 14px;border-radius:10px;border:1px solid #888;
    background:transparent;color:inherit;cursor:pointer">🔔 Enable system notifications</button>""", 44)
