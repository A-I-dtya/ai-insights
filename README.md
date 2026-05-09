# Secure AI Insights Assistant

An internal analytics chatbot for a fictional entertainment company. You ask things like
*"why is comedy weak?"* or *"compare Stellar Run and Dark Orbit"* and the assistant pulls
real numbers from the database, finds relevant snippets in our PDF reports, and gives you
a grounded answer — with a clear trace of which tools it used.

Built for the FF Task assignment.

---

## Demo

```
You:  Why is Stellar Run trending recently?

AI:   - 568 total views with 84.4% completion rate (highest on the platform)
      - Viral #StellarRunChallenge TikTok campaign hit 50M impressions
      - Sequel announcement drove 35% ticket uplift
      - Sci-Fi audience in 18-34 demographic responding strongly

      [> Tools used (3)]
        get_movie_details          {"title": "Stellar Run"}
        get_trending_content       {"days": "30", "limit": "5"}
        search_internal_documents  {"query": "Stellar Run trending viral"}
```

The dropdown at the bottom is the explainability layer — you can see exactly which
SQL queries ran and which PDFs got searched. No magic, no hallucination.

---

## Stack

```
React + Vite (frontend)
    │
    │  POST /chat  { message }
    ▼
FastAPI (backend, port 8000)
    │
    ├─► AI Service (Groq Llama 3.1 8B)
    │   └─► agentic tool loop (max 4 rounds)
    │       │
    │       ▼
    │   Tool Executor (allowlist, 9 tools)
    │       ├─► SQL Service ──► SQLite (6 tables, ~18k rows)
    │       └─► Document Service ──► TF-IDF over 5 PDFs
    │
    └─► /api/analytics/* (direct SQL for the dashboard charts)
```

**Why these choices:**

| Decision | Why |
|----------|-----|
| **Groq** as LLM provider | Free, fast (~1 sec responses), native function calling |
| **Llama 3.1 8B** model | Smaller than 3.3 70B but plenty for 9-tool dispatch; saves quota |
| **SQLite** | Zero setup, fits in the repo, fast enough for 18k rows |
| **Custom TF-IDF** instead of ChromaDB / embeddings | 5 PDFs, ~7 chunks. ML overhead wasn't worth it. Pure Python, no model downloads. |
| **React over Streamlit** | More control over UI; Streamlit was an option (see alternatives below) |
| **No auth** | Out of scope for a single-user demo |

---

## Run it

### Easiest way: Docker

```bash
git clone <this-repo> FF_Assignment
cd FF_Assignment
cp .env.example .env             # then add your Groq key
docker compose up --build
```

Visit:
- **http://localhost:5175** — the app
- **http://localhost:8000/docs** — Swagger / API docs

First build takes ~3 minutes. After that, `docker compose up` (no `--build`) is instant.

### Manual setup (if you don't want Docker)

You need Python 3.12 and Node 20+.

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # Mac/Linux

pip install -r requirements.txt

# Create .env with your Groq key
echo GROQ_API_KEY=gsk_xxx > .env

uvicorn app.main:app --reload
```

**Frontend** (new terminal):
```bash
cd frontend
npm install
npm run dev
```

Get a free Groq key at https://console.groq.com/keys (takes 30 seconds, no credit card).

---

## What's inside

```
FF_Assignment/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, rate limiter
│   │   ├── ai_service.py            # the LLM tool loop
│   │   ├── database.py              # SQLite + CSV loader
│   │   ├── routers/analytics.py     # /api/analytics/* (no AI, just SQL)
│   │   ├── services/
│   │   │   ├── sql_services.py      # 8 SQL query functions
│   │   │   └── document_service.py  # PDF parsing + TF-IDF
│   │   └── tools/execute.py         # Tool schemas + allowlist + dispatch
│   ├── data/
│   │   ├── csv/                     # 6 pre-generated CSVs (committed)
│   │   └── pdfs/                    # 5 internal PDFs (committed)
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # page router (Chat / Dashboard / History)
│   │   └── components/
│   │       ├── Sidebar.jsx
│   │       ├── Chat.jsx             # chat UI + tool trace dropdown
│   │       ├── Dashboard.jsx        # KPIs, charts, filters, insights
│   │       └── History.jsx          # past queries + delete buttons
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

The data files are committed so a reviewer doesn't have to run a generator. The script that
made them is in `backend/scripts/generate_data.py` if you're curious about the seeding
logic (Stellar Run is rigged to trend, comedy is rigged to underperform — so the example
questions land naturally).

---

## The 9 tools

This is the entire surface area the LLM can touch. Anything else, the executor rejects:

| Tool | What it does |
|------|--------------|
| `get_top_movies` | Top movies by revenue, optional year filter |
| `get_movie_details` | Full info on one movie (financials, ratings, watch stats) |
| `compare_movies` | Side-by-side compare with a "winner" verdict |
| `get_genre_trends` | Genre-level revenue, ratings, ROI |
| `get_regional_performance` | City-level views and engagement |
| `get_audience_insights` | Demographics (age / subscription / device / preference) |
| `get_trending_content` | Most-watched titles in recent window |
| `get_marketing_roi` | Campaign spend by channel and movie |
| `search_internal_documents` | TF-IDF over the 5 PDFs |

Adding a 10th would be ~5 lines: add the function to `sql_services.py`, register it in
`execute.py`'s TOOLS list and DISPATCH dict. Done.

---

## Security thinking

| Risk | What I did about it |
|------|---------------------|
| SQL injection | Every user-derived value goes through `?` parameters. No f-string concatenation of inputs. |
| AI doing something unapproved | Hard allowlist of 9 tool names. Anything else returns `{"error": "Unknown tool"}`. |
| Prompt injection that asks for raw SQL | Doesn't matter — there's no raw SQL tool exposed. |
| Quota abuse / runaway costs | Rate limiter: **30 chat requests / day / IP** (slowapi). |
| AI hallucinating answers from training data | System prompt forces tool use; `tool_choice="required"` on round 1; explicit "say I don't know" instruction. |
| Secrets in repo | `.env` in `.gitignore`. `.env.example` committed as a template. |
| CORS open to the world | Locked to `localhost:5175` only. |
| PII exposure | The AI never sees raw viewer rows — only aggregated counts and grouped queries. |

---

## Things I had to figure out the hard way

Honest list, because most of the time was spent on the boring stuff:

### 1. `google-generativeai` vs `google-genai`
Started with Gemini. Pip-installed `google-generativeai` (the deprecated one) and spent
30 minutes wondering why `from google import genai` didn't exist. The new package name is
`google-genai`. Uninstall, reinstall, move on.

### 2. uvicorn picking up the wrong Python
Activated my venv, installed packages, ran `uvicorn` — got `ModuleNotFoundError`. Turned
out Windows had a global `uvicorn.exe` ahead of my venv's in PATH, so the global Python
was running and didn't have the packages. Fix: `python -m uvicorn` to force the venv.

### 3. `.env` file with quotes
`GROQ_API_KEY="gsk_xxx"` got parsed with the quotes included as part of the value, and
Groq rejected the key. Removing the quotes fixed it. Also: PowerShell's `Out-File` writes
UTF-16 by default, which `python-dotenv` can fail to parse — had to use `-Encoding ascii`.

### 4. Hit Gemini's free quota mid-development
After ~50 test messages I started getting `429 RESOURCE_EXHAUSTED`. Switched to Groq
which has a much more generous free tier. Better function calling support too, in my
experience.

### 5. Llama returning numeric args as strings
Schema says `{"limit": "integer"}`, model returns `{"limit": "3"}`. Groq's server-side
validation rejected the call. Fix: change schema types to `"string"` and coerce with
`int()` inside each function. Defensive parsing > strict schemas — for LLM outputs at
least.

### 6. CORS preflight failures
Frontend was on port 5175 (Vite jumped from 5173 because something else had taken it).
CORS allowed 5173. Browser sent OPTIONS, server rejected, fetch failed silently with
"Failed to fetch". Always check Network tab before guessing. Fix: explicit ports in
`allow_origins`.

### 7. Groq library adding fields the API doesn't accept
The `groq` Python library puts an `annotations` field on assistant messages. When you
echo that message back into the next request, Groq's API rejects it. Had to manually
build the assistant message with only `role`, `content`, `tool_calls`.

### 8. AI hallucinating "Avatar grossed $2.92B"
Asked "highest grossing movie" and got real-world Hollywood facts instead of our 50-movie
catalogue. The model was pulling from training data when it had no tool result handy.
Fix: stronger system prompt + `tool_choice="required"` on the first round forces a tool
call before answering anything data-related.

### 9. The "null" response bug
Spent 10 minutes debugging why the chat endpoint returned `null`. The endpoint just
called `ai_chat(body.message)` without `return`. Python's implicit `None` return became
`null` in JSON. The lesson: always read your endpoint's first line aloud.

### 10. AI dumping raw JSON as the answer
Early on, when the AI got tool results back, it would just paste the raw JSON into the
response text instead of summarising. Fixed with a strict system prompt:
`"NEVER paste raw tool results, always summarise in 3-6 bullets max 200 words"`. Plus
truncating document chunks to 600 chars so the model has less to copy-paste from.

---

## Trade-offs I'm aware of

- **Single-user demo.** No auth. Anyone on `localhost` can hit the API.
- **In-memory query history.** Refresh the browser, it's gone. Real version would persist
  to Redis or another SQLite table.
- **TF-IDF over embeddings.** Works for 5 PDFs. Wouldn't scale to 500. The trade-off was
  zero ML dependencies vs slightly better fuzzy matching.
- **Llama 3.1 8B over 3.3 70B.** 8B is faster and cheaper but occasionally fumbles
  multi-tool reasoning. The 70B line is commented in `ai_service.py` if you want to
  swap.
- **Synthetic data is committed**, not generated on first run. Saves the reviewer 30
  seconds and avoids `fpdf2` dependency at runtime. Generator script is still in the
  repo for transparency.
- **`tool_choice="required"` on round 1** means even casual greetings might trigger a
  tool call. The alternative (`"auto"`) caused too much hallucination. Picked the
  trade-off that hurts UX less than wrong answers do.

---

## Alternative I considered: Streamlit

Honestly, Streamlit would've been faster to build. It's a Python framework that lets you
write the UI in the same language as your backend — no React, no CORS, no separate dev
servers, no `npm install`.

A Streamlit version of this would be roughly:

```python
# streamlit_app.py — entire frontend in one file
import streamlit as st
from app.ai_service import chat

st.title("AI Insights Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = chat(prompt)
            st.markdown(result["answer"])
            with st.expander(f"Tools used ({len(result['tool_calls'])})"):
                st.json(result["tool_calls"])
        st.session_state.messages.append({"role": "assistant", "content": result["answer"]})
```

Run with `streamlit run streamlit_app.py`. ~50 lines for chat + tool trace.

Charts would use `st.bar_chart`, `st.metric`, `st.dataframe` — all built in. No Recharts,
no axis configuration.

**Why I went React instead:**

- Wanted to show a separation between frontend and backend (proper API design)
- More control over the dark theme and the tool-trace dropdown UX
- Better grading signal for "frontend engineering" — Streamlit is one file
- I wanted to learn the React + tool-calling pattern, since that's industry standard

**When Streamlit is the right call:**

- You're prototyping fast and don't need a polished UI
- The audience is data scientists / internal users
- You want to ship in a day, not a week
- You'll deploy to Streamlit Cloud (one-click)

If I were doing this again under time pressure, Streamlit would be a serious option.
The architecture (FastAPI + tools + SQLite + PDF search) would be **identical** —
only the UI layer changes.

---

## Future improvements

- Persistent query history (Redis or a SQLite log table)
- User auth + per-user rate limits
- WebSocket streaming so token output appears live instead of after the full response
- Server-side audit log of every tool call (CSV or structured logs)
- Vector embeddings for the document search if the PDF count grows past ~20
- Cost tracking dashboard (Groq tokens used per session)

---

## Submission checklist

- [x] Working backend
- [x] Working frontend
- [x] Multi-source answers (SQL + PDFs combined in single response)
- [x] Charts (4 of them on the Dashboard)
- [x] Filters / selectors (year + audience segment)
- [x] Insights panel (auto-generated bullets)
- [x] Tool trace (dropdown under each AI message)
- [x] Query history (with per-item and clear-all delete)
- [x] All 6 example questions tested
- [x] Rate limiting (30/day/IP)
- [x] Pydantic validation
- [x] Parameterised SQL
- [x] Docker setup, tested
- [x] README + architecture diagram
- [x] Trade-offs documented
- [x] Pushed to GitHub

That's it. Hope you enjoy poking at it.
