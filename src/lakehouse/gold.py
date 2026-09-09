"""Regional Water Source Concentration, derived exclusively from Silver."""
from collections import defaultdict
from math import fsum
from pathlib import Path

import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

GOLD_SCHEMA = pa.schema([
    ("year", pa.int64()), ("region", pa.string()),
    ("total_water_volume_m3", pa.float64()), ("dominant_source", pa.string()),
    ("dominant_source_volume_m3", pa.float64()),
    ("dominant_source_share_pct", pa.float64()), ("active_source_count", pa.int64()),
])


def build_gold(silver_path: Path, gold_path: Path) -> None:
    groups = defaultdict(list)
    for row in DeltaTable(silver_path).to_pyarrow_table().to_pylist():
        if row["region"] != "Grand Total":
            groups[(row["year"], row["region"])].append(row)
    profiles = []
    for (year, region), rows in sorted(groups.items()):
        total = fsum(r["volume_m3"] for r in rows)
        dominant = min(rows, key=lambda r: (-r["volume_m3"], r["source"]))
        profiles.append(dict(
            year=year, region=region, total_water_volume_m3=total,
            dominant_source=dominant["source"], dominant_source_volume_m3=dominant["volume_m3"],
            dominant_source_share_pct=dominant["volume_m3"] / total * 100 if total else None,
            active_source_count=sum(r["volume_m3"] > 0 for r in rows),
        ))
    write_deltalake(gold_path, pa.Table.from_pylist(profiles, schema=GOLD_SCHEMA),
                    mode="overwrite", name="gold_regional_water_profile")
