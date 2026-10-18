"""Futuristic dark-glass theme. Layout uses our own HTML/CSS so it never overlaps on phones."""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--bg:#070b16;--glass:rgba(255,255,255,.05);--line:rgba(255,255,255,.10);--muted:#8b97bd;
 --violet:#8b5cf6;--cyan:#22d3ee;--pink:#ec4899;--text:#e8edff}
.stApp{font-family:Inter,system-ui,sans-serif;color:var(--text);
 background:radial-gradient(900px 520px at 8% -8%,rgba(139,92,246,.38),transparent 60%),
 radial-gradient(760px 460px at 100% 2%,rgba(34,211,238,.22),transparent 58%),
 radial-gradient(700px 500px at 50% 110%,rgba(236,72,153,.14),transparent 60%),var(--bg)}
.stApp::before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.5;
 background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);
 background-size:38px 38px;-webkit-mask-image:radial-gradient(ellipse at 50% 0,#000 20%,transparent 75%);mask-image:radial-gradient(ellipse at 50% 0,#000 20%,transparent 75%)}
header[data-testid="stHeader"]{background:transparent}
footer,#MainMenu{visibility:hidden}
.block-container{max-width:760px;padding:1rem 1rem 8rem!important}
div[data-testid="stVerticalBlock"]{gap:.7rem}
.disp,h1,h2,h3{font-family:'Space Grotesk',Inter,sans-serif;letter-spacing:-.02em}
h3{font-size:1.05rem!important;margin:.3rem 0 0!important}
.grad{background:linear-gradient(90deg,#a78bfa,#22d3ee);-webkit-background-clip:text;background-clip:text;color:transparent}
.muted,.sub{color:var(--muted);font-size:.78rem}

/* ---------- header ---------- */
.hdr{padding-bottom:.9rem;display:flex;align-items:center;gap:.8rem;padding:.2rem 0}
.hdr .av{flex:none;padding:2px;border-radius:50%;background:linear-gradient(135deg,#8b5cf6,#22d3ee);box-shadow:0 0 22px rgba(139,92,246,.55)}
.hdr .av .tf-avatar{border:2px solid var(--bg)}
.hdr .who{flex:1;min-width:0}.eyebrow{font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.hello{font:700 1.3rem/1.15 'Space Grotesk',Inter,sans-serif;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ring{--p:0;--a:#22d3ee;flex:none;width:54px;height:54px;border-radius:50%;display:grid;place-items:center;
 background:conic-gradient(var(--a) calc(var(--p)*1%),rgba(255,255,255,.09) 0);position:relative;box-shadow:0 0 18px color-mix(in srgb,var(--a) 35%,transparent)}
.ring::before{content:"";position:absolute;inset:6px;border-radius:50%;background:#0b1020}
.ring span{position:relative;font:700 .8rem 'Space Grotesk',sans-serif}
.ring.big{width:210px;height:210px}.ring.big::before{inset:12px}.ring.big span{font-size:2.7rem}
.ring.mid{width:96px;height:96px}.ring.mid::before{inset:9px}.ring.mid span{font-size:1.25rem}

/* ---------- glass cards ---------- */
[class*="st-key-task_"],[class*="st-key-note_"],.st-key-voice,.st-key-authbox,.glass{
 position:relative;background:var(--glass);border:1px solid var(--line);border-radius:18px;
 -webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);box-shadow:0 8px 30px rgba(0,0,0,.28)}
[class*="st-key-task_"],[class*="st-key-note_"]{gap:0!important;padding:0;transition:transform .15s,border-color .15s}
[class*="st-key-task_"]:hover,[class*="st-key-note_"]:hover{border-color:rgba(139,92,246,.55);transform:translateY(-1px)}
.tcard{padding:.85rem 3rem 1.75rem 3.1rem}.ncard{padding:.85rem 3rem .4rem .95rem}
.tcard::before{content:"";position:absolute;left:0;top:14px;bottom:14px;width:3px;border-radius:0 3px 3px 0;
 background:var(--c);box-shadow:0 0 12px var(--c)}
.tt{font-weight:600;line-height:1.3;word-break:break-word}.tt.done{text-decoration:line-through;opacity:.5}
.desc{color:var(--muted);font-size:.8rem;margin-top:.2rem}
.meta{display:flex;flex-wrap:wrap;gap:.3rem;margin-top:.4rem}
.chip{display:inline-flex;align-items:center;gap:.25rem;padding:.1rem .55rem;border-radius:999px;font-size:.7rem;font-weight:600;
 white-space:nowrap;color:var(--c,var(--text));background:color-mix(in srgb,var(--c,#888) 14%,transparent);
 border:1px solid color-mix(in srgb,var(--c,#888) 38%,transparent)}
.chip.plain{--c:#9fb0d9;font-weight:500}
/* round check + menu button pinned inside each card */
[class*="st-key-task_"] [data-testid="stCheckbox"]{position:absolute;left:.95rem;top:.9rem;width:auto}
[class*="st-key-task_"] [data-testid="stCheckbox"] label{min-height:0;padding:0}
[class*="st-key-task_"] [data-testid="stCheckbox"] label>div:first-of-type{width:1.4rem;height:1.4rem;border-radius:50%;margin:0;border:2px solid rgba(139,92,246,.75)!important;box-shadow:0 0 10px rgba(139,92,246,.35)}
[data-testid="stPopover"]{position:absolute;right:.5rem;top:.5rem;width:auto}
[data-testid="stPopoverButton"]{width:2.2rem;height:2.2rem;min-height:0;padding:0;border-radius:12px;background:transparent;border:0;color:var(--muted)}
[data-testid="stPopoverButton"] [aria-hidden="true"]{display:none}
[data-testid="stPopoverButton"]:hover{background:var(--glass);color:#fff}

/* ---------- tiles ---------- */
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:.6rem;padding-bottom:1.1rem}
.tiles.three{grid-template-columns:repeat(3,1fr)}
@media(max-width:560px){.tiles{grid-template-columns:repeat(2,1fr)}.tiles.three{grid-template-columns:repeat(3,1fr)}}
.tile{position:relative;overflow:hidden;padding:.75rem .85rem;border-radius:16px;
 background:linear-gradient(160deg,color-mix(in srgb,var(--c) 20%,transparent),rgba(255,255,255,.03) 70%);
 border:1px solid color-mix(in srgb,var(--c) 38%,transparent)}
.tile::after{content:"";position:absolute;right:-18px;top:-18px;width:64px;height:64px;border-radius:50%;
 background:var(--c);filter:blur(28px);opacity:.45}
.tile b{display:block;font:700 1.9rem/1 'Space Grotesk',sans-serif;color:#fff}
.tile span{display:block;margin-top:.35rem;font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;color:color-mix(in srgb,var(--c) 70%,#fff)}
.bar{height:7px;border-radius:99px;background:rgba(255,255,255,.08);overflow:hidden}
.bar i{display:block;height:100%;background:linear-gradient(90deg,#8b5cf6,#22d3ee);border-radius:99px;box-shadow:0 0 12px #22d3ee}
.hero{margin-bottom:.6rem;display:flex;align-items:center;gap:1rem;padding:1rem;border-radius:18px;background:var(--glass);border:1px solid var(--line)}
.hero .big{font:700 1.5rem 'Space Grotesk',sans-serif}

/* ---------- controls ---------- */
.stButton>button,.stDownloadButton>button,[data-testid="stFormSubmitButton"]>button{border-radius:14px;font-weight:600;
 border:1px solid var(--line);background:var(--glass);transition:all .15s}
.stButton>button:hover,[data-testid="stFormSubmitButton"]>button:hover{border-color:var(--violet);box-shadow:0 0 18px rgba(139,92,246,.4)}
button[kind="primary"],button[kind="primaryFormSubmit"]{background:linear-gradient(135deg,#8b5cf6,#6366f1 55%,#22d3ee)!important;border:0!important;color:#fff!important;
 box-shadow:0 6px 22px rgba(99,102,241,.45)}
[data-testid="stTextInput"] [role="group"],[data-testid="stTextArea"] [role="group"],[data-testid="stSelectbox"] [role="group"],[data-testid="stDateInput"] [role="group"],[data-testid="stTimeInput"] [role="group"]{border:1px solid rgba(255,255,255,.13)!important;border-radius:12px}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-testid="stSelectbox"] input{border-radius:12px}
[data-testid="stExpander"]{border:1px solid var(--line)!important;border-radius:16px!important;background:var(--glass)}
div[role="dialog"]{background:#0d1324!important;border:1px solid var(--line);border-radius:22px!important;box-shadow:0 30px 90px rgba(0,0,0,.6)}
[data-testid="stButtonGroup"] button{border-radius:12px}
[data-testid="stButtonGroup"] button[aria-checked="true"],[data-testid="stButtonGroup"] button[data-selected="true"]{
 background:linear-gradient(135deg,rgba(139,92,246,.9),rgba(34,211,238,.75))!important;color:#fff!important;border-color:transparent!important;box-shadow:0 0 18px rgba(139,92,246,.5)}
.st-key-voice{padding:.55rem .9rem}

/* one-line rows (filters, quick add, popup buttons) */
[class*="st-key-row_"] [data-testid="stHorizontalBlock"],.st-key-alarm_popup [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:.5rem!important}
[class*="st-key-row_"] [data-testid="stColumn"],.st-key-alarm_popup [data-testid="stColumn"]{min-width:0!important;flex:1 1 0!important}
.st-key-row_quick [data-testid="stColumn"]:last-child{flex:0 0 3.2rem!important;width:3.2rem!important}
.st-key-row_quick [data-testid="stForm"]{border:0;padding:0}

/* bottom navigation */
.st-key-navbar{position:fixed;left:50%;transform:translateX(-50%);bottom:.7rem;z-index:1000;width:calc(100% - 1.2rem);max-width:560px;
 padding:.35rem;border-radius:22px;background:rgba(10,15,30,.78);border:1px solid var(--line);
 -webkit-backdrop-filter:blur(18px);backdrop-filter:blur(18px);box-shadow:0 12px 40px rgba(0,0,0,.55)}
.st-key-navbar [data-testid="stButtonGroup"]>div:last-child,.st-key-navbar [role="radiogroup"]{width:100%;display:flex;gap:.2rem;border:0;background:transparent}
.st-key-navbar button{flex:1 1 0;min-width:0;padding:.45rem .1rem;font-size:.68rem;border:0!important;background:transparent;white-space:nowrap}
.st-key-navbar button p{font-size:.68rem}
/* floating action button */
.st-key-fab{position:fixed;right:max(1rem,calc(50% - 370px));bottom:5.3rem;z-index:999;width:auto}
.st-key-fab button p{font-size:2rem;line-height:1;margin:0}
.st-key-fab button{width:3.5rem;height:3.5rem;border-radius:50%;padding:0;font-size:1.7rem;line-height:1;
 box-shadow:0 10px 34px rgba(139,92,246,.7)!important}
/* alarm popup */
.st-key-alarm_popup{position:fixed;top:.8rem;left:50%;transform:translateX(-50%);z-index:99999;width:calc(100% - 1.2rem);max-width:430px;
 background:rgba(13,19,36,.94);border:1px solid var(--cyan);border-radius:22px;padding:1rem;
 -webkit-backdrop-filter:blur(20px);backdrop-filter:blur(20px);box-shadow:0 0 0 1px rgba(34,211,238,.3),0 0 50px rgba(34,211,238,.35),0 24px 70px rgba(0,0,0,.6);
 animation:drop .3s ease-out}
.st-key-alarm_popup audio,.st-key-alarm_popup [data-testid="stAudio"]{display:none}
@keyframes drop{from{transform:translate(-50%,-30px);opacity:0}to{transform:translate(-50%,0);opacity:1}}
.bell{font-size:2.1rem;display:inline-block;animation:shake .7s infinite;filter:drop-shadow(0 0 12px #22d3ee)}
@keyframes shake{0%,100%{transform:rotate(-14deg)}50%{transform:rotate(14deg)}}
.timer-wrap{display:grid;place-items:center;padding:.6rem 0}
[class*="st-key-note_"] [data-testid="stElementContainer"]:nth-child(2){padding:.55rem 1rem .9rem;font-size:.86rem;color:#c3cdee}
@media(max-width:560px){.ring.big{width:180px;height:180px}.ring.big span{font-size:2.3rem}}
</style>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)
