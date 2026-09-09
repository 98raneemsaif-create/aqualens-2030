"""Validate raw Kafka JSON and acknowledge real DLQ writes before success."""

import argparse
import json
from pathlib import Path
from pydantic import ValidationError

from src.common.config import IngestionConfig
from src.ingestion.bounded import read_run
from src.ingestion.kafka_io import new_producer, publish_json
from src.ingestion.quarantine import quarantine_record, recover_run_id
from src.ingestion.schema import WaterEvent


def consume(config: IngestionConfig, manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text())
    run_id = manifest['run_id']
    if manifest['produced_count'] != len(manifest['deliveries']):
        raise ValueError('Expected record count disagrees with acknowledged offsets')
    accepted, rejected, dlq_deliveries = 0, 0, []
    dlq = new_producer(config)
    accepted_path = manifest_path.parent / 'accepted.jsonl'
    # Exclusive creation prevents an accidental replay from overwriting prior output.
    with accepted_path.open('x', encoding='utf-8') as output:
        for message in read_run(config.bootstrap_servers, manifest['raw_topic'], run_id,
                                manifest['deliveries'], config.timeout_seconds, 'aqualens-ingestion'):
            payload = message.value()
            try:
                if payload is None:
                    raise ValueError('Kafka tombstone is not a JSON water event')
                event = WaterEvent.model_validate_json(payload)
            except (ValidationError, ValueError) as error:
                reason = str(error)
                record = quarantine_record(payload, recover_run_id(payload, message.headers()), reason,
                                           message.topic(), message.partition(), message.offset())
                delivery = publish_json(dlq, manifest['quarantine_topic'], [record], run_id,
                                        config.timeout_seconds)
                dlq_deliveries.extend(delivery)
                rejected += 1
                print(json.dumps({'action': 'quarantined', **record, 'dlq_delivery': delivery[0]}), flush=True)
            else:
                output.write(event.model_dump_json() + '\n')
                accepted += 1
                print(json.dumps({'action': 'accepted', 'run_id': run_id, 'event_id': event.event_id,
                                  'raw_partition': message.partition(), 'raw_offset': message.offset()}), flush=True)
    if accepted + rejected != manifest['produced_count']:
        raise RuntimeError('Consumed count differs from producer acknowledgements')
    result = {'run_id': run_id, 'produced_count': manifest['produced_count'],
              'accepted_count': accepted, 'quarantined_count': rejected,
              'accepted_path': str(accepted_path), 'quarantine_deliveries': dlq_deliveries}
    with (manifest_path.parent / 'consumer_result.json').open('x', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2)
        handle.write('\n')
    print(json.dumps({'action': 'consumer_complete', **result}), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    consume(IngestionConfig.from_env(), parser.parse_args().manifest)
