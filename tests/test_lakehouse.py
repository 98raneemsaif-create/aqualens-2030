"""Real Delta integration proof. Run in the approved container via unittest."""
import csv
import hashlib
import json
import math
import unittest
from collections import Counter
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import deltalake
import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

from src.lakehouse.bronze import EVENT_SCHEMA, append_bronze, read_accepted
from src.lakehouse.silver import BUSINESS_KEY, merge_silver
from src.lakehouse.gold import build_gold
from src.lakehouse.schema_proof import prove_schema_rejection, snapshot

RUN_ID = "ea8464c0-722b-4c8a-a83c-252fff68ee33"
ACCEPTED = Path("storage/ingestion") / RUN_ID / "accepted.jsonl"
SOURCE = Path("data/source/water_distribution_urban_saudi.csv")


def rows(path):
    return DeltaTable(path).to_pyarrow_table().to_pylist()


def analytical(records):
    return Counter((r["year"], r["region"], r["source"], Decimal(str(r["volume_m3"]))) for r in records)


def describe(path):
    table = DeltaTable(path)
    return dict(path=str(path), **snapshot(path), history=table.history(),
                configuration=table.metadata().configuration,
                delta_log_files=sorted(p.name for p in (path / "_delta_log").glob("*.json")))


class LakehouseProof(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof_id = str(uuid4())
        cls.root = Path("storage/delta/proofs/phase_c") / cls.proof_id
        cls.root.mkdir(parents=True, exist_ok=False)
        cls.evidence = Path("docs/evidence/phase_c") / cls.proof_id
        cls.evidence.mkdir(parents=True, exist_ok=False)
        cls.bronze = cls.root / "bronze/water_events"
        cls.silver = cls.root / "silver/water_distribution"
        cls.gold = cls.root / "gold/gold_regional_water_profile"
        cls.accepted = read_accepted(ACCEPTED)
        cls.output = dict(proof_id=cls.proof_id, deltalake_version=deltalake.__version__,
                          input=dict(run_id=RUN_ID, path=str(ACCEPTED), expected_count=56,
                                     sha256=hashlib.sha256(ACCEPTED.read_bytes()).hexdigest()))
        print(f"Fresh proof root: {cls.root}; evidence: {cls.evidence}", flush=True)

    @classmethod
    def tearDownClass(cls):
        (cls.evidence / "results.json").write_text(json.dumps(cls.output, indent=2) + "\n")

    def test_01_input_and_bronze(self):
        result = json.loads((ACCEPTED.parent / "consumer_result.json").read_text())
        self.assertEqual((result["run_id"], result["accepted_count"]), (RUN_ID, 56))
        self.assertEqual(self.accepted.num_rows, 56)
        self.assertEqual({r["run_id"] for r in self.accepted.to_pylist()}, {RUN_ID})
        self.assertEqual({r["record_kind"] for r in self.accepted.to_pylist()}, {"source"})
        append_bronze(ACCEPTED, self.bronze)
        self.assertEqual(Counter(json.dumps(r, sort_keys=True) for r in rows(self.bronze)),
                         Counter(json.dumps(r, sort_keys=True) for r in self.accepted.to_pylist()))
        self.assertEqual(sum(r["region"] == "Grand Total" for r in rows(self.bronze)), 4)
        self.assertEqual(sum(r["volume_m3"] == 0 for r in rows(self.bronze)), 20)
        self.assertEqual(DeltaTable(self.bronze).metadata().configuration["delta.appendOnly"], "true")
        self.assertTrue(list((self.bronze / "_delta_log").glob("*.json")))
        self.output["bronze"] = describe(self.bronze)
        append_path = self.root / "append_only_test"
        append_bronze(ACCEPTED, append_path)
        before = describe(append_path)
        append_bronze(ACCEPTED, append_path)
        self.assertEqual(analytical(rows(append_path)), analytical(rows(self.bronze)) + analytical(rows(self.bronze)))
        self.output["append_proof"] = dict(before=before, after=describe(append_path))

    def test_02_silver_merge_and_replay(self):
        first = merge_silver(self.bronze, self.silver)
        first_state = describe(self.silver)
        second = merge_silver(self.bronze, self.silver)
        data = rows(self.silver)
        self.assertEqual(first_state["count"], 56)
        self.assertEqual(len(data), 56)
        self.assertEqual(len({tuple(r[k] for k in BUSINESS_KEY) for r in data}), 56)
        self.assertEqual(analytical(data), analytical(self.accepted.to_pylist()))
        self.assertEqual(sum(r["region"] == "Grand Total" for r in data), 4)
        self.assertEqual(sum(r["volume_m3"] == 0 for r in data), 20)
        self.assertEqual(DeltaTable(self.silver).history()[0]["operation"], "MERGE")
        self.assertEqual(first["num_target_rows_inserted"], 56)
        self.assertEqual(second["num_target_rows_inserted"], 0)
        self.output["silver"] = dict(first_metrics=first, first_state=first_state,
                                    replay_metrics=second, replay_state=describe(self.silver),
                                    unique_keys=56, grand_total_rows=4, zero_rows=20,
                                    accepted_analytical_tuples_match=True)

    def test_03_schema_rejection(self):
        proof = prove_schema_rejection(self.root / "schema_rejection", self.accepted)
        self.assertEqual(proof["before"], proof["after"])
        self.output["schema_rejection"] = proof
        print(json.dumps(proof), flush=True)

    def test_04_gold_independent_recomputation(self):
        build_gold(self.silver, self.gold)
        profiles = rows(self.gold)
        self.assertEqual(len(profiles), 13)
        self.assertEqual(len({(r["year"], r["region"]) for r in profiles}), 13)
        for profile in profiles:
            self.assertNotEqual(profile["region"], "Grand Total")
            members = [r for r in rows(self.silver) if (r["year"], r["region"]) == (profile["year"], profile["region"])]
            self.assertEqual(len(members), 4)
            total = sum(Decimal(str(r["volume_m3"])) for r in members)
            maximum = max(Decimal(str(r["volume_m3"])) for r in members)
            name = sorted(r["source"] for r in members if Decimal(str(r["volume_m3"])) == maximum)[0]
            self.assertEqual(Decimal(str(profile["total_water_volume_m3"])), total)
            self.assertEqual(profile["dominant_source"], name)
            self.assertEqual(Decimal(str(profile["dominant_source_volume_m3"])), maximum)
            self.assertTrue(math.isclose(profile["dominant_source_share_pct"], float(maximum / total * 100), rel_tol=1e-12))
            self.assertEqual(profile["active_source_count"], len([r for r in members if Decimal(str(r["volume_m3"])) > 0]))
        self.output["gold"] = dict(table=describe(self.gold), profiles=profiles,
                                  independently_recomputed_profiles=13, grand_total_rows=0)

    def test_05_source_provenance(self):
        digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        self.assertEqual(digest, "4df640b65d3341c1e42e64be7582434aa5e19ceabfa952feb35195f8350a849c")
        with SOURCE.open(newline="", encoding="utf-8") as stream:
            official = Counter((int(r["Year"]), r["Province"], r["Source"], Decimal(r["Value"])) for r in csv.DictReader(stream))
        self.assertEqual(official, analytical(rows(self.silver)))
        observations = []
        for name in sorted({r["source"] for r in rows(self.silver)}):
            data = [r for r in rows(self.silver) if r["source"] == name]
            regional = sum(r["volume_m3"] for r in data if r["region"] != "Grand Total")
            supplied = sum(r["volume_m3"] for r in data if r["region"] == "Grand Total")
            observations.append(dict(source=name, regional_sum_m3=regional, supplied_grand_total_m3=supplied,
                                     difference_m3=regional-supplied))
        self.output["provenance"] = dict(source_sha256=digest, source_matches_silver=True, observations=observations)

    def test_06_isolated_update_insert_and_tie(self):
        initial = dict(year=2024, region="TEST FIXTURE ONLY", source="B", volume_m3=1.0,
                       run_id="test", event_id="1", record_kind="test_fixture")
        first, batch, silver, gold = [self.root / name for name in ("fixture_first", "fixture_batch", "fixture_silver", "fixture_gold")]
        write_deltalake(first, pa.Table.from_pylist([initial], schema=EVENT_SCHEMA))
        merge_silver(first, silver)
        updated = dict(initial, volume_m3=2.0)
        inserted = dict(updated, source="A", event_id="2")
        zero = dict(initial, source="C", volume_m3=0.0, event_id="3")
        write_deltalake(batch, pa.Table.from_pylist([updated, inserted, zero, inserted], schema=EVENT_SCHEMA))
        metrics = merge_silver(batch, silver)
        self.assertEqual(metrics["num_target_rows_updated"], 1)
        self.assertEqual(metrics["num_target_rows_inserted"], 2)
        self.assertEqual(len(rows(silver)), 3)
        build_gold(silver, gold)
        profile = rows(gold)[0]
        self.assertEqual((profile["dominant_source"], profile["dominant_source_share_pct"], profile["active_source_count"]), ("A", 50.0, 2))
        self.output["isolated_fixtures"] = dict(initial=[initial], batch=[updated, inserted, zero, inserted],
                                              merge_metrics=metrics, silver=rows(silver), gold=profile)


if __name__ == "__main__":
    unittest.main(verbosity=2)
