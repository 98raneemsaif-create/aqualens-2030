"""Page-bound, deterministic chunks from the two immutable official PDFs."""
import hashlib
import re
import unicodedata
from pathlib import Path

import pymupdf

from src.rag.extraction import extract_document


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text).replace("ـ", "")).strip()


def narrative_runs(text: str):
    """Keep contiguous prose only; excluded lines never get stitched together."""
    run = []
    start = 1
    for number, line in enumerate(text.splitlines(), 1):
        clean = normalize(line)
        acceptable = (not any(c.isdigit() for c in clean) and "�" not in clean
                      and "?" not in clean and sum(c.isalpha() for c in clean) >= 15
                      and not re.search(r"[A-Za-z]", clean))
        if acceptable:
            if not run:
                start = number
            run.append(clean)
        else:
            if run:
                yield start, number - 1, " ".join(run)
                run = []
    if run:
        yield start, len(text.splitlines()), " ".join(run)


def split_text(text: str, size: int = 800, overlap: int = 120):
    if not 0 <= overlap < size:
        raise ValueError("Require 0 <= overlap < size")
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start + size // 2, end)
            if boundary > start:
                end = boundary
        yield start, text[start:end]
        if end == len(text):
            break
        start = end - overlap


def make_chunks() -> tuple[list[dict], list[dict]]:
    chunks, summaries = [], []
    for name in ("mewa_strategy", "gastat_methodology"):
        import json
        path = Path("rag/sources") / f"{name}.json"
        if name == "mewa_strategy":
            meta = json.loads(path.read_text())
            pdf = path.parent / meta["filename"]
            assert hashlib.sha256(pdf.read_bytes()).hexdigest() == meta["sha256"]
            with pymupdf.open(pdf) as document:
                pages = [dict(page=i+1, text=p.get_text("text")) for i,p in enumerate(document)]
            method = "PyMuPDF-1.28.2/text-unsorted/narrative-only"
        else:
            meta, pages = extract_document(path)
            method = "pypdf-6.17.0/plain"
        before = len(chunks)
        for page in pages:
            runs = list(narrative_runs(page["text"])) if name == "mewa_strategy" else [(1, len(page["text"].splitlines()), normalize(page["text"]))]
            for first, last, text in runs:
                if len(text) < 100:
                    continue
                for offset, passage in split_text(text):
                    identity = f"{meta['sha256']}:{method}:{page['page']}:{first}:{last}:{offset}:{passage}"
                    chunk_id = hashlib.sha256(identity.encode()).hexdigest()
                    chunks.append(dict(chunk_id=chunk_id, text=passage, metadata=dict(
                        title=meta["title"], organization=meta["organization"], page=page["page"],
                        canonical_url=meta["canonical_url"], language=meta["language"],
                        source_sha256=meta["sha256"], source_id=name, extraction_method=method,
                        first_line=first, last_line=last, run_offset=offset)))
        summaries.append(dict(source_id=name, total_pages=len(pages), nonempty_pages=sum(bool(p['text'].strip()) for p in pages),
                              chunks=len(chunks)-before, method=method))
    return chunks, summaries
