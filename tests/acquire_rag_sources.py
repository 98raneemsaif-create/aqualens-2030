"""Download only the two canonical PDFs recorded in approved preflight."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


def main():
    preflight = Path("docs/preflight_report.md").read_text(encoding="utf-8")
    urls = re.findall(r"\]\((https://[^)]+)\)", preflight)
    sources = [
        ("mewa_strategy", "National Water Strategy 2030", "MEWA", "ar",
         next(u for u in urls if "PublishingImages" in u)),
        ("gastat_methodology", "Methodology and Quality Report of Water Accounts", "GASTAT", "en",
         next(u for u in urls if "Water%2BAccounts_EN.pdf" in u)),
    ]
    root = Path("rag/sources")
    root.mkdir(parents=True, exist_ok=True)
    for source_id, title, organization, language, url in sources:
        pdf = root / (source_id + ".pdf")
        metadata_path = root / (source_id + ".json")
        if pdf.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            assert hashlib.sha256(pdf.read_bytes()).hexdigest() == metadata["sha256"]
            print(json.dumps(dict(source_id=source_id, reused=True, **metadata)))
            continue
        with urlopen(Request(url, headers={"User-Agent": "AquaLens2030 official-document snapshot"}), timeout=90) as response:
            content = response.read()
            resolved_url = response.url
        if not content.startswith(b"%PDF-"):
            raise ValueError(f"Official source did not return a PDF: {source_id}")
        metadata = dict(source_id=source_id, title=title, organization=organization, language=language,
                        canonical_url=url, resolved_url=resolved_url,
                        retrieved_at=datetime.now(timezone.utc).isoformat(), source_format="application/pdf",
                        sha256=hashlib.sha256(content).hexdigest(), filename=pdf.name)
        if organization == "MEWA":
            metadata["provenance_webpage"] = next(u for u in urls if "/ar/" in u and "Pages/Strategy.aspx" in u)
        with pdf.open("xb") as stream:
            stream.write(content)
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(metadata), flush=True)


if __name__ == "__main__":
    main()
