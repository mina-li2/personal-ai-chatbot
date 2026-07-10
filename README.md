# Personal AI Chatbot

A retrieval-augmented, tool-using chatbot that answers questions about me using my own project history and resume as its knowledge base — built to demonstrate a full RAG + agentic AI pipeline end to end: embeddings, vector search, tool-calling, LLM generation, and cloud deployment.

**Live demo:** https://ask-about-minali.onrender.com
*(Free-tier hosting spins down after inactivity — the first message may take up to a minute to respond while it wakes up.)*

## Architecture

User → React chat UI → FastAPI /chat → embed question (Cohere)
                                     → similarity search in Postgres (pgvector)
                                     → build context from top matches
                                     → LLM (Groq) generates answer,
                                       optionally calling a tool to check
                                       GitHub for latest projects live
                                     → response returned to user

**Why these choices:**
- **pgvector** — keeps structured data and vector search in one database instead of running a separate vector DB.
- **Cohere for embeddings** — hosted, so no local model loaded into memory.
- **Groq for generation** — fast, and supports tool calling; the model decides for itself when it needs to check GitHub for live data versus answering from static context.
- **Neon + Render** — fully free deployment split: Neon for a permanent (non-expiring) Postgres database, Render for the backend API and frontend static site.

## Stack
FastAPI · React (Vite) · PostgreSQL + pgvector · Cohere Embed · Groq (Llama 3.3) · Docker · Neon · Render

## Features
- RAG-grounded answers from a real knowledge base, not hallucinated
- Agentic tool use: live GitHub API lookup for "what's she working on lately"
- Rate limiting (10 req/min/IP) and message length caps to protect free-tier API usage
- Automatic chat history cleanup (deletes messages older than 30 days)

## Running locally

1. Copy the env file:
   cp backend/.env.example backend/.env

2. Fill in backend/.env:
   - GROQ_API_KEY — free at https://console.groq.com
   - COHERE_API_KEY — free at https://dashboard.cohere.com
   - GITHUB_USERNAME — your GitHub username, for the live-repo tool

3. Start everything:
   docker compose up --build

4. Copy the example to get started: 
      cp backend/data/about_me.example.md backend/data/about_me.md 
   
5. Then edit it with your own background before running load_docs.py:
      docker compose exec backend python scripts/load_docs.py

5. Open the chat UI at http://localhost:5173