"""
Document loading and chunking.
Supports: .pdf, .docx, .txt, .md
"""
from pathlib import Path
from typing import List, Dict
import pypdf
import docx


SUPPORTED_EXTS = {".pdf", ".docx", ".txt", ".md"}


def load_text(path: Path) -> str:
    ext = path.suffix.lower()

    if ext == ".pdf":
        reader = pypdf.PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)

    if ext == ".docx":
        doc = docx.Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)

    if ext in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")

    raise ValueError(f"Unsupported file type: {ext}")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    text = text.strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    buffer = ""

    for para in paragraphs:
        if len(buffer) + len(para) + 2 <= chunk_size:
            buffer = f"{buffer}\n\n{para}".strip()
        else:
            if buffer:
                chunks.append(buffer)
            if len(para) > chunk_size:
                start = 0
                while start < len(para):
                    end = start + chunk_size
                    chunks.append(para[start:end])
                    start = end - overlap
            else:
                buffer = para

    if buffer:
        chunks.append(buffer)

    return chunks


def ingest_file(path: Path) -> List[Dict]:
    from src.config import CHUNK_SIZE, CHUNK_OVERLAP
    text = load_text(path)
    chunks = chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
    return [
        {"text": c, "source": path.name, "chunk_id": i}
        for i, c in enumerate(chunks)
    ]
