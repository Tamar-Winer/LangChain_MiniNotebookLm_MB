import json
from typing import TypedDict, List

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt


RESEARCH_SYSTEM_PROMPT = """You are a research assistant specialized in collecting comprehensive information sources.

Your goal is to search the internet and gather diverse, high-quality sources about the given topic.

Instructions:
- Run at least 4-6 different search queries using different angles and keywords
- Search from multiple perspectives: basics, recent developments, expert opinions, statistics, case studies
- Collect as many relevant sources as possible — the user will filter them later
- When you finish searching, briefly state how many sources you found"""


class Source(TypedDict):
    url: str
    title: str
    content: str


class ResearchState(TypedDict):
    topic: str
    sources: List[Source]
    approved_sources: List[Source]
    summary: str


def _extract_sources(messages: list) -> List[Source]:
    """Parse Tavily search results out of agent tool-call messages."""
    sources: List[Source] = []
    seen_urls: set = set()

    for msg in messages:
        if getattr(msg, "type", None) != "tool":
            continue
        try:
            results = json.loads(msg.content)
            if not isinstance(results, list):
                continue
            for r in results:
                url = r.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    sources.append(
                        Source(
                            url=url,
                            title=r.get("title", "Untitled"),
                            content=r.get("content", "")[:800],
                        )
                    )
        except Exception:
            pass

    return sources


def research_node(state: ResearchState) -> dict:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = create_react_agent(
        llm,
        tools=[TavilySearch(max_results=5)],
        prompt=RESEARCH_SYSTEM_PROMPT,
    )
    result = agent.invoke(
        {"messages": [HumanMessage(content=f"Collect sources about: {state['topic']}")]}
    )
    return {"sources": _extract_sources(result["messages"])}


def human_review_node(state: ResearchState) -> dict:
    # Pause here — caller receives state["sources"] and resumes with approved list
    approved = interrupt(state["sources"])
    return {"approved_sources": approved}


def summarize_node(state: ResearchState) -> dict:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    sources_text = "\n\n".join(
        f"Title: {s['title']}\nURL: {s['url']}\nContent: {s['content']}"
        for s in state["approved_sources"]
    )

    prompt = (
        f'Write a comprehensive summary about "{state["topic"]}" based on these sources:\n\n'
        f"{sources_text}\n\n"
        "Structure your response with:\n"
        "1. Overview\n"
        "2. Key Points\n"
        "3. Different Perspectives\n"
        "4. Conclusions"
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    return {"summary": response.content}


def create_research_graph():
    builder = StateGraph(ResearchState)

    builder.add_node("research", research_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("summarize", summarize_node)

    builder.add_edge(START, "research")
    builder.add_edge("research", "human_review")
    builder.add_edge("human_review", "summarize")
    builder.add_edge("summarize", END)

    return builder.compile(checkpointer=MemorySaver())
