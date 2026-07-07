"""
main.py — the FastAPI app. This is the entry point.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from app.db import init_db, save_chat_message
from app.rag import answer_question

app = FastAPI(title="Personal AI Chatbot")


@app.on_event("startup")
def startup():
    init_db()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    save_chat_message("user", req.message)
    result = answer_question(req.message)
    save_chat_message("assistant", result["answer"])
    return result
