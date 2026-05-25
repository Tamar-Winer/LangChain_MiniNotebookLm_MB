import time
from urllib.parse import urlparse
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from langgraph.types import Command
from agent.research_agent import create_research_graph

st.set_page_config(
    page_title="NotebookLM Mini",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
/* ═══ BASE ══════════════════════════════════════════════════════════════════ */
.stApp {
    background: #040714;
    font-family: 'Inter', sans-serif !important;
    min-height: 100vh;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding-top: 0 !important;
    padding-bottom: 4rem;
    max-width: 820px;
}

/* ═══ AMBIENT BACKGROUND ════════════════════════════════════════════════════ */
.orb-wrap {
    position: fixed; inset: 0;
    pointer-events: none; z-index: 0; overflow: hidden;
}
.orb {
    position: absolute; border-radius: 50%;
    filter: blur(90px);
}
.orb-1 {
    width: 560px; height: 560px;
    background: radial-gradient(circle, rgba(124,58,237,0.20) 0%, transparent 70%);
    top: -180px; left: -160px;
    animation: orb1 20s ease-in-out infinite;
}
.orb-2 {
    width: 480px; height: 480px;
    background: radial-gradient(circle, rgba(37,99,235,0.16) 0%, transparent 70%);
    bottom: -140px; right: -120px;
    animation: orb2 24s ease-in-out infinite;
}
.orb-3 {
    width: 380px; height: 380px;
    background: radial-gradient(circle, rgba(6,182,212,0.11) 0%, transparent 70%);
    top: 40%; left: 55%;
    animation: orb3 16s ease-in-out infinite;
}
@keyframes orb1 {
    0%,100%{ transform:translate(0,0) scale(1); }
    33%    { transform:translate(45px,-35px) scale(1.07); }
    66%    { transform:translate(-30px,40px) scale(0.95); }
}
@keyframes orb2 {
    0%,100%{ transform:translate(0,0) scale(1); }
    40%    { transform:translate(-50px,28px) scale(1.10); }
    70%    { transform:translate(28px,-40px) scale(0.93); }
}
@keyframes orb3 {
    0%,100%{ transform:translate(0,0) scale(1); opacity:.8; }
    50%    { transform:translate(-35px,22px) scale(1.14); opacity:1; }
}
.grid-veil {
    position: fixed; inset: 0;
    background-image:
        linear-gradient(rgba(167,139,250,0.022) 1px, transparent 1px),
        linear-gradient(90deg, rgba(167,139,250,0.022) 1px, transparent 1px);
    background-size: 44px 44px;
    pointer-events: none; z-index: 0;
}

/* ═══ HERO ══════════════════════════════════════════════════════════════════ */
.hero { text-align: center; padding: 2.6rem 0 1rem; }

.hero-pill {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(124,58,237,0.12);
    border: 1px solid rgba(124,58,237,0.30);
    border-radius: 100px;
    padding: 5px 15px;
    font-size: 0.70rem; font-weight: 700;
    letter-spacing: 0.13em; color: #a78bfa;
    text-transform: uppercase;
    margin-bottom: 1.1rem;
    animation: fadeDown 0.6s ease-out;
}
.hero-pill-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #a78bfa;
    box-shadow: 0 0 8px #a78bfa;
    animation: blink 2s ease-in-out infinite;
}
@keyframes blink { 0%,100%{opacity:1;} 50%{opacity:0.25;} }

.main-title {
    font-size: 3.3rem; font-weight: 900;
    background: linear-gradient(135deg, #c4b5fd 0%, #818cf8 30%, #60a5fa 65%, #34d399 100%);
    background-size: 280% auto;
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.045em; line-height: 1.08;
    animation: gradShift 7s linear infinite, fadeDown 0.7s ease-out;
}
@keyframes gradShift {
    0%   { background-position: 0% center; }
    100% { background-position: 280% center; }
}
@keyframes fadeDown {
    from { opacity:0; transform:translateY(-18px); }
    to   { opacity:1; transform:translateY(0); }
}
.subtitle {
    font-size: 0.78rem; font-weight: 500; color: #3f4f66;
    letter-spacing: 0.12em; text-transform: uppercase;
    margin-top: 0.55rem;
    animation: fadeDown 0.9s ease-out;
}

/* ═══ PROGRESS STEPS ════════════════════════════════════════════════════════ */
.steps-wrap {
    display: flex; justify-content: center; align-items: center;
    padding: 0.4rem 0 2.4rem; gap: 0;
}
.step-item { display:flex; flex-direction:column; align-items:center; gap:8px; }
.step-dot {
    width: 46px; height: 46px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.9rem; font-weight: 800;
    transition: all 0.4s ease; z-index: 1; position: relative;
}
.sd-active {
    background: linear-gradient(135deg, #7c3aed, #3b82f6);
    color: #fff;
    box-shadow: 0 0 0 4px rgba(124,58,237,0.18), 0 0 22px rgba(124,58,237,0.55);
    animation: glow 2.5s ease-in-out infinite;
}
.sd-done {
    background: linear-gradient(135deg, #059669, #0d9488);
    color: #fff; box-shadow: 0 0 18px rgba(5,150,105,0.50);
}
.sd-idle {
    background: rgba(255,255,255,0.04); color: #2d3f55;
    border: 1.5px solid rgba(255,255,255,0.06);
}
@keyframes glow {
    0%,100%{ box-shadow:0 0 0 4px rgba(124,58,237,0.18),0 0 22px rgba(124,58,237,0.55); }
    50%    { box-shadow:0 0 0 9px rgba(124,58,237,0.08),0 0 42px rgba(124,58,237,0.75); }
}
.step-lbl {
    font-size: 0.63rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.11em; color: #2d3f55;
}
.sl-active { color: #a78bfa; }
.sl-done   { color: #34d399; }
.step-conn {
    width: 80px; height: 2px; margin-bottom: 30px;
    background: rgba(255,255,255,0.055); border-radius: 2px; overflow: hidden;
}
.sc-lit { background: transparent; position:relative; }
.sc-lit::after {
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(90deg, #7c3aed, #3b82f6);
    box-shadow: 0 0 10px rgba(124,58,237,0.5);
    animation: sweep 0.65s ease-out forwards;
}
@keyframes sweep {
    from{ transform:scaleX(0); transform-origin:left; }
    to  { transform:scaleX(1); transform-origin:left; }
}

/* ═══ CHAT BUBBLES ══════════════════════════════════════════════════════════ */
.chat-wrap { margin: 10px 0; animation: popUp 0.4s cubic-bezier(0.34,1.56,0.64,1); }
@keyframes popUp {
    from{ opacity:0; transform:translateY(14px) scale(0.97); }
    to  { opacity:1; transform:translateY(0) scale(1); }
}
.row-a { display:flex; align-items:flex-start; gap:13px; }
.row-u { display:flex; align-items:flex-start; gap:13px; flex-direction:row-reverse; }
.av {
    width:41px; height:41px; border-radius:50%; flex-shrink:0;
    display:flex; align-items:center; justify-content:center; font-size:1.2rem;
}
.av-a { background:linear-gradient(135deg,#7c3aed,#3b82f6); box-shadow:0 4px 18px rgba(124,58,237,0.40); }
.av-u { background:linear-gradient(135deg,#059669,#0d9488); box-shadow:0 4px 18px rgba(5,150,105,0.36); }
.bubble {
    max-width:80%; padding:12px 16px;
    font-size:0.93rem; line-height:1.72; color:#c8d5e8;
}
.bbl-a {
    background:rgba(255,255,255,0.040);
    border:1px solid rgba(167,139,250,0.18);
    border-radius:4px 16px 16px 16px;
    backdrop-filter:blur(18px); -webkit-backdrop-filter:blur(18px);
}
.bbl-u {
    background:rgba(124,58,237,0.14);
    border:1px solid rgba(124,58,237,0.26);
    border-radius:16px 4px 16px 16px;
}

/* ═══ SOURCE CARDS ══════════════════════════════════════════════════════════ */
.src-card {
    background: rgba(255,255,255,0.028);
    border: 1px solid rgba(167,139,250,0.13);
    border-radius: 16px;
    padding: 14px 18px;
    margin: 3px 0 2px;
    transition: all 0.28s cubic-bezier(0.4,0,0.2,1);
    position: relative; overflow: hidden;
}
.src-card::after {
    content: '';
    position: absolute; left:0; top:0; bottom:0; width:3px;
    background: linear-gradient(180deg, #7c3aed, #3b82f6);
    opacity: 0; transition: opacity 0.28s;
}
.src-card:hover {
    border-color: rgba(167,139,250,0.35);
    background: rgba(255,255,255,0.048);
    transform: translateX(5px);
    box-shadow: -3px 0 24px rgba(124,58,237,0.13), 0 4px 28px rgba(0,0,0,0.25);
}
.src-card:hover::after { opacity: 1; }
.src-badge {
    display:inline-flex; align-items:center; justify-content:center;
    width:26px; height:26px; border-radius:8px;
    background:linear-gradient(135deg,#7c3aed,#3b82f6);
    font-size:0.70rem; font-weight:800; color:#fff;
    margin-right:10px; flex-shrink:0;
}
.src-title { font-size:0.92rem; font-weight:600; color:#dde5f2; }
.src-domain { font-size:0.71rem; color:#6366f1; margin-top:4px; opacity:.85; }
.src-domain::before { content:'🔗  '; }

/* ═══ STATS BAR ═════════════════════════════════════════════════════════════ */
.stats-bar {
    display:flex; align-items:center; gap:18px;
    background:rgba(255,255,255,0.028);
    border:1px solid rgba(167,139,250,0.13);
    border-radius:14px; padding:12px 20px; margin:16px 0 20px;
}
.stat-item { display:flex; align-items:center; gap:7px; font-size:0.80rem; color:#64748b; font-weight:500; }
.stat-num {
    font-size:1.15rem; font-weight:800;
    background:linear-gradient(135deg,#a78bfa,#60a5fa);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}
.stats-sep { width:1px; height:22px; background:rgba(255,255,255,0.06); }

/* ═══ CHIPS ══════════════════════════════════════════════════════════════════ */
.chips { display:flex; gap:9px; justify-content:center; flex-wrap:wrap; margin-top:1.9rem; }
.chip {
    border-radius:100px; padding:5px 14px;
    font-size:0.74rem; font-weight:600;
    animation: fadeDown 1s ease-out;
}
.chip-p { background:rgba(124,58,237,0.12); border:1px solid rgba(124,58,237,0.28); color:#a78bfa; }
.chip-b { background:rgba(37, 99,235,0.12); border:1px solid rgba(37, 99,235,0.28); color:#60a5fa; }
.chip-c { background:rgba(  6,182,212,0.12); border:1px solid rgba(  6,182,212,0.28); color:#67e8f9; }
.chip-g { background:rgba( 16,185,129,0.12); border:1px solid rgba( 16,185,129,0.28); color:#6ee7b7; }

/* ═══ DONE HEADER ════════════════════════════════════════════════════════════ */
.done-head { text-align:center; padding:1.4rem 0 0.6rem; }
.done-icon { font-size:3rem; animation:popBounce 0.55s cubic-bezier(0.34,1.56,0.64,1); display:block; }
@keyframes popBounce {
    from{ transform:scale(0.2) rotate(-15deg); opacity:0; }
    to  { transform:scale(1)   rotate(0deg);   opacity:1; }
}
.done-title {
    font-size:1.65rem; font-weight:800; margin:.35rem 0 .2rem;
    background:linear-gradient(135deg,#34d399,#06b6d4);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}
.done-sub { font-size:0.83rem; color:#3f4f66; }

/* ═══ BUTTONS ════════════════════════════════════════════════════════════════ */
.stButton > button {
    background: linear-gradient(135deg,#7c3aed 0%,#3b82f6 100%) !important;
    color:#fff !important; border:none !important;
    border-radius:13px !important; padding:12px 26px !important;
    font-size:0.95rem !important; font-weight:700 !important;
    letter-spacing:0.02em !important;
    transition:all 0.28s ease !important;
    box-shadow:0 4px 22px rgba(124,58,237,0.35) !important;
    width:100% !important;
}
.stButton > button:hover {
    transform:translateY(-3px) !important;
    box-shadow:0 14px 38px rgba(124,58,237,0.58) !important;
    filter:brightness(1.07) !important;
}
.stButton > button:active { transform:translateY(-1px) !important; }

/* ═══ INPUT ══════════════════════════════════════════════════════════════════ */
.stTextInput > div > div > input {
    background:rgba(255,255,255,0.042) !important;
    border:1.5px solid rgba(167,139,250,0.22) !important;
    border-radius:14px !important; color:#f0f4fb !important;
    padding:14px 18px !important; font-size:1rem !important;
    font-family:'Inter',sans-serif !important;
    caret-color:#a78bfa !important; transition:all 0.28s ease !important;
}
.stTextInput > div > div > input:focus {
    border-color:#7c3aed !important;
    box-shadow:0 0 0 3px rgba(124,58,237,0.18),0 4px 26px rgba(124,58,237,0.12) !important;
    background:rgba(255,255,255,0.062) !important;
}
.stTextInput > div > div > input::placeholder { color:#28374d !important; }
.stTextInput label { color:#3f4f66 !important; font-size:0.80rem !important; }

/* ═══ CHECKBOX ═══════════════════════════════════════════════════════════════ */
.stCheckbox label { color:#94a3b8 !important; font-size:0.84rem !important; }

/* ═══ EXPANDER ═══════════════════════════════════════════════════════════════ */
[data-testid="stExpander"] details summary {
    background:rgba(255,255,255,0.022) !important;
    border-radius:9px !important; color:#475569 !important;
    font-size:0.77rem !important;
    border:1px solid rgba(167,139,250,0.09) !important;
}

/* ═══ TABS ═══════════════════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    background:rgba(255,255,255,0.038) !important;
    border-radius:14px !important; padding:5px !important;
    border:1px solid rgba(167,139,250,0.14) !important; gap:4px !important;
}
.stTabs [data-baseweb="tab"] {
    background:transparent !important; color:#3f5068 !important;
    border-radius:10px !important; font-weight:600 !important;
    font-size:0.87rem !important; transition:all 0.24s !important;
    padding:8px 20px !important;
}
.stTabs [aria-selected="true"] {
    background:linear-gradient(135deg,#7c3aed,#3b82f6) !important;
    color:#fff !important; box-shadow:0 4px 18px rgba(124,58,237,0.38) !important;
}
.stTabs [data-baseweb="tab-panel"] {
    background:rgba(255,255,255,0.022) !important;
    border:1px solid rgba(167,139,250,0.13) !important;
    border-radius:0 14px 14px 14px !important;
    padding:22px 24px !important; margin-top:1px !important;
}

/* ═══ SPINNER ════════════════════════════════════════════════════════════════ */
[data-testid="stSpinner"] { color: #a78bfa !important; }

/* ═══ SIDEBAR ════════════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background:rgba(4,7,20,0.96) !important;
    border-right:1px solid rgba(167,139,250,0.10) !important;
}
[data-testid="stSidebar"] .block-container { padding-top:1.5rem !important; }

/* ═══ MISC ═══════════════════════════════════════════════════════════════════ */
hr { border-color:rgba(167,139,250,0.08) !important; }
p, li { color:#c8d5e8; }
::-webkit-scrollbar { width:5px; }
::-webkit-scrollbar-thumb { background:linear-gradient(#7c3aed,#3b82f6); border-radius:3px; }
</style>
""", unsafe_allow_html=True)

# ── Ambient background ────────────────────────────────────────────────────────
st.markdown("""
<div class="orb-wrap" aria-hidden="true">
  <div class="orb orb-1"></div>
  <div class="orb orb-2"></div>
  <div class="orb orb-3"></div>
  <div class="grid-veil"></div>
</div>
""", unsafe_allow_html=True)


# ── HTML helpers ──────────────────────────────────────────────────────────────

def steps_html(stage: str) -> str:
    order  = ["input", "reviewing", "done"]
    labels = ["Search", "Review", "Summary"]
    idx    = order.index(stage)

    html = '<div class="steps-wrap">'
    for i, label in enumerate(labels):
        done   = i < idx
        active = i == idx
        d_cls  = "sd-done" if done else ("sd-active" if active else "sd-idle")
        l_cls  = "sl-done" if done else ("sl-active" if active else "")
        icon   = "✓" if done else str(i + 1)
        html += (f'<div class="step-item">'
                 f'<div class="step-dot {d_cls}">{icon}</div>'
                 f'<div class="step-lbl {l_cls}">{label}</div>'
                 f'</div>')
        if i < 2:
            html += f'<div class="step-conn {"sc-lit" if i < idx else ""}"></div>'
    html += '</div>'
    return html


def agent_msg(text: str) -> str:
    return (f'<div class="chat-wrap"><div class="row-a">'
            f'<div class="av av-a">🤖</div>'
            f'<div class="bubble bbl-a">{text}</div>'
            f'</div></div>')


def user_msg(text: str) -> str:
    return (f'<div class="chat-wrap"><div class="row-u">'
            f'<div class="av av-u">👤</div>'
            f'<div class="bubble bbl-u">{text}</div>'
            f'</div></div>')


def src_card_html(i: int, src: dict) -> str:
    title = src.get("title", "Untitled")
    url   = src.get("url", "")
    try:
        domain = urlparse(url).netloc
    except Exception:
        domain = url
    return (f'<div class="src-card">'
            f'<div style="display:flex;align-items:center;">'
            f'<span class="src-badge">{i + 1}</span>'
            f'<span class="src-title">{title}</span>'
            f'</div>'
            f'<div class="src-domain">{domain}</div>'
            f'</div>')


# ── Sidebar ───────────────────────────────────────────────────────────────────

def _sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding:.8rem 0 .2rem;">
          <div style="font-size:1.25rem;font-weight:900;color:#dde5f2;letter-spacing:-0.02em;">📚 NotebookLM Mini</div>
          <div style="font-size:0.68rem;color:#2d3f55;text-transform:uppercase;letter-spacing:.11em;margin-top:3px;">AI Research Assistant</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<hr style='border-color:rgba(167,139,250,0.10);margin:10px 0 18px;'>", unsafe_allow_html=True)

        st.markdown("<div style='font-size:0.78rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.09em;margin-bottom:12px;'>How it works</div>", unsafe_allow_html=True)

        for num, title, desc, color in [
            ("1", "Enter a Topic",    "Agent runs 4–6 diverse search queries", "#7c3aed"),
            ("2", "Review Sources",   "Pick which results to keep or discard",  "#3b82f6"),
            ("3", "Get Summary",      "AI synthesises your curated sources",     "#059669"),
        ]:
            st.markdown(f"""
            <div style="display:flex;gap:11px;align-items:flex-start;margin-bottom:14px;">
              <div style="background:{color};border-radius:8px;width:28px;height:28px;
                          display:flex;align-items:center;justify-content:center;
                          font-size:0.78rem;font-weight:800;color:#fff;flex-shrink:0;">{num}</div>
              <div>
                <div style="font-size:0.83rem;font-weight:600;color:#dde5f2;">{title}</div>
                <div style="font-size:0.73rem;color:#3f4f66;margin-top:2px;">{desc}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr style='border-color:rgba(167,139,250,0.08);margin:6px 0 16px;'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.78rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.09em;margin-bottom:10px;'>Tips</div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:0.76rem;color:#3a4f65;line-height:1.75;">
          💡 Specific topics yield better sources — <em>"AI in cancer detection 2024"</em> beats <em>"AI in medicine"</em><br><br>
          💡 Quality over quantity — 5 great sources trump 15 mediocre ones<br><br>
          💡 Preview shows the first 450 characters of each article
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr style='border-color:rgba(167,139,250,0.08);margin:16px 0 12px;'>", unsafe_allow_html=True)
        st.markdown("""
        <div style="display:flex;flex-direction:column;gap:6px;">
          <div style="display:flex;align-items:center;gap:7px;">
            <span style="font-size:0.68rem;background:rgba(124,58,237,0.15);border:1px solid rgba(124,58,237,0.28);border-radius:6px;padding:2px 8px;color:#a78bfa;font-weight:600;">LangGraph</span>
            <span style="font-size:0.68rem;background:rgba(37,99,235,0.15);border:1px solid rgba(37,99,235,0.28);border-radius:6px;padding:2px 8px;color:#60a5fa;font-weight:600;">Tavily</span>
            <span style="font-size:0.68rem;background:rgba(16,185,129,0.15);border:1px solid rgba(16,185,129,0.28);border-radius:6px;padding:2px 8px;color:#6ee7b7;font-weight:600;">GPT-4o-mini</span>
          </div>
        </div>
        """, unsafe_allow_html=True)


# ── Session helpers ───────────────────────────────────────────────────────────

def _init():
    if "graph" not in st.session_state:
        st.session_state.graph = create_research_graph()
    st.session_state.setdefault("stage",     "input")
    st.session_state.setdefault("thread_id", f"t-{int(time.time())}")
    st.session_state.setdefault("topic",     "")


def _cfg():
    return {"configurable": {"thread_id": st.session_state.thread_id}}


def _reset():
    for key in [k for k in st.session_state if k.startswith("src_")]:
        del st.session_state[key]
    st.session_state.stage     = "input"
    st.session_state.thread_id = f"t-{int(time.time())}"
    st.session_state.topic     = ""


# ── Pages ─────────────────────────────────────────────────────────────────────

def page_input():
    st.markdown(steps_html("input"), unsafe_allow_html=True)

    st.markdown(agent_msg(
        "Hello! I'm your AI research assistant. 🔭<br>"
        "Give me any topic and I'll autonomously run <strong>multiple search queries</strong> "
        "across different angles — then hand the sources over to you for review before generating a summary."
    ), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    topic = st.text_input("", placeholder="e.g.  The future of quantum computing in cryptography")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀  Start Research"):
            if not topic.strip():
                st.warning("Please enter a topic first.")
                return
            st.session_state.topic = topic.strip()
            with st.spinner("🔍  Agent is searching the web…"):
                st.session_state.graph.invoke(
                    {"topic": topic.strip(), "sources": [], "approved_sources": [], "summary": ""},
                    config=_cfg(),
                )
            st.session_state.stage = "reviewing"
            st.rerun()

    st.markdown("""
    <div class="chips">
      <span class="chip chip-p">🤖 GPT-4o-mini</span>
      <span class="chip chip-b">🔍 Tavily Search</span>
      <span class="chip chip-c">⚡ LangGraph</span>
      <span class="chip chip-g">✋ Human-in-the-Loop</span>
    </div>
    """, unsafe_allow_html=True)


def page_review():
    st.markdown(steps_html("reviewing"), unsafe_allow_html=True)

    gs      = st.session_state.graph.get_state(_cfg())
    sources = gs.values.get("sources", [])

    st.markdown(user_msg(f"Research topic: <strong>{st.session_state.topic}</strong>"), unsafe_allow_html=True)

    if not sources:
        st.markdown(agent_msg("Hmm, I couldn't find any sources for that topic. Try a different keyword?"),
                    unsafe_allow_html=True)
        if st.button("← Try Again"):
            _reset(); st.rerun()
        return

    st.markdown(agent_msg(
        f"I found <strong>{len(sources)} sources</strong> about "
        f"<em>{st.session_state.topic}</em>. ✅<br>"
        "Review them below — <strong>check the ones you want included</strong> in the final summary."
    ), unsafe_allow_html=True)

    # Quick-select row
    _, qa1, qa2 = st.columns([3, 1, 1])
    with qa1:
        if st.button("☑  All"):
            for i in range(len(sources)):
                st.session_state[f"src_{i}"] = True
            st.rerun()
    with qa2:
        if st.button("☐  None"):
            for i in range(len(sources)):
                st.session_state[f"src_{i}"] = False
            st.rerun()

    # Initialise defaults
    for i in range(len(sources)):
        st.session_state.setdefault(f"src_{i}", True)

    checked: dict[int, bool] = {}
    for i, src in enumerate(sources):
        col_card, col_cb = st.columns([14, 1])
        with col_card:
            st.markdown(src_card_html(i, src), unsafe_allow_html=True)
            with st.expander("📄 Preview"):
                st.write(src.get("content", "")[:450])
        with col_cb:
            st.markdown("<br><br>", unsafe_allow_html=True)
            checked[i] = st.checkbox("", key=f"src_{i}")

    selected_count = sum(1 for ok in checked.values() if ok)
    st.markdown(f"""
    <div class="stats-bar">
      <div class="stat-item">Sources found <span class="stat-num">{len(sources)}</span></div>
      <div class="stats-sep"></div>
      <div class="stat-item">Selected <span class="stat-num">{selected_count}</span></div>
      <div class="stats-sep"></div>
      <div class="stat-item">Excluded <span class="stat-num">{len(sources) - selected_count}</span></div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅  Approve & Summarize"):
            selected = [sources[i] for i, ok in checked.items() if ok]
            if not selected:
                st.error("Please select at least one source.")
                return
            with st.spinner("✍️  Generating your summary…"):
                st.session_state.graph.invoke(Command(resume=selected), config=_cfg())
            st.session_state.stage = "done"
            st.rerun()
    with col2:
        if st.button("🔄  Start Over"):
            _reset(); st.rerun()


def page_done():
    st.markdown(steps_html("done"), unsafe_allow_html=True)

    gs       = st.session_state.graph.get_state(_cfg())
    summary  = gs.values.get("summary", "")
    approved = gs.values.get("approved_sources", [])

    st.markdown(f"""
    <div class="done-head">
      <span class="done-icon">🎉</span>
      <div class="done-title">Research Complete!</div>
      <div class="done-sub">Summary synthesised from {len(approved)} verified source{'s' if len(approved) != 1 else ''}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(user_msg(
        f"Topic: <strong>{st.session_state.topic}</strong> — "
        f"approved <strong>{len(approved)}</strong> source{'s' if len(approved) != 1 else ''}"
    ), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    tab_sum, tab_src = st.tabs(["📝  Summary", "🔗  Sources"])

    with tab_sum:
        st.markdown(summary)

    with tab_src:
        for i, src in enumerate(approved):
            st.markdown(src_card_html(i, src), unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔍  Research New Topic"):
            _reset(); st.rerun()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    _init()
    _sidebar()

    st.markdown("""
    <div class="hero">
      <div class="hero-pill">
        <span class="hero-pill-dot"></span>
        AI Research Agent
      </div>
      <div class="main-title">📚 NotebookLM Mini</div>
      <div class="subtitle">LangGraph &nbsp;·&nbsp; Tavily Search &nbsp;·&nbsp; Human-in-the-Loop</div>
    </div>
    """, unsafe_allow_html=True)

    stage = st.session_state.stage
    if   stage == "input":     page_input()
    elif stage == "reviewing": page_review()
    elif stage == "done":      page_done()


if __name__ == "__main__":
    main()
