# Personal AI Chatbot

A retrieval-augmented chatbot that answers questions using my own project
history, resume, and background as its knowledge base — built to
demonstrate a full RAG pipeline end to end: embeddings, vector search,
LLM generation, and containerized deployment.

## Architecture

```
User → FastAPI /chat → embed question (sentence-transformers)
                     → similarity search in Postgres (pgvector)
                     → build context from top matches
                     → LLM (Groq or local Ollama) generates answer
                     → response + sources returned to user
```

**Why these choices:**
- **pgvector**: keeps structured data and vector search in one database
  instead of running a separate vector DB — simpler ops story.
- **Local embeddings (sentence-transformers)**: no per-request API cost
  or external dependency for the retrieval step.
- **Groq for generation (default)**: free, no credit card, fast — good
  default for a portfolio project. Swappable to a fully local model via
  Ollama by changing one env var, with no other code changes needed.

## Stack
FastAPI · PostgreSQL + pgvector · sentence-transformers · Groq API
(or local Ollama) · Docker Compose

## Running locally

1. Copy the env file:
   ```
   cp backend/.env.example backend/.env
   ```

2. Choose your LLM backend in `backend/.env`:

   **Option A — Groq (default, recommended, needs internet):**
   - Get a free key at https://console.groq.com (no credit card)
   - Set `GROQ_API_KEY` in `.env`
   - Leave `LLM_PROVIDER=groq`

   **Option B — Ollama (fully local, no internet, no API key):**
   - Install Ollama: https://ollama.com
   - Pull a model: `ollama pull llama3.1`
   - Make sure Ollama is running (`ollama serve` or the desktop app)
   - Set `LLM_PROVIDER=ollama` in `.env`

3. Start everything:
   ```
   docker compose up --build
   ```

4. Load the knowledge base (run once, and again whenever you edit
   `backend/data/about_me.example.md`):
   Copy the example to get started:
    cp backend/data/about_me.example.md backend/data/about_me.md
   Then edit it with your own background before running `load_docs.py`. 
   ```
   docker compose exec backend python scripts/load_docs.py
   ```

5. Ask it something:
   ```
   curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "What projects has User built?"}'
   ```

## Roadmap
- [ ] Web chat UI (React)
- [ ] Agent tool: live GitHub API lookup of latest repos
- [ ] Deploy to a cloud VM / Kubernetes
