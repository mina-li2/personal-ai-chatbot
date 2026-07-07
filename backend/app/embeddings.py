"""
embeddings.py — turns text into vectors so we can do similarity search.

We use a small local model (all-MiniLM-L6-v2). It's fast, free, runs on
CPU, and produces 384-dimensional vectors — good enough for a personal
knowledge base of a few dozen documents.
"""
from sentence_transformers import SentenceTransformer

EMBEDDING_DIM = 384  # must match db.py

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_text(text: str) -> list[float]:
    model = get_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()
