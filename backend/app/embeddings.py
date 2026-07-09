"""
embeddings.py — turns text into vectors so we can do similarity search.

We use Cohere's Embed API (free trial tier, no credit card, stable and
widely used for RAG specifically). We switched here from Google's Gemini
embeddings after hitting Google's in-progress API key format migration,
which was breaking for many developers, not just us.

Cohere distinguishes between embedding a document (something to be
searched) and embedding a query (the search itself) via input_type —
using the right one improves retrieval quality slightly.
"""
import os
import cohere

EMBEDDING_DIM = 1024  # must match db.py — Cohere's embed-english-v3.0 output size

co = cohere.Client(os.environ["COHERE_API_KEY"])


def embed_text(text: str, input_type: str = "search_document") -> list[float]:
    response = co.embed(
        texts=[text],
        model="embed-english-v3.0",
        input_type=input_type,
    )
    return response.embeddings[0]