"""Compare actual PyMuPDF extraction modes without repairing Arabic text."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pymupdf

ROOT = Path("docs/evidence/phase_d/pymupdf")
SAMPLES = [6, 14, 15, 16, 17, 30, 50, 70, 90, 110, 124]


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    for name in ("mewa_strategy", "gastat_methodology"):
        meta = json.loads(Path(f"rag/sources/{name}.json").read_text())
        assert hashlib.sha256(Path(f"rag/sources/{name}.pdf").read_bytes()).hexdigest() == meta["sha256"]
    pdf = Path("rag/sources/mewa_strategy.pdf")
    document = pymupdf.open(pdf)
    summaries = []
    for mode in ("text", "sorted", "layout"):
        pages = []
        errors = []
        existing = ROOT / f"{mode}_pages.json"
        if existing.exists():
            pages = json.loads(existing.read_text(encoding="utf-8"))
        for index, page in enumerate(document):
            if existing.exists():
                break
            if mode == "layout":
                output = ROOT / "layout_page.txt"
                result = subprocess.run([sys.executable, "-m", "pymupdf", "gettext", str(pdf),
                                "-mode", "layout", "-pages", str(index + 1),
                                "-output", str(output)], capture_output=True, text=True)
                if result.returncode:
                    errors.append(dict(page=index + 1, exit_code=result.returncode, stderr=result.stderr))
                    text = ""
                else:
                    text = output.read_text(encoding="utf-8")
                output.unlink(missing_ok=True)
            else:
                text = page.get_text("text", sort=(mode == "sorted"))
            pages.append(dict(page=index + 1, text=text))
        if not existing.exists():
            existing.write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
        summary = dict(mode=mode, total_pages=len(pages), nonempty_pages=sum(bool(p["text"].strip()) for p in pages),
                       characters=sum(len(p["text"]) for p in pages),
                       errors=errors, samples=[dict(page=n, text=pages[n-1]["text"][:2500]) for n in SAMPLES])
        summaries.append(summary)
        print(json.dumps({k:v for k,v in summary.items() if k != "samples"}), flush=True)
    (ROOT / "summary.json").write_text(json.dumps(dict(pymupdf=pymupdf.VersionBind,
        source_hash_verified=True, modes=summaries), ensure_ascii=False, indent=2), encoding="utf-8")
    print("Extraction complete; manual narrative readability gate still required.", flush=True)


if __name__ == "__main__":
    main()
