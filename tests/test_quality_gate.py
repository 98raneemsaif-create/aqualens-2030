"""Real GX + Delta tests for the Phase E quality gate."""

import json
import tempfile
import unittest
from pathlib import Path

import pyarrow as pa
from deltalake import write_deltalake

from src.lakehouse.bronze import EVENT_SCHEMA
from src.quality.gate import DataQualityError, validate_silver


class QualityGateTests(unittest.TestCase):
    def _write(self, root: Path, rows: list[dict]) -> Path:
        path = root / "silver"
        write_deltalake(path, pa.Table.from_pylist(rows, schema=EVENT_SCHEMA))
        return path

    @staticmethod
    def _row(event_id: str, *, volume: float = 1.0, region: str = "Riyadh", source: str = "Groundwater"):
        return {
            "year": 2024,
            "region": region,
            "source": source,
            "volume_m3": volume,
            "run_id": "quality-unit-test",
            "event_id": event_id,
            "record_kind": "test_fixture",
        }

    def test_real_gx_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            silver = self._write(root, [self._row("a"), self._row("b", source="Surface water", volume=0.0)])
            evidence = root / "success.json"
            summary = validate_silver(silver, evidence)
            self.assertTrue(summary["success"])
            self.assertTrue(json.loads(evidence.read_text())["success"])

    def test_negative_volume_fails_real_gx_and_writes_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            silver = self._write(root, [self._row("a"), self._row("negative", volume=-1.0, region="Quality Gate Fixture")])
            evidence = root / "failure.json"
            with self.assertRaises(DataQualityError):
                validate_silver(silver, evidence)
            payload = json.loads(evidence.read_text())
            self.assertFalse(payload["success"])
            self.assertTrue(any(not row["success"] for row in payload["results"]))

    def test_duplicate_business_key_fails_real_gx(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            silver = self._write(root, [self._row("a"), self._row("b")])
            evidence = root / "duplicate.json"
            with self.assertRaises(DataQualityError):
                validate_silver(silver, evidence)
            payload = json.loads(evidence.read_text())
            self.assertFalse(payload["success"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
