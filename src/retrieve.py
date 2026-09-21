"""
Semantic retrieval over the ChromaDB collection.
"""
from typing import List, Dict

from src.embed_store import get_embedder, get_collection
from src.config import TOP_K


def semantic_search(query: str, top_k: int = None) -> List[Dict]:
    """
    Return the top_k most similar chunks for a given query.

    Each result:
      { "text": str, "source": str, "chunk_id": int, "score": float }
    Higher score = more similar (cosine similarity in [0, 1]).
    """
    if top_k is None:
        top_k = TOP_K

    embedder = get_embedder()
    collection = get_collection()

    if collection.count() == 0:
        return []

    query_vec = embedder.encode(
        [query],
        normalize_embeddings=True,
    ).tolist()

    results = collection.query(
        query_embeddings=query_vec,
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        # Chroma returns cosine *distance* → similarity = 1 - distance
        hits.append({
            "text": doc,
            "source": meta.get("source", "unknown"),
            "chunk_id": meta.get("chunk_id"),
            "score": round(1.0 - dist, 4),
        })
    return hits