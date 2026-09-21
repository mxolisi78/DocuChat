"""
Embedding + ChromaDB storage layer.
"""
from pathlib import Path
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from src.config import (
    CHROMA_DIR,
    EMBED_MODEL,
    COLLECTION_NAME,
)


# Lazy-loaded singletons (avoid loading model on import)
_embedder = None
_client = None
_collection = None


def get_embedder() -> SentenceTransformer:
    """Load the embedding model once and cache it."""
    global _embedder
    if _embedder is None:
        print(f"Loading embedding model: {EMBED_MODEL} (first time only)...")
        _embedder = SentenceTransformer(EMBED_MODEL)
    return _embedder


def get_client():
    """Persistent ChromaDB client rooted at CHROMA_DIR."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _client


def get_collection():
    """Get or create the main collection."""
    global _collection
    if _collection is None:
        _collection = get_client().get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},   # cosine similarity
        )
    return _collection


def add_chunks(chunks: List[Dict]) -> int:
    """
    Embed a list of chunk dicts and store them.
    Each dict must have: 'text', 'source', 'chunk_id'.

    Returns number of chunks added.
    """
    if not chunks:
        return 0

    embedder = get_embedder()
    collection = get_collection()

    texts = [c["text"] for c in chunks]
    embeddings = embedder.encode(
        texts,
        normalize_embeddings=True,   # unit vectors → cosine = dot product
        show_progress_bar=False,
        batch_size=32,
    ).tolist()

    # Chroma requires string IDs
    ids = [f"{c['source']}::{c['chunk_id']}" for c in chunks]
    metadatas = [
        {"source": c["source"], "chunk_id": c["chunk_id"]}
        for c in chunks
    ]

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return len(chunks)


def count() -> int:
    """How many chunks are in the collection."""
    return get_collection().count()


def reset_collection():
    """Delete everything and start fresh."""
    client = get_client()
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass
    global _collection
    _collection = None
    return get_collection()


def list_sources() -> List[str]:
    """Return unique source filenames currently in the collection."""
    collection = get_collection()
    data = collection.get(include=["metadatas"])
    sources = {m["source"] for m in data["metadatas"] if m}
    return sorted(sources)