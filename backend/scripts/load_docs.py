"""
scripts/load_docs.py — reads every .md file in backend/data/, splits it
into chunks, embeds each chunk, and inserts it into the `documents`
table.

Run this once (and again any time you update your docs) with:
    docker compose exec backend python scripts/load_docs.py
"""
import glob
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import init_db, insert_documents, clear_documents
from app.embeddings import embed_text

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Simple word-count-based chunking with a bit of overlap so we don't
    cut a sentence's meaning in half between chunks."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start = end - overlap
    return chunks


def main():
    init_db()
    clear_documents()

    md_files = glob.glob(os.path.join(DATA_DIR, "*.md"))
    if not md_files:
        print(f"No .md files found in {DATA_DIR}. Add some and re-run.")
        return

    rows = []
    for filepath in md_files:
        source = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        for chunk in chunk_text(text):
            embedding = embed_text(chunk)
            rows.append((source, chunk, embedding))
        print(f"Chunked {source} into {len(chunk_text(text))} piece(s).")

    insert_documents(rows)
    print(f"Inserted {len(rows)} chunks into the documents table.")


if __name__ == "__main__":
    main()
