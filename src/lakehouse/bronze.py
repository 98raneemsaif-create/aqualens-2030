"""Append accepted Kafka events to real, append-only Delta storage."""
import json
from pathlib import Path

import pyarrow as pa
from deltalake import write_deltalake

EVENT_SCHEMA = pa.schema([
    ("year", pa.int64()), ("region", pa.string()), ("source", pa.string()),
    ("volume_m3", pa.float64()), ("run_id", pa.string()),
    ("event_id", pa.string()), ("record_kind", pa.string()),
])


def read_accepted(path: Path) -> pa.Table:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return pa.Table.from_pylist(rows, schema=EVENT_SCHEMA)


def append_bronze(accepted_path: Path, table_path: Path) -> None:
    write_deltalake(table_path, read_accepted(accepted_path), mode="append",
                    configuration={"delta.appendOnly": "true"})
