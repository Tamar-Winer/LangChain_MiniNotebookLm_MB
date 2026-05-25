# NotebookLM Mini 📚

An AI-powered research assistant that mimics Google's NotebookLM source-collection workflow.  
The agent autonomously searches the web, then hands control back to you so you can choose which sources to keep before generating a summary.

---

## What it does

1. You enter a research topic
2. The AI agent independently runs 4–6 Tavily searches with varied queries
3. You review the collected sources and select which ones to include (**Human-in-the-Loop**)
4. The agent generates a structured summary from your approved sources

---

## Tech Stack

| Tool | Role |
|------|------|
| **LangGraph** | Agent graph + state management + checkpointing |
| **LangChain** | LLM abstraction layer |
| **Tavily** | AI-optimised web search |
| **OpenAI GPT-4o-mini** | Language model |
| **Streamlit** | Web UI |

---

## Setup

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd "Project5 LangChain"
pip install -r requirements.txt
```

### 2. Add your API keys

```bash
cp .env.example .env
```

Edit `.env` and fill in your keys:

```
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
```

- OpenAI key → https://platform.openai.com/api-keys  
- Tavily key → https://tavily.com (free tier available — 1,000 searches/month)

### 3. Run the app

```bash
streamlit run app.py
```

The app opens at **http://localhost:8501**

---

## Architecture

```
[User enters topic]
        ↓
  ┌─────────────┐
  │  research   │  Agent runs 4-6 Tavily searches autonomously
  │    node     │
  └──────┬──────┘
         ↓
  ┌─────────────┐
  │ human_review│  ← INTERRUPT — execution pauses here
  │    node     │  User selects which sources to keep
  └──────┬──────┘
         ↓ (Command.resume with selected sources)
  ┌─────────────┐
  │  summarize  │  Generates structured summary from approved sources
  │    node     │
  └──────┬──────┘
         ↓
  [Summary displayed to user]
```

**Checkpointer:** `MemorySaver` persists state between the interrupt and resume calls within the same session.

---

## Example Topics

- Climate change and renewable energy
- Machine learning in medical diagnosis
- The history of the internet
- Python programming best practices
- Space exploration future missions
- The impact of social media on mental health

---

## Project Structure

```
Project5 LangChain/
├── agent/
│   ├── __init__.py
│   └── research_agent.py   # LangGraph graph: research → HITL → summarize
├── app.py                  # Streamlit UI
├── requirements.txt
├── .env.example
└── README.md
```
