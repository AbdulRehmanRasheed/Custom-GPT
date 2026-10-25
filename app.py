import uuid
from pathlib import Path

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# ----------------------------------------------------------------------------
# Page setup
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Custom GPT",
    page_icon=":material/forum:",
    layout="wide",
)

# Streamlit reads its theme file only at startup. The page below is styled with explicit colours,
# so it looks right either way, but we also make sure a matching light theme file exists
# (it takes effect the next time the app is restarted).
LIGHT_THEME = (
    '[theme]\nbase = "light"\nprimaryColor = "#FF6B57"\nbackgroundColor = "#FFF6E5"\n'
    'secondaryBackgroundColor = "#FFE9A8"\ntextColor = "#1A1625"\nfont = "sans serif"\n'
)
try:
    _cfg = Path(".streamlit/config.toml")
    if not _cfg.exists() or 'base = "dark"' in _cfg.read_text(encoding="utf-8"):
        _cfg.parent.mkdir(exist_ok=True)
        _cfg.write_text(LIGHT_THEME, encoding="utf-8")
except OSError:
    pass  # read-only hosting is fine, the CSS below does the work

# Google retires models fairly often. If one stops working, pick "Custom..." in the sidebar
# and type the new model name, or edit this list.
MODELS = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.7-flash"]

PERSONAS = {
    "Helpful assistant": "You are a helpful assistant. Be clear, accurate and friendly.",
    "Coding mentor": (
        "You are a patient senior developer. Explain ideas step by step, show short "
        "code examples, and point out common mistakes."
    ),
    "Writing coach": (
        "You are a writing coach. Improve clarity and tone, keep the author's voice, "
        "and briefly explain what you changed."
    ),
    "Explain like I'm five": (
        "Explain everything in very simple words, using everyday examples and short sentences."
    ),
    "Custom": "You are a helpful assistant.",
}

SUGGESTIONS = [
    ("💡  Explain something", "Explain how the internet works, in simple words."),
    ("✉️  Write an email", "Write a polite follow-up email after a job interview."),
    ("🧳  Plan a trip", "Plan a relaxed 3-day city break in Istanbul."),
    ("💻  Learn to code", "Give me a beginner-friendly Python practice project idea, with steps."),
]

# ----------------------------------------------------------------------------
# Styling: flat, bold and colourful. Thick ink outlines, hard shadows, bright palette.
# ----------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=DM+Sans:wght@400;500;600;700&display=swap');

:root {
    --ink: #1A1625;
    --paper: #FFF6E5;
    --yellow: #FFD23F;
    --coral: #FF6B57;
    --mint: #5EE0B0;
    --sky: #6CC6FF;
    --pink: #FF9ECD;
    --lilac: #C4B1FF;
    --muted: #5E5870;
}
:root, .stApp { color-scheme: light; }

html, body, [class*="css"], .stApp, button, input, textarea { font-family: 'DM Sans', sans-serif !important; }
h1, h2, h3, h4, .display { font-family: 'Bricolage Grotesque', sans-serif !important; }

.stApp {
    background-color: var(--paper);
    background-image: radial-gradient(rgba(26,22,37,.13) 1.2px, transparent 1.5px);
    background-size: 24px 24px;
}
/* One rule for text colour so nothing depends on the browser or Streamlit theme */
[data-testid="stAppViewContainer"] *, section[data-testid="stSidebar"] * { color: var(--ink); }
.stApp a { color: #C2255C !important; font-weight: 600; }

/* Flat colour stripe along the top edge */
body::before {
    content: ""; position: fixed; top: 0; left: 0; right: 0; height: 6px; z-index: 999999;
    background: linear-gradient(90deg, var(--yellow) 0 20%, var(--coral) 20% 40%, var(--mint) 40% 60%, var(--sky) 60% 80%, var(--pink) 80% 100%);
}

/* Clean the chrome but keep the header, because the "open sidebar" arrow lives in it */
#MainMenu, footer, [data-testid="stDecoration"] { visibility: hidden; }
[data-testid="stAppDeployButton"], .stAppDeployButton, .stDeployButton { display: none !important; }
header[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stExpandSidebarButton"] {
    background: var(--yellow) !important; border: 2px solid var(--ink) !important; border-radius: 10px !important;
    box-shadow: 2px 2px 0 var(--ink);
}

.block-container { position: relative; z-index: 1; max-width: 820px; padding-top: 2.5rem; padding-bottom: 7rem; }

/* ---------- Animations ---------- */
@keyframes pop     { from { opacity: 0; transform: scale(.94) translateY(10px); } to { opacity: 1; transform: none; } }
@keyframes slideIn { from { opacity: 0; transform: translateX(-12px); } to { opacity: 1; transform: none; } }
@keyframes float   { 0%,100% { transform: translateY(0) rotate(0deg); } 50% { transform: translateY(-24px) rotate(6deg); } }
@keyframes float2  { 0%,100% { transform: translateY(0) rotate(18deg); } 50% { transform: translateY(-20px) rotate(30deg); } }
@keyframes spin    { to { transform: rotate(360deg); } }
@keyframes wiggle  { 0%,100% { transform: rotate(-5deg); } 50% { transform: rotate(5deg); } }
@keyframes bob     { 0%,100% { transform: translateY(0) rotate(-4deg); } 50% { transform: translateY(-7px) rotate(4deg); } }
@keyframes pulse   { 0% { box-shadow: 0 0 0 0 rgba(94,224,176,.8); } 100% { box-shadow: 0 0 0 10px rgba(94,224,176,0); } }
@keyframes scroll  { to { transform: translateX(-50%); } }
@keyframes rot     { 0%,20% { transform: translateY(0); } 25%,45% { transform: translateY(-20%); }
                     50%,70% { transform: translateY(-40%); } 75%,95% { transform: translateY(-60%); } 100% { transform: translateY(-80%); } }
@keyframes dots    { 0%,80%,100% { transform: scale(.5); opacity: .4; } 40% { transform: scale(1); opacity: 1; } }
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }

/* ---------- Floating background shapes ---------- */
[data-testid="stElementContainer"]:has(.bg-shapes), [data-testid="stElementContainer"]:has(.marquee) { height: 0; margin: 0; }
.bg-shapes { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }
.shp { position: absolute; display: block; }
.shp.a { width: 220px; height: 220px; border-radius: 50%; background: var(--yellow); border: 3px solid var(--ink); left: -80px; top: 16%; animation: float 9s ease-in-out infinite; }
.shp.b { width: 150px; height: 150px; border-radius: 28px; background: var(--coral); border: 3px solid var(--ink); right: -50px; top: 24%; transform: rotate(18deg); animation: float2 11s ease-in-out infinite; }
.shp.c { width: 140px; height: 128px; background: var(--mint); clip-path: polygon(50% 0, 100% 100%, 0 100%); right: 5%; bottom: 16%; animation: float 10s ease-in-out infinite; }
.shp.d { width: 120px; height: 120px; border-radius: 50%; border: 20px solid var(--sky); left: 6%; bottom: 14%; animation: float2 12s ease-in-out infinite; }
.shp.e { width: 90px; height: 90px; background: var(--pink); right: 11%; top: 10%; animation: spin 16s linear infinite;
         clip-path: polygon(50% 0, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%); }
.shp.f { width: 110px; height: 110px; background: var(--lilac); border: 3px solid var(--ink); left: 13%; top: 8%;
         border-radius: 60% 40% 55% 45% / 50% 60% 40% 50%; animation: float 8s ease-in-out infinite; }
@media (max-width: 800px) { .bg-shapes { display: none; } }

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] { background: var(--yellow) !important; border-right: 3px solid var(--ink); z-index: 5; }
section[data-testid="stSidebar"] > div { background: transparent; }
section[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }
.brand { display: flex; align-items: center; gap: .7rem; margin-bottom: 1rem; }
.brand .mark {
    width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center; background: var(--coral);
    border: 2px solid var(--ink); box-shadow: 3px 3px 0 var(--ink); font-weight: 800; transform: rotate(-5deg);
}
.brand:hover .mark { animation: wiggle .5s ease-in-out infinite; }
.brand .name { font-family: 'Bricolage Grotesque', sans-serif; font-size: 1.35rem; font-weight: 800; letter-spacing: -.02em; }
.side-label { font-size: .72rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; margin: 1.3rem 0 .5rem 0; }

/* ---------- Buttons: flat colour, ink outline, hard shadow that "presses" ---------- */
.stButton button, [data-testid="stFormSubmitButton"] button {
    background: #fff !important; border: 2px solid var(--ink) !important; border-radius: 12px;
    box-shadow: 3px 3px 0 var(--ink); font-weight: 700;
    transition: transform .12s ease, box-shadow .12s ease, background .12s ease;
}
.stButton button p, .stButton button span, [data-testid="stFormSubmitButton"] button p { color: var(--ink) !important; }
.stButton button:hover, [data-testid="stFormSubmitButton"] button:hover {
    background: var(--yellow) !important; transform: translate(-2px, -2px); box-shadow: 5px 5px 0 var(--ink);
}
section[data-testid="stSidebar"] .stButton button:hover { background: var(--pink) !important; }
.stButton button:active, [data-testid="stFormSubmitButton"] button:active { transform: translate(3px, 3px); box-shadow: 0 0 0 var(--ink); }
.stButton button[kind="primary"], [data-testid="stBaseButton-primary"] { background: var(--coral) !important; }
.stButton button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover { background: #FF8573 !important; }
[data-testid="stFormSubmitButton"] button { width: 100%; background: var(--coral) !important; font-size: 1.05rem; padding: .55rem 1rem; }
[data-testid="stFormSubmitButton"] button:hover { background: #FF8573 !important; }

/* Chat history rows */
[class*="st-key-chat_"] button, .st-key-active_chat button {
    justify-content: flex-start !important; text-align: left; box-shadow: 2px 2px 0 var(--ink); animation: slideIn .3s ease both;
}
[class*="st-key-chat_"] button p, .st-key-active_chat button p {
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 150px;
}
.st-key-active_chat button { background: var(--mint) !important; }
[class*="st-key-del_"] button { background: transparent !important; border-color: transparent !important; box-shadow: none !important; }
[class*="st-key-del_"] button:hover { background: var(--coral) !important; border-color: var(--ink) !important; transform: none; box-shadow: 2px 2px 0 var(--ink) !important; }

/* ---------- Inputs / selects ---------- */
/* ---------- Inputs / selects ---------- */
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div {
    background-color: #fff !important; 
    border: 2px solid var(--ink) !important; 
    border-radius: 12px !important;
}
[data-baseweb="base-input"] { 
    background-color: #fff !important;
    border: none !important; 
}
[data-baseweb="input"] input, [data-baseweb="base-input"] input, [data-baseweb="textarea"] textarea {
    background-color: #fff !important; 
    color: var(--ink) !important; 
    -webkit-text-fill-color: var(--ink) !important;
}
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within, [data-baseweb="select"]:hover > div {
    border-color: var(--coral) !important; 
    box-shadow: 3px 3px 0 var(--ink);
}
input::placeholder, textarea::placeholder { 
    color: #8A8497 !important; 
    -webkit-text-fill-color: #8A8497 !important; 
}
[data-testid="InputInstructions"] { display: none !important; }
[data-baseweb="select"] svg, [data-baseweb="input"] svg { fill: var(--ink) !important; }
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within, [data-baseweb="select"]:hover > div {
    border-color: var(--coral) !important; box-shadow: 3px 3px 0 var(--ink);
}
input::placeholder, textarea::placeholder { color: #8A8497 !important; -webkit-text-fill-color: #8A8497 !important; }
[data-testid="InputInstructions"] { display: none !important; }   /* the "Press Enter to submit form" hint */
[data-baseweb="select"] svg, [data-baseweb="input"] svg { fill: var(--ink) !important; }

[data-baseweb="popover"], [data-baseweb="popover"] div, [data-baseweb="popover"] ul, [data-baseweb="popover"] li,
[data-baseweb="menu"], [data-baseweb="menu"] li {
    background-color: #fff !important; color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important;
}
[data-baseweb="popover"] li:hover, [data-baseweb="popover"] li[aria-selected="true"] { background-color: var(--yellow) !important; }
[data-baseweb="popover"] > div { border: 2px solid var(--ink); border-radius: 12px; box-shadow: 4px 4px 0 var(--ink); }

[data-testid="stSlider"] [role="slider"] { background-color: var(--coral) !important; border: 2px solid var(--ink) !important; box-shadow: none !important; }
[data-testid="stSliderThumbValue"], [data-testid="stTickBarMin"], [data-testid="stTickBarMax"] { color: var(--ink) !important; font-weight: 700; }

[data-testid="stExpander"] { border: none; background: transparent; }
[data-testid="stExpander"] details { background: #fff; border: 2px solid var(--ink); border-radius: 14px; box-shadow: 3px 3px 0 var(--ink); }
[data-testid="stExpander"] summary * { font-weight: 700; }

[data-testid="stAlert"] { background: #FFD9E3 !important; border: 2px solid var(--ink); border-radius: 14px; box-shadow: 3px 3px 0 var(--ink); animation: pop .3s ease both; }

/* ---------- Empty state ---------- */
.hero {
    max-width: 580px; margin: 8vh auto 1.6rem auto; padding: 2.4rem 2rem; text-align: center;
    background: #fff; border: 3px solid var(--ink); border-radius: 24px; box-shadow: 8px 8px 0 var(--ink);
    animation: pop .5s cubic-bezier(.2,1.2,.4,1) both;
}
.hero .mark {
    width: 58px; height: 58px; margin: 0 auto 1rem auto; border-radius: 18px; display: grid; place-items: center;
    background: var(--yellow); border: 2px solid var(--ink); box-shadow: 3px 3px 0 var(--ink); font-size: 1.5rem; font-weight: 800;
    animation: bob 4s ease-in-out infinite;
}
.hero h1 { font-size: 2.4rem; font-weight: 800; letter-spacing: -.03em; line-height: 1.1; margin: 0 0 .6rem 0; }
.hl { background: linear-gradient(transparent 58%, var(--yellow) 58%); padding: 0 .1em; }
.hl.pk { background: linear-gradient(transparent 58%, var(--pink) 58%); }
.hero p { color: var(--muted) !important; margin: 0; font-size: 1.05rem; }

[class*="st-key-sugg_"] button { min-height: 3.5rem; font-size: 1rem; animation: pop .5s cubic-bezier(.2,1.2,.4,1) both; }
.st-key-sugg_0 button { background: var(--coral) !important; animation-delay: .10s !important; }
.st-key-sugg_1 button { background: var(--mint) !important;  animation-delay: .18s !important; }
.st-key-sugg_2 button { background: var(--sky) !important;   animation-delay: .26s !important; }
.st-key-sugg_3 button { background: var(--pink) !important;  animation-delay: .34s !important; }
[class*="st-key-sugg_"] button:hover { filter: brightness(1.06); }

/* ---------- Messages ---------- */
[data-testid="stChatMessage"] {
    background: #fff; border: 2px solid var(--ink); border-radius: 18px; box-shadow: 4px 4px 0 var(--ink);
    padding: 1rem 1.2rem; margin-bottom: 1rem; animation: pop .35s cubic-bezier(.2,1.2,.4,1) both;
}
[data-testid="stChatMessage"]:has([data-testid*="AvatarUser"]) { background: #D9EEFF; }
[data-testid*="AvatarUser"] { background: var(--coral) !important; border: 2px solid var(--ink); }
[data-testid*="AvatarAssistant"] { background: var(--yellow) !important; border: 2px solid var(--ink); }
pre, [data-testid="stCode"] { background: var(--ink) !important; border: 2px solid var(--ink); border-radius: 12px; }
pre *, [data-testid="stCode"] * { color: #FFF6E5 !important; background: transparent !important; }
code { background: #FFE9A8; border-radius: 6px; padding: .1rem .35rem; }
pre code { background: transparent; padding: 0; }

.typing { display: inline-flex; gap: 7px; padding: .4rem 0; }
.typing span { width: 11px; height: 11px; border-radius: 50%; border: 2px solid var(--ink); background: var(--coral); animation: dots 1.2s infinite ease-in-out; }
.typing span:nth-child(2) { animation-delay: .15s; background: var(--yellow); }
.typing span:nth-child(3) { animation-delay: .3s; background: var(--sky); }

/* ---------- Prompt bar ---------- */
[data-testid="stBottom"], [data-testid="stBottom"] > div { background: transparent !important; }
[data-testid="stBottomBlockContainer"] {
    max-width: 820px; margin: 0 auto; padding-bottom: 1.5rem;
    background: linear-gradient(to bottom, rgba(255,246,229,0), var(--paper) 40%) !important;
}
[data-testid="stChatInput"] {
    background: #fff !important; border: 3px solid var(--ink); border-radius: 18px; box-shadow: 5px 5px 0 var(--ink);
    transition: box-shadow .15s ease, transform .15s ease;
}
[data-testid="stChatInput"]:focus-within { box-shadow: 7px 7px 0 var(--coral); transform: translate(-1px, -1px); }
[data-testid="stChatInput"] > div, [data-testid="stChatInput"] [data-baseweb] { background: transparent !important; border: none !important; }
[data-testid="stChatInput"] textarea { color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important; background: transparent !important; }
[data-testid="stChatInput"] button { background: var(--coral) !important; border: 2px solid var(--ink) !important; border-radius: 10px; }
[data-testid="stChatInput"] button svg { fill: var(--ink) !important; color: var(--ink) !important; }

/* ---------- API key page ---------- */
.chip {
    display: inline-flex; align-items: center; gap: .55rem; background: var(--lilac); border: 2px solid var(--ink);
    border-radius: 999px; padding: .35rem 1rem; font-weight: 700; font-size: .85rem; box-shadow: 3px 3px 0 var(--ink);
    animation: pop .5s cubic-bezier(.2,1.2,.4,1) both;
}
.chip .dot { width: 10px; height: 10px; border-radius: 50%; background: var(--mint); border: 2px solid var(--ink); animation: pulse 1.4s infinite; }
.gate-h1 {
    font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800; font-size: clamp(2.4rem, 6vw, 3.7rem);
    line-height: 1.2; letter-spacing: -.03em; margin: 1.1rem 0 .9rem 0; animation: pop .6s .08s cubic-bezier(.2,1.2,.4,1) both;
}
.rot { display: inline-block; height: 1.2em; overflow: hidden; vertical-align: top; }
.rot-in { display: flex; flex-direction: column; align-items: flex-start; animation: rot 10s cubic-bezier(.7,0,.2,1) infinite; }
.rot-in b { display: block; height: 1.2em; line-height: 1.2em; padding: 0 .22em; border-radius: .22em; border: 3px solid var(--ink); box-sizing: border-box; }
.rot-in b.w1 { background: var(--coral); } .rot-in b.w2 { background: var(--mint); }
.rot-in b.w3 { background: var(--sky); }   .rot-in b.w4 { background: var(--pink); }
.gate-sub { font-size: 1.1rem; color: var(--muted) !important; margin: 0 0 1.8rem 0; max-width: 520px; animation: pop .6s .16s cubic-bezier(.2,1.2,.4,1) both; }

[data-testid="stForm"] {
    position: relative; background: #fff; border: 3px solid var(--ink); border-radius: 22px; padding: 1.6rem 1.5rem 1.4rem 1.5rem;
    box-shadow: 8px 8px 0 var(--ink); animation: pop .6s .24s cubic-bezier(.2,1.2,.4,1) both;
}
[data-testid="stForm"]::after {
    content: "🔒 never saved to disk"; position: absolute; top: -17px; right: 20px; background: var(--mint);
    border: 2px solid var(--ink); border-radius: 999px; padding: .15rem .8rem; font-size: .78rem; font-weight: 700;
    transform: rotate(3deg); box-shadow: 2px 2px 0 var(--ink);
}
[data-testid="stForm"] label p { font-weight: 700; }

.steps { display: flex; gap: .9rem; margin-top: 1.7rem; flex-wrap: wrap; }
.step {
    flex: 1 1 150px; display: flex; align-items: center; gap: .7rem; padding: .8rem 1rem; border: 2px solid var(--ink);
    border-radius: 16px; box-shadow: 4px 4px 0 var(--ink); text-decoration: none !important; font-weight: 700;
    transition: transform .15s ease, box-shadow .15s ease; animation: pop .6s cubic-bezier(.2,1.2,.4,1) both;
}
.step:hover { transform: translate(-2px, -3px) rotate(-1.5deg); box-shadow: 7px 7px 0 var(--ink); }
.step b { width: 30px; height: 30px; flex: none; border-radius: 50%; background: #fff; border: 2px solid var(--ink); display: grid; place-items: center; }
.step.s1 { background: var(--yellow); animation-delay: .34s; } .step.s2 { background: var(--sky); animation-delay: .42s; }
.step.s3 { background: var(--pink); animation-delay: .5s; }
.step, .step * { color: var(--ink) !important; }

.marquee {
    position: fixed; left: 0; right: 0; bottom: 0; z-index: 50; background: var(--yellow);
    border-top: 3px solid var(--ink); overflow: hidden; padding: .6rem 0;
}
.marquee .track { display: inline-flex; white-space: nowrap; animation: scroll 30s linear infinite; }
.marquee .track span { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800; letter-spacing: .08em; font-size: 1rem; padding-right: 1.5rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

SHAPES_HTML = (
    '<div class="bg-shapes"><span class="shp a"></span><span class="shp b"></span><span class="shp c"></span>'
    '<span class="shp d"></span><span class="shp e"></span><span class="shp f"></span></div>'
)
_marquee_text = "ASK ANYTHING ✦ WRITE ✦ LEARN ✦ PLAN ✦ CODE ✦ CREATE ✦ " * 4
MARQUEE_HTML = f'<div class="marquee"><div class="track"><span>{_marquee_text}</span><span>{_marquee_text}</span></div></div>'
TYPING_HTML = '<div class="typing"><span></span><span></span><span></span></div>'

st.markdown(SHAPES_HTML, unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def new_chat() -> str:
    chat_id = uuid.uuid4().hex[:8]
    st.session_state.chats[chat_id] = {"title": "New chat", "messages": []}
    st.session_state.current = chat_id
    return chat_id


def chunk_text(content) -> str:
    """Newer Gemini models can return a list of content blocks instead of a plain string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
    return str(content)


def friendly_error(exc: Exception) -> str:
    msg = str(exc)
    low = msg.lower()
    if "api key" in low or "api_key_invalid" in low or "unauthenticated" in low:
        return "Gemini rejected your API key. Use **Change API key** in the sidebar and paste a fresh one."
    if "not_found" in low or "404" in low:
        return "That model isn't available any more. Pick another one under **Model and behavior**, or choose **Custom...** and type a current model name."
    if "429" in low or "quota" in low or "resource_exhausted" in low:
        return "You've hit Gemini's rate or quota limit. Wait a minute and try again, or switch to a lighter model."
    return f"The request failed: {msg}"


# ----------------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------------
st.session_state.setdefault("api_key", "")
st.session_state.setdefault("chats", {})
st.session_state.setdefault("pending_prompt", None)
if "current" not in st.session_state:
    new_chat()

# ----------------------------------------------------------------------------
# Step 1: ask for the Gemini API key
# ----------------------------------------------------------------------------
if not st.session_state.api_key:
    st.markdown(
        "<style>section[data-testid='stSidebar'], [data-testid='stExpandSidebarButton'],"
        "[data-testid='stSidebarCollapsedControl']{display:none}"
        ".block-container{max-width:980px !important;padding-top:7vh !important;padding-bottom:7rem !important}</style>",
        unsafe_allow_html=True,
    )
    st.markdown(MARQUEE_HTML, unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 3, 1])
    with mid:
        st.markdown(
            "<div class='chip'><span class='dot'></span>Powered by Google Gemini</div>"
            "<div class='gate-h1'>A GPT that<br>loves to "
            "<span class='rot'><span class='rot-in'>"
            "<b class='w1'>explain.</b><b class='w2'>write.</b><b class='w3'>plan.</b><b class='w4'>code.</b><b class='w1'>explain.</b>"
            "</span></span></div>"
            "<div class='gate-sub'>Paste your free Gemini API key and start chatting in seconds. "
            "Your key stays in this browser session and is never stored.</div>",
            unsafe_allow_html=True,
        )
        with st.form("api_key_form", border=True):
            key = st.text_input(
                "Gemini API key",
                type="password",
                placeholder="Paste your Gemini API key",
                icon=":material/key:",
            )
            submitted = st.form_submit_button("Start chatting", icon=":material/arrow_forward:")
        if submitted:
            key = key.strip()
            if len(key) >= 20 and " " not in key:
                st.session_state.api_key = key
                st.rerun()
            else:
                st.error("That doesn't look like a Gemini API key. Copy the whole key from Google AI Studio.")

        st.markdown(
            "<div class='steps'>"
            "<a class='step s1' href='https://aistudio.google.com/apikey' target='_blank'><b>1</b>Get a free key</a>"
            "<div class='step s2'><b>2</b>Paste it above</div>"
            "<div class='step s3'><b>3</b>Start chatting</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    st.stop()

# ----------------------------------------------------------------------------
# Step 2: sidebar (history on the left)
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        "<div class='brand'><div class='mark'>✦</div><div class='name'>Custom GPT</div></div>",
        unsafe_allow_html=True,
    )

    if st.button("New chat", icon=":material/add:", type="primary", use_container_width=True):
        new_chat()
        st.rerun()

    st.markdown("<p class='side-label'>History</p>", unsafe_allow_html=True)
    for cid, chat_data in reversed(list(st.session_state.chats.items())):
        is_active = cid == st.session_state.current
        row, trash = st.columns([5, 1], vertical_alignment="center")
        with row:
            if st.button(
                chat_data["title"],
                key="active_chat" if is_active else f"chat_{cid}",
                icon=":material/chat_bubble:",
                use_container_width=True,
            ):
                st.session_state.current = cid
                st.rerun()
        with trash:
            if st.button("", key=f"del_{cid}", icon=":material/delete:", help="Delete chat"):
                del st.session_state.chats[cid]
                if not st.session_state.chats:
                    new_chat()
                elif st.session_state.current == cid:
                    st.session_state.current = list(st.session_state.chats)[-1]
                st.rerun()

    st.markdown("<p class='side-label'>Settings</p>", unsafe_allow_html=True)
    with st.expander("Model and behavior", icon=":material/tune:"):
        persona = st.selectbox("Persona", list(PERSONAS))
        system_message = st.text_area(
            "System role",
            value=PERSONAS[persona],
            key=f"sys_{persona}",  # each persona keeps its own editable text
            height=110,
            help="Tells the model how to behave in every reply.",
        )
        choice = st.selectbox("Model", MODELS + ["Custom..."])
        if choice == "Custom...":
            model_name = st.text_input("Model name", placeholder="e.g. gemini-3.5-flash") or MODELS[0]
        else:
            model_name = choice
        temperature = st.slider(
            "Temperature", 0.0, 2.0, 1.0, 0.1,
            help="Higher means more creative, lower means more focused. Gemini works well around 1.0.",
        )

    if st.button("Change API key", icon=":material/logout:", use_container_width=True):
        st.session_state.api_key = ""
        st.rerun()

# ----------------------------------------------------------------------------
# Step 3: chat area
# ----------------------------------------------------------------------------
current = st.session_state.chats[st.session_state.current]

# The prompt bar is created first so a clicked suggestion and a typed message take the same path.
prompt = st.chat_input("Message Custom GPT")
if not prompt and st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

if prompt:
    current["messages"].append(HumanMessage(content=prompt))
    if current["title"] == "New chat":
        current["title"] = prompt[:28] + ("..." if len(prompt) > 28 else "")

if not current["messages"]:
    st.markdown(
        "<div class='hero'><div class='mark'>✦</div>"
        "<h1>What can I <span class='hl'>help</span> with <span class='hl pk'>today?</span></h1>"
        "<p>Ask a question, draft something, or paste text to work on.</p></div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for i, (label, text) in enumerate(SUGGESTIONS):
        with cols[i % 2]:
            if st.button(label, key=f"sugg_{i}", help=text, use_container_width=True):
                st.session_state.pending_prompt = text
                st.rerun()

for msg in current["messages"]:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.markdown(msg.content)

if prompt:
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        google_api_key=st.session_state.api_key,
    )
    full_context = [SystemMessage(content=system_message or PERSONAS["Custom"])] + current["messages"]

    with st.chat_message("assistant"):
        slot = st.empty()
        slot.markdown(TYPING_HTML, unsafe_allow_html=True)
        reply = ""
        try:
            for chunk in llm.stream(full_context):
                reply += chunk_text(chunk.content)
                slot.markdown(reply + " ▌")
            slot.markdown(reply)
        except Exception as exc:
            slot.empty()
            current["messages"].pop()  # drop the unanswered prompt
            st.error(friendly_error(exc))
            st.stop()

    current["messages"].append(AIMessage(content=reply))
    st.rerun()