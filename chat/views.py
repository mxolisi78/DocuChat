"""
DocuChat views:
  - home       : renders the main UI
  - upload     : accepts a file, ingests + embeds it
  - ask        : answers a question via RAG
  - reset      : clears the vector store
"""
import json
from pathlib import Path

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

# Add project root to path so we can import src/
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import UPLOAD_DIR, TOP_K
from src.ingest import ingest_file
from src.embed_store import add_chunks, count, list_sources, reset_collection
from src.rag import ask as rag_ask


# ---------- views ----------

def home(request):
    """Main page — shows upload form, indexed sources, chat input."""
    return render(request, "chat/home.html", {
        "sources": list_sources(),
        "chunk_count": count(),
        "top_k": TOP_K,
    })


@require_POST
def upload(request):
    """Handle file upload → ingest → embed → store."""
    file = request.FILES.get("document")
    if not file:
        return JsonResponse({"ok": False, "error": "No file provided."}, status=400)

    # Save file to data/uploads/
    dest = UPLOAD_DIR / file.name
    with open(dest, "wb") as f:
        for chunk in file.chunks():
            f.write(chunk)

    # Skip re-index if this file is already in the collection
    from src.embed_store import list_sources
    if file.name in list_sources():
        return JsonResponse({
            "ok": False,
            "error": f'"{file.name}" is already indexed. Click "Clear all" first if you want to re-upload.',
        }, status=409)

    # Ingest + embed
    try:
        chunks = ingest_file(dest)
        n = add_chunks(chunks)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

    return JsonResponse({
        "ok": True,
        "filename": file.name,
        "chunks_added": n,
        "total_chunks": count(),
        "sources": list_sources(),
    })


@require_POST
def ask_view(request):
    """Handle a question → RAG → return answer + sources."""
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON."}, status=400)

    question = (data.get("question") or "").strip()
    if not question:
        return JsonResponse({"ok": False, "error": "Empty question."}, status=400)

    if count() == 0:
        return JsonResponse({
            "ok": False,
            "error": "No documents indexed yet. Upload a file first.",
        }, status=400)

    try:
        result = rag_ask(question)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

    return JsonResponse({
        "ok": True,
        "answer": result["answer"],
        "sources": result["sources"],
    })


@require_POST
def reset(request):
    """Clear the vector store (does not delete uploaded files)."""
    reset_collection()
    return JsonResponse({
        "ok": True,
        "total_chunks": count(),
        "sources": list_sources(),
    })