from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.database import init_db, get_connection
from app.ai_service import chat as ai_chat
from app.services.document_service import ingest_pdfs
from app.routers.analytics import router as analytics_router


@asynccontextmanager
async def lifespan(app):
    init_db()
    ingest_pdfs()
    yield


class ChatReq(BaseModel):
    message: str


# ─── Rate limiter (30 requests / day, keyed by client IP) ─────────────────────
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5175", "http://127.0.0.1:5175"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    expose_headers=["*"],
)


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/movies")
def list_movies():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM movies LIMIT 10").fetchall()
    return [dict(r) for r in rows]


@app.post("/chat")
@limiter.limit("30/day")
def chat_endpoint(request: Request, body: ChatReq):
    return ai_chat(body.message)


app.include_router(analytics_router, prefix="/api")
