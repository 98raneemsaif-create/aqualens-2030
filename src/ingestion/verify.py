"""Independently read Kafka DLQ deliveries and reconcile the controlled proof."""

import argparse
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from src.common.config import IngestionConfig
from src.ingestion.bounded import read_run


def verify(config: IngestionConfig, manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text())
    result = json.loads((manifest_path.parent / 'consumer_result.json').read_text())
    assert manifest['run_id'] == result['run_id']
    assert manifest['source_count'] == 56 and manifest['fixture_count'] == 1
    assert result['produced_count'] == 57
    assert result['accepted_count'] == 56 and result['quarantined_count'] == 1
    assert len(result['quarantine_deliveries']) == 1
    accepted = [json.loads(line) for line in Path(result['accepted_path']).read_text().splitlines()]
    assert len(accepted) == 56
    with config.source_path.open(encoding='utf-8-sig', newline='') as handle:
        source_rows = list(csv.DictReader(handle))
    expected = sorted((int(row['Year']), row['Province'], row['Source'], Decimal(row['Value']))
                      for row in source_rows)
    actual = sorted((row['year'], row['region'], row['source'], Decimal(str(row['volume_m3'])))
                    for row in accepted)
    assert actual == expected, 'Accepted analytical values do not match the immutable source'
    assert all(row['run_id'] == manifest['run_id'] and row['record_kind'] == 'source' for row in accepted)
    assert len({row['event_id'] for row in accepted}) == 56
    records = []
    # A new Kafka consumer reads broker messages; no locally constructed DLQ output is trusted.
    for message in read_run(config.bootstrap_servers, manifest['quarantine_topic'], manifest['run_id'],
                            result['quarantine_deliveries'], config.timeout_seconds, 'aqualens-dlq-proof'):
        record = json.loads(message.value())
        assert record['run_id'] == manifest['run_id']
        assert record['rejection_reason'].strip()
        assert record['rejected_at']
        original = json.loads(record['original_payload'])
        assert original['event_id'] == 'fixture-malformed-volume'
        assert original['record_kind'] == 'test_fixture'
        assert original['volume_m3'] == 'not-a-number'
        assert original['event_id'] not in {row['event_id'] for row in accepted}
        records.append({'quarantine_partition': message.partition(), 'quarantine_offset': message.offset(),
                        **record})
    assert len(records) == 1
    source_hash = hashlib.sha256(config.source_path.read_bytes()).hexdigest()
    assert source_hash == manifest['source_sha256_before'] == manifest['source_sha256_after']
    proof = {'run_id': manifest['run_id'], 'produced_count': 57, 'accepted_count': len(accepted),
             'quarantined_count': len(records), 'accepted_values_match_source': actual == expected,
             'valid_source_records_quarantined': 0,
             'grand_total_accepted': sum(row['region'] == 'Grand Total' for row in accepted),
             'zero_volume_accepted': sum(row['volume_m3'] == 0 for row in accepted),
             'source_sha256_after_verification': source_hash,
             'quarantine_records_read_from_kafka': records}
    print(json.dumps({'action': 'quarantine_verified', **proof}), flush=True)
    return proof


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    verify(IngestionConfig.from_env(), parser.parse_args().manifest)
