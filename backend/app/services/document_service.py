"""
Document Service — PDF ingestion + keyword search via TF-IDF.
No ML models required. Index is rebuilt in memory at startup.
"""

import re
import math
from collections import defaultdict
from pathlib import Path
from pypdf import PdfReader

# In-memory state
_corpus: list[dict] = []   # list of {text, source, tokens}
_idf: dict[str, float] = {}
_ingested = False


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z]{2,}", text.lower())


def _extract_chunks(pdf_path: Path, chunk_size: int = 400, overlap: int = 80) -> list[str]:
    """Read a PDF and return ~400-word chunks with overlap."""
    try:
        reader = PdfReader(str(pdf_path))
        text = " ".join(p.extract_text() or "" for p in reader.pages)
        text = re.sub(r"\s+", " ", text).strip()
    except Exception:
        return []

    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        chunk = " ".join(words[start:start + chunk_size])
        if len(chunk) > 40:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def ingest_pdfs(pdf_dir: str = "data/pdfs") -> dict:
    """Parse all PDFs in pdf_dir and build TF-IDF index. Run once at startup."""
    global _corpus, _idf, _ingested

    _corpus = []
    pdf_path = Path(pdf_dir)
    if not pdf_path.exists():
        return {"error": f"PDF directory not found: {pdf_dir}", "chunks": 0}

    for pdf_file in sorted(pdf_path.glob("*.pdf")):
        for chunk in _extract_chunks(pdf_file):
            _corpus.append({
                "text": chunk,
                "source": pdf_file.stem.replace("_", " ").title(),
                "tokens": _tokenize(chunk),
            })

    # Inverse Document Frequency: rare words score higher
    N = len(_corpus)
    df: dict[str, int] = defaultdict(int)
    for doc in _corpus:
        for term in set(doc["tokens"]):
            df[term] += 1
    _idf = {term: math.log((N + 1) / (count + 1)) + 1 for term, count in df.items()}

    _ingested = True
    print(f"[document_service] Ingested {N} chunks from {pdf_dir}")
    return {"chunks": N}


def search_documents(query: str, n_results: int = 5) -> dict:
    """Search PDFs by relevance. Returns top-n matching chunks with source + score."""
    global _ingested

    if not _ingested:
        ingest_pdfs()

    q_tokens = _tokenize(query)
    if not q_tokens or not _corpus:
        return {"results": []}

    def score(doc_tokens: list[str]) -> float:
        return sum(
            (doc_tokens.count(t) / max(len(doc_tokens), 1)) * _idf.get(t, 0)
            for t in q_tokens
        )

    scored = [(c, score(c["tokens"])) for c in _corpus]
    scored.sort(key=lambda x: x[1], reverse=True)

    n = max(1, min(int(n_results or 3), 5))
    return {
        "results": [
            {
                # Truncate text so the LLM can summarise instead of regurgitating
                "text": c["text"][:600] + ("…" if len(c["text"]) > 600 else ""),
                "source": c["source"],
                "score": round(s, 3),
            }
            for c, s in scored[:n] if s > 0
        ]
    }
