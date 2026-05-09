# 🎬 AI Insights Assistant

> An agentic analytics chatbot for a fictional entertainment company — ask natural-language questions, get grounded answers backed by real database queries and internal PDF reports.

---

## What it does

Ask things like *"Why is comedy underperforming?"* or *"Compare Stellar Run and Dark Orbit"* and the assistant:

1. Decides which tools to call (SQL queries, PDF search, or both)
2. Fetches real numbers from a SQLite database (~18k rows across 6 tables)
3. Searches internal PDF reports using TF-IDF
4. Returns a concise, grounded answer — no hallucination from training data

Every response includes a **tool trace dropdown** showing exactly which queries ran and which documents were searched.

---

## Demo

```
You:  Why is Stellar Run trending recently?

AI:   - 568 total views with 84.4% completion rate (highest on the platform)
      - Viral #StellarRunChallenge TikTok campaign hit 50M impressions
      - Sequel announcement drove 35% ticket uplift
      - Sci-Fi audience in 18–34 demographic responding strongly

      [▶ Tools used (3)]
        get_movie_details          {"title": "Stellar Run"}
        get_trending_content       {"days": "30", "limit": "5"}
        search_internal_documents  {"query": "Stellar Run trending viral"}
```

---

## Architecture

```
React + Vite (frontend, port 5175)
    │
    │  POST /chat  { message }
    ▼
FastAPI (backend, port 8000)
    │
    ├─► AI Service (Groq · Llama 3.1 8B)
    │   └─► Agentic tool loop (max 4 rounds)
    │       │
    │       ▼
    │   Tool Executor (allowlist · 9 tools)
    │       ├─► SQL Service ──► SQLite (6 tables · ~18k rows)
    │       └─► Document Service ──► TF-IDF over 5 PDFs
    │
    └─► /api/analytics/* (direct SQL for dashboard charts)
```

### Key decisions

| Decision | Rationale |
|---|---|
| **Groq** as LLM provider | Free tier, ~1s responses, native function calling |
| **Llama 3.1 8B** | Faster and cheaper than 70B; handles 9-tool dispatch well |
| **SQLite** | Zero setup, fits in the repo, fast enough for 18k rows |
| **Custom TF-IDF** (not ChromaDB) | 5 PDFs, ~7 chunks — ML overhead wasn't worth it |
| **React** (not Streamlit) | Proper API separation, more control over UI and tool-trace UX |
| **No auth** | Single-user demo, out of scope |

---

## Quick start

### Docker (recommended)

```bash
git clone <this-repo> ai-insights
cd ai-insights
cp .env.example .env        # add your Groq API key
docker compose up --build
```

- **http://localhost:5175** — the app
- **http://localhost:8000/docs** — Swagger / API docs

First build takes ~3 minutes. Subsequent starts are instant.

### Manual setup

Requires Python 3.12 and Node 20+.

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate          # Mac/Linux
# venv\Scripts\activate           # Windows

pip install -r requirements.txt
echo GROQ_API_KEY=gsk_xxx > .env
python -m uvicorn app.main:app --reload
```

**Frontend** (new terminal):
```bash
cd frontend
npm install
npm run dev
```

Get a free Groq key at https://console.groq.com/keys — takes 30 seconds, no credit card.

---

## Project structure

```
ai-insights/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, rate limiter
│   │   ├── ai_service.py            # LLM tool loop
│   │   ├── database.py              # SQLite + CSV loader
│   │   ├── routers/analytics.py     # /api/analytics/* (direct SQL)
│   │   ├── services/
│   │   │   ├── sql_services.py      # 8 SQL query functions
│   │   │   └── document_service.py  # PDF parsing + TF-IDF
│   │   └── tools/execute.py         # Tool schemas, allowlist, dispatch
│   ├── data/
│   │   ├── csv/                     # 6 pre-generated CSVs (committed)
│   │   └── pdfs/                    # 5 internal PDFs (committed)
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # Page router (Chat / Dashboard / History)
│   │   └── components/
│   │       ├── Sidebar.jsx
│   │       ├── Chat.jsx             # Chat UI + tool trace dropdown
│   │       ├── Dashboard.jsx        # KPIs, charts, filters, insights panel
│   │       └── History.jsx          # Past queries + delete buttons
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

> The data files are committed so reviewers don't need to run a generator. The seed script is in `backend/scripts/generate_data.py` — Stellar Run is rigged to trend, comedy is rigged to underperform, so the example questions land naturally.

---

## The 9 tools

The LLM can only call these. Anything outside this list is rejected by the executor.

| Tool | What it does |
|---|---|
| `get_top_movies` | Top movies by revenue, optional year filter |
| `get_movie_details` | Full info on one movie (financials, ratings, watch stats) |
| `compare_movies` | Side-by-side comparison with a winner verdict |
| `get_genre_trends` | Genre-level revenue, ratings, and ROI |
| `get_regional_performance` | City-level views and engagement |
| `get_audience_insights` | Demographics (age / subscription / device / preference) |
| `get_trending_content` | Most-watched titles in a recent time window |
| `get_marketing_roi` | Campaign spend by channel and movie |
| `search_internal_documents` | TF-IDF search over the 5 PDFs |

Adding a 10th tool takes ~5 lines: add the function to `sql_services.py`, then register it in `execute.py`'s `TOOLS` list and `DISPATCH` dict.

---

## Security

| Risk | Mitigation |
|---|---|
| SQL injection | All user-derived values go through `?` parameters — no f-string concatenation |
| Unauthorized tool calls | Hard allowlist of 9 tool names; anything else returns `{"error": "Unknown tool"}` |
| Prompt injection requesting raw SQL | No raw SQL tool is exposed |
| Quota abuse | Rate limiter: **30 chat requests / day / IP** (slowapi) |
| Hallucination from training data | `tool_choice="required"` on round 1 forces a tool call before any data answer |
| Secrets in repo | `.env` in `.gitignore`; `.env.example` committed as a safe template |
| CORS exposure | Locked to `localhost:5175` only |
| PII exposure | AI only sees aggregated query results, never raw viewer rows |

---

## Known trade-offs

- **Single-user demo** — no auth; anyone on localhost can hit the API.
- **In-memory query history** — clears on browser refresh. A real deployment would persist to Redis or a SQLite log table.
- **TF-IDF over embeddings** — works well for 5 PDFs; wouldn't scale past ~20. Zero ML dependencies was the deliberate trade-off.
- **Llama 3.1 8B over 3.3 70B** — faster and cheaper but occasionally fumbles multi-tool reasoning. The 70B line is commented in `ai_service.py`.
- **`tool_choice="required"` on round 1** — means even casual greetings may trigger a tool call. The alternative (`"auto"`) caused too much hallucination; wrong answers hurt UX more.

---

## Future improvements

- Persistent query history (Redis or a SQLite log table)
- User auth + per-user rate limits
- WebSocket streaming for live token output
- Server-side audit log of every tool call
- Vector embeddings for document search if PDF count grows past ~20
- Cost tracking dashboard (Groq tokens per session)

---

## Stack

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-Vite-61DAFB?style=flat&logo=react&logoColor=black)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![Groq](https://img.shields.io/badge/LLM-Groq%20%2F%20Llama%203.1-F54F29?style=flat)
