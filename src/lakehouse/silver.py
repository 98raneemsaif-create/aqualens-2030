"""Business-key deduplication and real Delta MERGE from Bronze."""
from pathlib import Path

import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

from src.lakehouse.bronze import EVENT_SCHEMA

BUSINESS_KEY = ("year", "region", "source")


def merge_silver(bronze_path: Path, silver_path: Path) -> dict:
    unique = {}
    for row in DeltaTable(bronze_path).to_pyarrow_table().to_pylist():
        key = tuple(row[name] for name in BUSINESS_KEY)
        previous = unique.get(key)
        if previous and previous["volume_m3"] != row["volume_m3"]:
            raise ValueError(f"Conflicting observations in one Bronze batch: {key}")
        # Identical observations collapse deterministically, retaining metadata.
        if previous is None or (row["run_id"], row["event_id"]) > (previous["run_id"], previous["event_id"]):
            unique[key] = row
    source = pa.Table.from_pylist([unique[k] for k in sorted(unique)], schema=EVENT_SCHEMA)
    if not DeltaTable.is_deltatable(str(silver_path)):
        write_deltalake(silver_path, pa.Table.from_pylist([], schema=EVENT_SCHEMA))
    return (DeltaTable(silver_path).merge(
        source, " AND ".join(f"target.{k} = incoming.{k}" for k in BUSINESS_KEY),
        source_alias="incoming", target_alias="target",
    ).when_matched_update_all().when_not_matched_insert_all().execute())
