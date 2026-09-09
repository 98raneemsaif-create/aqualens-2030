"""An isolated real Delta rejection; no pre-validation or schema evolution."""
import json
from pathlib import Path

import pyarrow as pa
from deltalake import DeltaTable, write_deltalake


def snapshot(path: Path) -> dict:
    table = DeltaTable(path)
    return dict(version=table.version(), count=table.to_pyarrow_table().num_rows,
                schema=json.loads(table.schema().to_json()))


def prove_schema_rejection(path: Path, valid: pa.Table) -> dict:
    write_deltalake(path, valid, mode="error")
    before = snapshot(path)
    invalid = valid.set_column(valid.schema.get_field_index("volume_m3"), "volume_m3",
                               pa.array(["not-a-number"] * valid.num_rows))
    try:
        write_deltalake(path, invalid, mode="append")
    except Exception as error:
        # This installed Delta writer reports conversion rejection as Exception.
        # Do not classify unrelated I/O or runtime failures as schema success.
        if "Cannot cast string 'not-a-number'" not in str(error):
            raise
        rejection = dict(type=type(error).__name__, message=str(error))
    else:
        raise AssertionError("Delta unexpectedly accepted an incompatible schema")
    after = snapshot(path)
    if after != before:
        raise AssertionError("Rejected write changed the Delta table")
    return dict(before=before, rejection=rejection, after=after, unchanged=True)
