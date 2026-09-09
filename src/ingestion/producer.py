"""Publish the immutable CSV and, only when requested, one malformed fixture."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from src.common.config import IngestionConfig
from src.ingestion.kafka_io import ensure_topics, new_producer, publish_json


def source_events(path: Path, run_id: str) -> list[dict]:
    with path.open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.DictReader(handle))
    return [dict(year=int(row['Year']), region=row['Province'], source=row['Source'],
                 volume_m3=float(row['Value']), run_id=run_id,
                 event_id=f'source-{index:04d}', record_kind='source')
            for index, row in enumerate(rows, start=1)]


def produce(config: IngestionConfig, fixture_path: Path | None = None,
            quality_fixture_path: Path | None = None) -> Path:
    run_id = str(uuid4())
    run_dir = config.output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    source_hash = hashlib.sha256(config.source_path.read_bytes()).hexdigest()
    events = source_events(config.source_path, run_id)
    source_count = len(events)
    if fixture_path is not None:
        fixture = json.loads(fixture_path.read_text(encoding='utf-8'))
        events.append({**fixture, 'run_id': run_id, 'event_id': 'fixture-malformed-volume',
                       'record_kind': 'test_fixture'})
    if quality_fixture_path is not None:
        fixture = json.loads(quality_fixture_path.read_text(encoding='utf-8'))
        if not isinstance(fixture.get('volume_m3'), (int, float)) or fixture['volume_m3'] >= 0:
            raise ValueError('Quality fixture must contain a numeric negative volume_m3')
        events.append({**fixture, 'run_id': run_id, 'event_id': 'fixture-negative-volume',
                       'record_kind': 'test_fixture'})
    ensure_topics(config)
    deliveries = publish_json(new_producer(config), config.raw_topic, events, run_id,
                              config.timeout_seconds)
    after_hash = hashlib.sha256(config.source_path.read_bytes()).hexdigest()
    if source_hash != after_hash:
        raise RuntimeError('Immutable source hash changed during production')
    manifest = {'run_id': run_id, 'raw_topic': config.raw_topic,
                'quarantine_topic': config.quarantine_topic, 'source_path': str(config.source_path),
                'source_sha256_before': source_hash, 'source_sha256_after': after_hash,
                'source_count': source_count, 'fixture_count': len(events) - source_count,
                'produced_count': len(deliveries), 'deliveries': deliveries}
    path = run_dir / 'producer_manifest.json'
    path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'action': 'producer_complete', 'manifest': str(path), **manifest}), flush=True)
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--malformed-fixture', type=Path)
    parser.add_argument('--quality-fixture', type=Path)
    args = parser.parse_args()
    produce(IngestionConfig.from_env(), args.malformed_fixture, args.quality_fixture)
