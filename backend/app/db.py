"""
db.py — everything related to talking to Postgres.

We use raw psycopg2 (not an ORM) on purpose: it keeps things simple and
transparent for a portfolio project, and it's easy to explain in an
interview ("here's exactly what SQL is running").
"""
import os
import psycopg2
from psycopg2.extras import execute_values

DATABASE_URL = os.environ["DATABASE_URL"]

# The embedding model we use (in embeddings.py) outputs 384-dim vectors.
# This MUST match EMBEDDING_DIM in embeddings.py.
EMBEDDING_DIM = 384


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    """Creates the pgvector extension and our tables if they don't exist yet.
    Safe to call every time the app starts."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            source TEXT NOT NULL,
            content TEXT NOT NULL,
            embedding VECTOR({EMBEDDING_DIM}) NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id SERIAL PRIMARY KEY,
            role TEXT NOT NULL,          -- 'user' or 'assistant'
            content TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)

    conn.commit()
    cur.close()
    conn.close()


def insert_documents(rows):
    """rows: list of (source, content, embedding_list) tuples."""
    conn = get_connection()
    cur = conn.cursor()
    execute_values(
        cur,
        "INSERT INTO documents (source, content, embedding) VALUES %s",
        rows,
        template="(%s, %s, %s::vector)",
    )
    conn.commit()
    cur.close()
    conn.close()

def clear_documents():
    """Deletes all rows from documents. Called before reloading so that
    editing a .md file and rerunning load_docs.py doesn't leave stale
    duplicate chunks behind."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM documents;")
    conn.commit()
    cur.close()
    conn.close()

def search_similar_documents(query_embedding, top_k=4):
    """Returns the top_k most similar document chunks using cosine distance.
    pgvector's <=> operator computes cosine distance directly in SQL —
    this is the core of RAG's "retrieval" step."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT source, content, embedding <=> %s::vector AS distance
        FROM documents
        ORDER BY distance ASC
        LIMIT %s;
        """,
        (query_embedding, top_k),
    )
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [{"source": r[0], "content": r[1], "distance": r[2]} for r in results]


def save_chat_message(role, content):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO chat_history (role, content) VALUES (%s, %s);",
        (role, content),
    )
    conn.commit()
    cur.close()
    conn.close()
