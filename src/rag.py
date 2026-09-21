"""
RAG answer generation.
Uses Groq (cloud) or Ollama (local), configurable via .env.
"""
from typing import List, Dict, Optional

from src.config import (
    LLM_PROVIDER, GROQ_API_KEY, LLM_MODEL,
    OLLAMA_BASE_URL, OLLAMA_MODEL,
)
from src.retrieve import semantic_search


SYSTEM_PROMPT = """You are DocuChat, a helpful assistant that answers questions strictly based on the provided document excerpts.

Rules:
1. Answer ONLY using the information in the CONTEXT below.
2. If the context does not contain the answer, say: "I couldn't find that in the uploaded documents."
3. Cite the source filenames you used, like: [source: filename.pdf]
4. Be concise. Do not speculate or bring in outside knowledge.
"""


def build_context(hits: List[Dict]) -> str:
    """Format retrieved chunks into a context block."""
    if not hits:
        return "(no relevant context found)"
    blocks = []
    for i, h in enumerate(hits, 1):
        blocks.append(
            f"[{i}] source: {h['source']} (chunk {h['chunk_id']}, score {h['score']})\n"
            f"{h['text']}"
        )
    return "\n\n---\n\n".join(blocks)


def _call_groq(prompt: str, system: str) -> str:
    from groq import Groq
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set in .env")

    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=600,
    )
    return response.choices[0].message.content.strip()


def _call_ollama(prompt: str, system: str) -> str:
    import ollama
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        options={"temperature": 0.2},
    )
    return response["message"]["content"].strip()


def ask(question: str, top_k: Optional[int] = None) -> Dict:
    """
    Full RAG pipeline: retrieve → build prompt → call LLM → return answer + sources.
    """
    hits = semantic_search(question, top_k=top_k)
    context = build_context(hits)

    user_prompt = (
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {question}\n\n"
        f"Answer using only the context. Include [source: filename] citations."
    )

    if LLM_PROVIDER == "ollama":
        answer = _call_ollama(user_prompt, SYSTEM_PROMPT)
    else:
        answer = _call_groq(user_prompt, SYSTEM_PROMPT)

    return {
        "question": question,
        "answer": answer,
        "sources": hits,
    }