"""Deterministic physical-page extraction, preserving unmodified PDF snapshots."""
import hashlib
import json
from pathlib import Path

from pypdf import PdfReader


def extract_document(metadata_path: Path) -> tuple[dict, list[dict]]:
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    pdf = metadata_path.parent / metadata["filename"]
    if hashlib.sha256(pdf.read_bytes()).hexdigest() != metadata["sha256"]:
        raise ValueError("Official snapshot hash mismatch")
    reader = PdfReader(pdf)
    pages = [dict(page=i + 1, text=page.extract_text(extraction_mode="plain") or "")
             for i, page in enumerate(reader.pages)]
    return metadata, pages


def main():
    output = Path("docs/evidence/phase_d/extraction")
    output.mkdir(parents=True, exist_ok=True)
    summaries = []
    for name in ("mewa_strategy", "gastat_methodology"):
        metadata, pages = extract_document(Path("rag/sources") / f"{name}.json")
        (output / f"{name}_pages.json").write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
        nonempty = [p for p in pages if p["text"].strip()]
        summary = dict(**metadata, total_pages=len(pages), nonempty_pages=len(nonempty),
                       total_characters=sum(len(p["text"]) for p in pages),
                       samples=[dict(page=p["page"], text=p["text"][:1800]) for p in nonempty[:5]])
        summaries.append(summary)
        print(json.dumps(summary, ensure_ascii=True), flush=True)
    (output / "summary.json").write_text(json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8")
    # Quantities alone do not establish readable extraction: review samples too.
    if any(s["total_characters"] < 1000 or s["nonempty_pages"] == 0 for s in summaries):
        raise RuntimeError("PDF extraction viability failed; stop before RAG")


if __name__ == "__main__":
    main()
