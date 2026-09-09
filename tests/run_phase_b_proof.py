"""Host proof driver: execute real container commands and retain their output."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


def execute(directory: Path, filename: str, arguments: list[str]) -> str:
    completed = subprocess.run(arguments, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               encoding='utf-8', errors='replace', timeout=180)
    text = completed.stdout
    with (directory / filename).open('x', encoding='utf-8') as handle:
        handle.write('Captured UTC: ' + datetime.now(timezone.utc).isoformat() + '\n')
        handle.write('Command argv: ' + json.dumps(arguments) + '\n')
        handle.write(text)
        handle.write('\nExit code: ' + str(completed.returncode) + '\n')
    print(filename, 'exit_code=', completed.returncode, flush=True)
    if completed.returncode:
        print(text, flush=True)
        raise SystemExit(completed.returncode)
    return text


def action(text: str, name: str) -> dict:
    for line in reversed(text.splitlines()):
        if line.startswith('{'):
            record = json.loads(line)
            if record.get('action') == name:
                return record
    raise AssertionError(f'Missing actual execution result: {name}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir', type=Path, required=True)
    directory = parser.parse_args().evidence_dir
    directory.mkdir(parents=True, exist_ok=False)
    before = hashlib.sha256(Path('data/source/water_distribution_urban_saudi.csv').read_bytes()).hexdigest()
    base = ['docker', 'compose', 'exec', '-T', 'airflow', 'python']
    produced = action(execute(directory, 'producer.log', base + ['-m', 'src.ingestion.producer',
                      '--malformed-fixture', 'tests/fixtures/malformed_water_event.json']), 'producer_complete')
    manifest = produced['manifest']
    consumed = action(execute(directory, 'consumer.log', base + ['-m', 'src.ingestion.consumer',
                      '--manifest', manifest]), 'consumer_complete')
    verified = action(execute(directory, 'quarantine_verification.log', base + ['-m', 'src.ingestion.verify',
                      '--manifest', manifest]), 'quarantine_verified')
    after = hashlib.sha256(Path('data/source/water_distribution_urban_saudi.csv').read_bytes()).hexdigest()
    assert before == after == verified['source_sha256_after_verification']
    summary = {'source_sha256_before': before, 'source_sha256_after': after,
               'producer': produced, 'consumer': consumed, 'verification': verified}
    with (directory / 'summary.json').open('x', encoding='utf-8') as handle:
        json.dump(summary, handle, indent=2)
        handle.write('\n')
    print(json.dumps({'run_id': produced['run_id'], 'produced': produced['produced_count'],
                      'accepted': consumed['accepted_count'], 'quarantined': consumed['quarantined_count'],
                      'source_unchanged': before == after, 'evidence': str(directory)}), flush=True)
