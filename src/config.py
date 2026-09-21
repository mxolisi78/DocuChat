"""
Central configuration for DocuChat.
Reads from .env at the project root.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Project root = parent of src/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env from project root
load_dotenv(PROJECT_ROOT / ".env")


def get(key: str, default=None):
    return os.getenv(key, default)


# === Paths ===
UPLOAD_DIR = PROJECT_ROOT / get("UPLOAD_DIR", "data/uploads")
CHROMA_DIR = PROJECT_ROOT / get("CHROMA_DIR", "data/chroma_db")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# === LLM ===
LLM_PROVIDER = get("LLM_PROVIDER", "groq")
GROQ_API_KEY = get("GROQ_API_KEY")
LLM_MODEL    = get("LLM_MODEL", "openai/gpt-oss-120b")
OLLAMA_BASE_URL = get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = get("OLLAMA_MODEL", "llama3.2")

# === Embeddings ===
EMBED_MODEL = get("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# === Chunking ===
CHUNK_SIZE    = int(get("CHUNK_SIZE", 500))
CHUNK_OVERLAP = int(get("CHUNK_OVERLAP", 50))

# === Retrieval ===
TOP_K = int(get("TOP_K", 4))

# === ChromaDB ===
COLLECTION_NAME = "docuchat_documents"