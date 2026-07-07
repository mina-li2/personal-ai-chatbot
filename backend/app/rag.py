"""
rag.py — the RAG + agent pipeline.

Flow:
  1. Embed the user's question
  2. Find the most similar chunks in `documents` (pgvector search)
  3. Stuff those chunks into the prompt as context
  4. Ask an LLM to answer — and give it a TOOL it can choose to call if
     the static context isn't enough (e.g. "what's she working on lately")

This tool-calling step is what makes it "agentic" rather than plain RAG:
the model itself decides whether it needs live data before answering.

LLM_PROVIDER controls which backend generates the answer:
  - "groq"   (default) — free hosted API, supports tool calling, needs
             GROQ_API_KEY and internet
  - "ollama" — fully local, no API key/internet needed, but this simple
             version does NOT use tool calling on the Ollama path (kept
             simple on purpose — see README for why)
"""
import os
import json
import requests
from groq import Groq
from app.db import search_similar_documents
from app.embeddings import embed_text
from app.tools import get_latest_repos

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "groq").lower()

GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")

SYSTEM_PROMPT = """You are a personal AI assistant representing Minali.
Answer questions about her using the context provided below. If asked
about her latest, current, or recent projects/work, use the
get_latest_repos tool to check GitHub for up-to-date info instead of
relying only on the static context, which may be outdated. If neither
the context nor the tool has the answer, say you don't have that
information rather than making something up. Speak in first person, as
if you are Minali's assistant introducing her work."""

# Tool schema in OpenAI-compatible function-calling format (Groq uses
# the same format). This is how we describe to the model what the tool
# does and when it might want to use it.
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_latest_repos",
            "description": (
                "Fetch Minali's most recently updated public GitHub "
                "repositories, with descriptions and last-updated dates. "
                "Use this whenever asked about her latest, current, or "
                "recent projects, since the static knowledge base can "
                "go stale."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "How many repos to fetch. Defaults to 5.",
                    }
                },
                "required": [],
            },
        },
    }
]

AVAILABLE_TOOLS = {"get_latest_repos": get_latest_repos}

_groq_client = None


def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _groq_client


def _call_groq(user_message: str) -> str:
    client = _get_groq_client()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    # First call: give the model the option to use a tool.
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=500,
        messages=messages,
        tools=TOOLS_SCHEMA,
    )
    reply = response.choices[0].message

    # If the model didn't ask for a tool, we're done — just return its answer.
    if not reply.tool_calls:
        return reply.content

    # The model wants to call one or more tools. Run them and feed the
    # real results back in, then ask it to write the final answer.
    messages.append(
        {
            "role": "assistant",
            "content": reply.content,
            "tool_calls": [tc.model_dump() for tc in reply.tool_calls],
        }
    )

    for tool_call in reply.tool_calls:
        fn_name = tool_call.function.name
        fn_args = json.loads(tool_call.function.arguments or "{}")
        fn = AVAILABLE_TOOLS.get(fn_name)
        result = fn(**fn_args) if fn else f"Unknown tool: {fn_name}"

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            }
        )

    followup = client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=500,
        messages=messages,
    )
    return followup.choices[0].message.content


def _call_ollama(user_message: str) -> str:
    # Kept simple on purpose: no tool calling here, just context-based
    # answers. Ollama tool calling is possible with newer models but
    # adds real complexity — documented as a known limitation.
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


def answer_question(question: str) -> dict:
    query_embedding = embed_text(question)
    chunks = search_similar_documents(query_embedding, top_k=4)

    context_text = "\n\n---\n\n".join(
        f"[Source: {c['source']}]\n{c['content']}" for c in chunks
    )

    user_message = f"""Context:\n{context_text}\n\nQuestion: {question}"""

    if LLM_PROVIDER == "ollama":
        answer_text = _call_ollama(user_message)
    else:
        answer_text = _call_groq(user_message)

    return {
        "answer": answer_text,
        "sources": [c["source"] for c in chunks],
    }