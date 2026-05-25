import time

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from langgraph.types import Command
from agent.research_agent import create_research_graph

st.set_page_config(page_title="NotebookLM Mini", page_icon="📚", layout="wide")


# ── Session helpers ──────────────────────────────────────────────────────────

def _init():
    if "graph" not in st.session_state:
        st.session_state.graph = create_research_graph()
    if "stage" not in st.session_state:
        st.session_state.stage = "input"
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"thread-{int(time.time())}"
    if "topic" not in st.session_state:
        st.session_state.topic = ""


def _config():
    return {"configurable": {"thread_id": st.session_state.thread_id}}


def _reset():
    st.session_state.stage = "input"
    st.session_state.thread_id = f"thread-{int(time.time())}"
    st.session_state.topic = ""


# ── Pages ────────────────────────────────────────────────────────────────────

def page_input():
    st.markdown("## 🔍 Research a Topic")
    st.markdown("Enter any topic and the AI agent will autonomously search the web for relevant sources.")

    topic = st.text_input(
        "Topic",
        placeholder="e.g., Artificial intelligence in healthcare",
    )

    if st.button("Start Research", type="primary") and topic.strip():
        st.session_state.topic = topic.strip()
        with st.spinner(f"Searching the web for: **{topic.strip()}**…"):
            st.session_state.graph.invoke(
                {
                    "topic": topic.strip(),
                    "sources": [],
                    "approved_sources": [],
                    "summary": "",
                },
                config=_config(),
            )
        st.session_state.stage = "reviewing"
        st.rerun()


def page_review():
    graph_state = st.session_state.graph.get_state(_config())
    sources = graph_state.values.get("sources", [])

    st.markdown(f"## 📋 Review Sources — *{st.session_state.topic}*")

    if not sources:
        st.warning("No sources were found. Try a different topic.")
        if st.button("← Back"):
            _reset()
            st.rerun()
        return

    st.markdown(
        f"The agent found **{len(sources)}** sources. "
        "Select the ones you want to include in the summary:"
    )
    st.divider()

    checked_map: dict[int, bool] = {}
    for i, src in enumerate(sources):
        col_check, col_info = st.columns([1, 11])
        with col_check:
            checked_map[i] = st.checkbox("", value=True, key=f"src_{i}")
        with col_info:
            st.markdown(f"**{src.get('title', 'Untitled')}**")
            url = src.get("url", "")
            st.markdown(f"[{url}]({url})")
            with st.expander("Preview content"):
                st.write(src.get("content", "")[:500])
        st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Approve & Summarize", type="primary"):
            selected = [sources[i] for i, ok in checked_map.items() if ok]
            if not selected:
                st.error("Please select at least one source.")
            else:
                with st.spinner("Generating summary from selected sources…"):
                    st.session_state.graph.invoke(
                        Command(resume=selected), config=_config()
                    )
                st.session_state.stage = "done"
                st.rerun()
    with col2:
        if st.button("🔄 Start Over"):
            _reset()
            st.rerun()


def page_done():
    graph_state = st.session_state.graph.get_state(_config())
    summary = graph_state.values.get("summary", "")
    approved = graph_state.values.get("approved_sources", [])

    st.markdown(f"## 📖 Summary — *{st.session_state.topic}*")

    tab_summary, tab_sources = st.tabs(["📝 Summary", "🔗 Sources"])

    with tab_summary:
        st.markdown(summary)

    with tab_sources:
        st.markdown(f"**{len(approved)} sources used:**")
        for src in approved:
            st.markdown(f"**{src.get('title', 'Untitled')}**")
            url = src.get("url", "")
            st.markdown(f"[{url}]({url})")
            st.write(src.get("content", "")[:300] + "…")
            st.divider()

    if st.button("🔍 New Research", type="primary"):
        _reset()
        st.rerun()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    _init()

    st.title("📚 NotebookLM Mini")
    st.caption("AI-powered research assistant with human-in-the-loop source selection")

    stage = st.session_state.stage
    if stage == "input":
        page_input()
    elif stage == "reviewing":
        page_review()
    elif stage == "done":
        page_done()


if __name__ == "__main__":
    main()
