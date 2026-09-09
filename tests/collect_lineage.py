"""Snapshot and collect real OpenLineage FileTransport events for AquaLens."""

import argparse
import json
from pathlib import Path

DAG_TOKEN = "aqualens_2030_pipeline."


def raw_files(root: Path) -> list[Path]:
    return sorted(p for p in root.glob("event-*") if p.is_file())


def snapshot(root: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps([p.name for p in raw_files(root)], indent=2) + "\n", encoding="utf-8")


def collect(root: Path, before: Path, output_dir: Path) -> None:
    previous = set(json.loads(before.read_text(encoding="utf-8")))
    new_files = [p for p in raw_files(root) if p.name not in previous]
    events = []
    for path in new_files:
        try:
            event = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        job = event.get("job") or {}
        name = str(job.get("name", ""))
        if DAG_TOKEN not in name:
            continue
        events.append(event)

    output_dir.mkdir(parents=True, exist_ok=True)
    grouped = {"START": [], "COMPLETE": [], "FAIL": []}
    for event in events:
        event_type = event.get("eventType")
        if event_type in grouped:
            grouped[event_type].append(event)

    for event_type, rows in grouped.items():
        path = output_dir / f"{event_type.lower()}.jsonl"
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")

    summary = {
        "new_raw_files": len(new_files),
        "aqualens_events": len(events),
        "counts": {key: len(value) for key, value in grouped.items()},
        "jobs": sorted({(event.get("job") or {}).get("name") for event in events}),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary), flush=True)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    snap = sub.add_parser("snapshot")
    snap.add_argument("--root", type=Path, default=Path("docs/evidence/lineage/raw"))
    snap.add_argument("--output", type=Path, required=True)
    col = sub.add_parser("collect")
    col.add_argument("--root", type=Path, default=Path("docs/evidence/lineage/raw"))
    col.add_argument("--before", type=Path, required=True)
    col.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "snapshot":
        snapshot(args.root, args.output)
    else:
        collect(args.root, args.before, args.output_dir)


if __name__ == "__main__":
    main()
