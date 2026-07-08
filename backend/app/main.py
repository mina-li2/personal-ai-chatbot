"""
main.py — the FastAPI app. This is the entry point.
"""
import os
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.db import init_db, save_chat_message, delete_old_chat_history
from app.rag import answer_question

app = FastAPI(title="Personal AI Chatbot")

# How long to keep chat messages before auto-deleting them, and how often
# to check. Configurable via env vars if you ever want to change them
# without touching code.
CHAT_HISTORY_RETENTION_DAYS = int(os.environ.get("CHAT_HISTORY_RETENTION_DAYS", "30"))
CLEANUP_INTERVAL_SECONDS = 24 * 60 * 60  # once a day

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def periodic_cleanup():
    """Runs forever in the background, deleting old chat_history rows
    once a day so the database doesn't grow unbounded once this is
    public and strangers are chatting with it."""
    while True:
        try:
            deleted = delete_old_chat_history(CHAT_HISTORY_RETENTION_DAYS)
            print(f"[cleanup] Deleted {deleted} chat_history row(s) older than {CHAT_HISTORY_RETENTION_DAYS} days.")
        except Exception as e:
            print(f"[cleanup] Failed: {e}")
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)


@app.on_event("startup")
async def startup():
    init_db()
    asyncio.create_task(periodic_cleanup())


class ChatRequest(BaseModel):
    # max_length caps how long a single question can be, so nobody can
    # send a giant wall of text and burn through Groq's free tier in one
    # request.
    message: str = Field(min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
def chat(request: Request, req: ChatRequest):
    save_chat_message("user", req.message)
    result = answer_question(req.message)
    save_chat_message("assistant", result["answer"])
    return result