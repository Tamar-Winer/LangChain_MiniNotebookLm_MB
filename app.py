import time
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
<style>
/* ─ Base ──────────────────────────────────────────────────────────────────── */
.stApp {
    background: linear-gradient(135deg, #060818 0%, #0e0b2e 50%, #060d20 100%);
    min-height: 100vh;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 860px; }

/* ─ Animated gradient title ────────────────────────────────────────────────── */
.main-title {
    font-size: 2.9rem;
    font-weight: 900;
    background: linear-gradient(270deg, #a78bfa, #60a5fa, #34d399, #a78bfa);
    background-size: 300% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    animation: gradientShift 5s linear infinite, fadeSlideDown 0.7s ease-out;
    letter-spacing: -0.02em;
}

@keyframes gradientShift {
    0%   { background-position: 0%   center; }
    100% { background-position: 300% center; }
}

@keyframes fadeSlideDown {
    from { opacity: 0; transform: translateY(-18px); }
    to   { opacity: 1; transform: translateY(0);     }
}

.subtitle {
    text-align: center;
    color: #475569 !important;
    font-size: 0.9rem;
    margin-top: 0.3rem;
    margin-bottom: 1.6rem;
    letter-spacing: 0.06em;
    animation: fadeSlideDown 0.9s ease-out;
}

/* ─ Progress steps ─────────────────────────────────────────────────────────── */
.steps-bar {
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 0.5rem 0 2rem;
}

.step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 7px;
}

.step-dot {
    width: 42px;
    height: 42px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.95rem;
    font-weight: 800;
    transition: all 0.4s ease;
    z-index: 1;
}

.step-dot.active {
    background: linear-gradient(135deg, #7c3aed, #2563eb);
    color: #fff;
    animation: dotGlow 2s ease-in-out infinite;
}

.step-dot.done {
    background: linear-gradient(135deg, #059669, #0d9488);
    color: #fff;
    box-shadow: 0 0 14px rgba(5,150,105,0.55);
}

.step-dot.inactive {
    background: rgba(255,255,255,0.05);
    color: #334155;
    border: 1.5px solid rgba(255,255,255,0.08);
}

@keyframes dotGlow {
    0%,100% { box-shadow: 0 0 18px rgba(124,58,237,0.7); }
    50%      { box-shadow: 0 0 36px rgba(124,58,237,1), 0 0 70px rgba(37,99,235,0.45); }
}

.step-line {
    width: 70px;
    height: 2px;
    margin-bottom: 26px;
    background: rgba(255,255,255,0.07);
    border-radius: 2px;
    transition: background 0.5s ease;
}

.step-line.lit {
    background: linear-gradient(90deg, #7c3aed, #2563eb);
    box-shadow: 0 0 8px rgba(124,58,237,0.45);
}

.step-label {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #334155;
}
.step-label.active { color: #a78bfa; }
.step-label.done   { color: #34d399; }

/* ─ Chat bubbles ────────────────────────────────────────────────────────────── */
.chat-wrap { margin: 12px 0; animation: slideUp 0.45s ease-out; }

@keyframes slideUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0);    }
}

.chat-row-agent {
    display: flex; align-items: flex-start; gap: 13px;
}
.chat-row-user {
    display: flex; align-items: flex-start; gap: 13px;
    flex-direction: row-reverse;
}

.avatar {
    width: 42px; height: 42px; border-radius: 50%; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center; font-size: 1.25rem;
}
.av-agent { background: linear-gradient(135deg,#7c3aed,#2563eb); box-shadow: 0 4px 14px rgba(124,58,237,0.45); }
.av-user  { background: linear-gradient(135deg,#059669,#0d9488); box-shadow: 0 4px 14px rgba(5,150,105,0.4); }

.bubble {
    max-width: 78%;
    padding: 13px 17px;
    font-size: 0.95rem;
    line-height: 1.65;
    color: #e2e8f0;
}
.bbl-agent {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(167,139,250,0.22);
    border-radius: 4px 18px 18px 18px;
    backdrop-filter: blur(12px);
}
.bbl-user {
    background: rgba(124,58,237,0.18);
    border: 1px solid rgba(124,58,237,0.32);
    border-radius: 18px 4px 18px 18px;
}

/* ─ Source cards ────────────────────────────────────────────────────────────── */
.src-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(167,139,250,0.18);
    border-radius: 14px;
    padding: 14px 18px;
    margin: 4px 0 0;
    transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
    position: relative; overflow: hidden;
}
.src-card::before {
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(120deg, rgba(167,139,250,0.05) 0%, transparent 55%);
    pointer-events: none;
}
.src-card:hover {
    border-color: rgba(167,139,250,0.5);
    transform: translateX(5px);
    box-shadow: -4px 0 20px rgba(124,58,237,0.18);
}

.src-num {
    display: inline-flex; align-items: center; justify-content: center;
    width: 25px; height: 25px; border-radius: 50%;
    background: linear-gradient(135deg,#7c3aed,#2563eb);
    font-size: 0.72rem; font-weight: 800; color: #fff;
    margin-right: 9px; flex-shrink: 0;
}
.src-title { font-size: 0.95rem; font-weight: 600; color: #e2e8f0; }
.src-url   { font-size: 0.76rem; color: #7c3aed; opacity:.88; margin-top:3px; word-break:break-all; }

/* ─ Buttons ─────────────────────────────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #7c3aed 0%, #2563eb 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 13px !important;
    padding: 12px 28px !important;
    font-size: 0.97rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.025em !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 18px rgba(124,58,237,0.4) !important;
    width: 100% !important;
}
.stButton > button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 10px 32px rgba(124,58,237,0.62) !important;
    filter: brightness(1.08) !important;
}
.stButton > button:active { transform: translateY(-1px) !important; }

/* ─ Text input ──────────────────────────────────────────────────────────────── */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.05) !important;
    border: 1.5px solid rgba(167,139,250,0.28) !important;
    border-radius: 13px !important;
    color: #f1f5f9 !important;
    padding: 13px 17px !important;
    font-size: 1rem !important;
    caret-color: #a78bfa !important;
    transition: all 0.3s !important;
}
.stTextInput > div > div > input:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.2) !important;
    background: rgba(255,255,255,0.08) !important;
}
.stTextInput > div > div > input::placeholder { color: #3f4f66 !important; }
.stTextInput label { color: #64748b !important; font-size: 0.85rem !important; }

/* ─ Checkbox ────────────────────────────────────────────────────────────────── */
.stCheckbox label { color: #94a3b8 !important; font-size: 0.87rem !important; }

/* ─ Expander ────────────────────────────────────────────────────────────────── */
.streamlit-expanderHeader {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 9px !important;
    color: #64748b !important;
    font-size: 0.8rem !important;
}

/* ─ Tabs ────────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 13px !important;
    padding: 4px !important;
    border: 1px solid rgba(167,139,250,0.18) !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #475569 !important;
    border-radius: 9px !important;
    font-weight: 600 !important;
    transition: all 0.25s !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg,#7c3aed,#2563eb) !important;
    color: #fff !important;
    box-shadow: 0 4px 14px rgba(124,58,237,0.38) !important;
}

/* ─ Divider & misc ──────────────────────────────────────────────────────────── */
hr { border-color: rgba(167,139,250,0.1) !important; }
h1,h2,h3,p { color: #e2e8f0; }
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-thumb { background: linear-gradient(#7c3aed,#2563eb); border-radius:3px; }
</style>
""", unsafe_allow_html=True)


# ── HTML helpers ──────────────────────────────────────────────────────────────

def steps_html(stage: str) -> str:
    order  = ["input", "reviewing", "done"]
    labels = ["Search", "Review", "Summary"]
    idx    = order.index(stage)

    html = '<div class="steps-bar">'
    for i, label in enumerate(labels):
        done   = i < idx
        active = i == idx
        cls    = "done" if done else ("active" if active else "inactive")
        lcls   = "done" if done else ("active" if active else "")
        icon   = "✓"  if done else str(i + 1)

        html += (f'<div class="step">'
                 f'<div class="step-dot {cls}">{icon}</div>'
                 f'<div class="step-label {lcls}">{label}</div>'
                 f'</div>')
        if i < 2:
            html += f'<div class="step-line {"lit" if i < idx else ""}"></div>'
    html += '</div>'
    return html


def agent_msg(text: str) -> str:
    return (f'<div class="chat-wrap"><div class="chat-row-agent">'
            f'<div class="avatar av-agent">🤖</div>'
            f'<div class="bubble bbl-agent">{text}</div>'
            f'</div></div>')


def user_msg(text: str) -> str:
    return (f'<div class="chat-wrap"><div class="chat-row-user">'
            f'<div class="avatar av-user">👤</div>'
            f'<div class="bubble bbl-user">{text}</div>'
            f'</div></div>')


def src_card_html(i: int, src: dict) -> str:
    title = src.get("title", "Untitled")
    url   = src.get("url", "")
    return (f'<div class="src-card">'
            f'<div style="display:flex;align-items:center;">'
            f'<span class="src-num">{i+1}</span>'
            f'<span class="src-title">{title}</span>'
            f'</div>'
            f'<div class="src-url">🔗 {url}</div>'
            f'</div>')


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
    st.session_state.stage     = "input"
    st.session_state.thread_id = f"t-{int(time.time())}"
    st.session_state.topic     = ""


# ── Pages ─────────────────────────────────────────────────────────────────────

def page_input():
    st.markdown(steps_html("input"), unsafe_allow_html=True)
    st.markdown(agent_msg(
        "Hello! I'm your AI research assistant. 🔍<br>"
        "Tell me a topic and I'll autonomously search the web, collect diverse sources, "
        "and generate a comprehensive summary — with <strong>you</strong> in control of what makes the cut."
    ), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    topic = st.text_input("", placeholder="e.g.  The future of quantum computing")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀  Start Research"):
            if not topic.strip():
                st.warning("Please enter a topic first.")
                return
            st.session_state.topic = topic.strip()
            with st.spinner("🔍  Searching the web…"):
                st.session_state.graph.invoke(
                    {"topic": topic.strip(), "sources": [], "approved_sources": [], "summary": ""},
                    config=_cfg(),
                )
            st.session_state.stage = "reviewing"
            st.rerun()


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
        "Review them below and <strong>check the ones you want included</strong> in the summary."
    ), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    checked: dict[int, bool] = {}
    for i, src in enumerate(sources):
        col_card, col_cb = st.columns([14, 1])
        with col_card:
            st.markdown(src_card_html(i, src), unsafe_allow_html=True)
            with st.expander("📄 Preview content"):
                st.write(src.get("content", "")[:450])
        with col_cb:
            st.markdown("<br><br>", unsafe_allow_html=True)
            checked[i] = st.checkbox("", value=True, key=f"src_{i}")

    st.markdown("<br>", unsafe_allow_html=True)
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

    st.markdown(user_msg(
        f"Topic: <strong>{st.session_state.topic}</strong> — "
        f"approved <strong>{len(approved)}</strong> source{'s' if len(approved) != 1 else ''}"
    ), unsafe_allow_html=True)

    st.markdown(agent_msg(
        f"Here's your research summary for <em>{st.session_state.topic}</em> 📖<br>"
        f"Synthesised from <strong>{len(approved)}</strong> verified sources."
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

    st.markdown("""
    <div style="text-align:center; padding:1.8rem 0 0.5rem;">
        <div class="main-title">📚 NotebookLM Mini</div>
        <div class="subtitle">AI RESEARCH AGENT &nbsp;•&nbsp; HUMAN-IN-THE-LOOP &nbsp;•&nbsp; LANGGRAPH + TAVILY</div>
    </div>
    """, unsafe_allow_html=True)

    stage = st.session_state.stage
    if   stage == "input":     page_input()
    elif stage == "reviewing": page_review()
    elif stage == "done":      page_done()


if __name__ == "__main__":
    main()
