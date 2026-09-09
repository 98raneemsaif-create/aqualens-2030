"""Runtime-only checks. No ingestion, transformations, rules, models, or DAGs."""

import errno
import hashlib
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import traceback
import urllib.request


def packages() -> None:
    assert sys.version_info[:2] == (3, 11), sys.version
    print(f"Python: {sys.version}", flush=True)
    for line in Path('/opt/airflow/requirements/runtime.lock').read_text().splitlines():
        if not line or line.startswith('#'):
            continue
        name, expected = line.split('==')
        actual = importlib.metadata.version(name)
        assert actual == expected, (name, expected, actual)
    print('All 195 frozen runtime package versions match.', flush=True)
    for name in [
        'airflow', 'airflow.providers.openlineage', 'openlineage.client',
        'great_expectations', 'deltalake', 'confluent_kafka', 'pydantic',
        'chromadb', 'sentence_transformers', 'rank_bm25', 'google.genai',
        'torch', 'transformers', 'sentencepiece', 'pyarrow',
    ]:
        importlib.import_module(name)
        print(f'Import OK: {name}', flush=True)
    from sentence_transformers import CrossEncoder, SentenceTransformer
    import torch

    assert CrossEncoder and SentenceTransformer
    assert torch.__version__ == '2.14.0+cpu'
    assert torch.version.cuda is None
    installed = {d.metadata['Name'].lower() for d in importlib.metadata.distributions()}
    assert not any(n.startswith(('nvidia-', 'cuda-', 'pyspark', 'celery', 'redis')) for n in installed)
    print(f'CPU-only torch: {torch.__version__}; CUDA build: {torch.version.cuda}', flush=True)


def kafka_connectivity() -> None:
    from confluent_kafka.admin import AdminClient

    address = os.environ['KAFKA_BOOTSTRAP_SERVERS']
    metadata = AdminClient({'bootstrap.servers': address}).list_topics(timeout=15)
    assert metadata.brokers
    print(json.dumps({'bootstrap': address, 'cluster_id': metadata.cluster_id,
                      'brokers': {key: str(value) for key, value in metadata.brokers.items()}}))
    print('Kafka metadata request from Airflow succeeded; no business records produced.')


def airflow_runtime() -> None:
    from airflow.configuration import conf

    assert importlib.metadata.version('apache-airflow') == '3.3.1'
    for key, expected in [('executor', 'LocalExecutor'), ('parallelism', '1'),
                          ('max_active_runs_per_dag', '1'), ('load_examples', 'false')]:
        actual = conf.get('core', key)
        assert actual.lower() == expected.lower(), (key, actual)
        print(f'Airflow core.{key}={actual}')
    with urllib.request.urlopen('http://localhost:8080/api/v2/monitor/health', timeout=10) as response:
        health = json.load(response)
    print('Airflow health:', json.dumps(health))
    assert health['metadatabase']['status'] == 'healthy'
    assert health['scheduler']['status'] == 'healthy'
    with sqlite3.connect('file:/opt/airflow/runtime/airflow.db?mode=ro', uri=True) as connection:
        mode = connection.execute('PRAGMA journal_mode').fetchone()[0]
    print('SQLite journal_mode:', mode)
    assert mode.lower() == 'wal'


def lineage_configuration() -> None:
    from airflow import plugins_manager
    from airflow.providers_manager import ProvidersManager
    from airflow.providers.openlineage.plugins.adapter import OpenLineageAdapter
    from openlineage.client.transport.file import FileTransport

    provider = ProvidersManager().providers['apache-airflow-providers-openlineage']
    print('OpenLineage provider:', provider.version)
    assert provider.version == '2.20.0'
    plugins_manager.ensure_plugins_loaded()
    errors = plugins_manager.get_import_errors()
    assert not errors, errors
    plugins = plugins_manager.get_plugin_info()
    names = [plugin['name'] for plugin in plugins]
    assert 'OpenLineageProviderPlugin' in names
    print('Plugin import errors:', errors)
    print('Loaded plugins:', names)
    client = OpenLineageAdapter().get_or_create_openlineage_client()
    assert isinstance(client.transport, FileTransport)
    assert client.transport.config.append is False
    print('OpenLineage transport:', type(client.transport).__name__)
    print('OpenLineage append:', client.transport.config.append)
    print('OpenLineage file prefix:', client.transport.config.log_file_path)
    print('OpenLineage namespace:', os.environ['AIRFLOW__OPENLINEAGE__NAMESPACE'])
    directory = Path('/opt/airflow/docs/evidence/lineage/raw')
    with tempfile.NamedTemporaryFile(prefix='permission-check-', suffix='.tmp', dir=directory) as probe:
        probe.write(b'Phase A filesystem permission check; not a lineage event.\n')
        probe.flush()
        assert Path(probe.name).read_bytes().startswith(b'Phase A')
    print('Lineage directory create/write/read/delete succeeded; no events emitted.')


def source_mount() -> None:
    path = Path('/opt/airflow/data/source/water_distribution_urban_saudi.csv')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == '4df640b65d3341c1e42e64be7582434aa5e19ceabfa952feb35195f8350a849c'
    # O_WRONLY without O_TRUNC never writes or truncates the immutable source.
    try:
        descriptor = os.open(path, os.O_WRONLY)
    except OSError as error:
        assert error.errno == errno.EROFS, error
        print('Source write-open refused by read-only filesystem (EROFS).')
    else:
        os.close(descriptor)
        raise AssertionError('Source mount unexpectedly permits write-open.')
    print('Immutable source SHA-256:', digest)


if __name__ == '__main__':
    failures = []
    checks = [packages, kafka_connectivity, airflow_runtime, lineage_configuration, source_mount]
    if len(sys.argv) > 1:
        requested = set(sys.argv[1:])
        assert requested <= {check.__name__ for check in checks}, requested
        checks = [check for check in checks if check.__name__ in requested]
    for check in checks:
        print(f'\nCHECK: {check.__name__}', flush=True)
        try:
            check()
        except Exception:
            failures.append(check.__name__)
            traceback.print_exc()
        else:
            print(f'PASS: {check.__name__}', flush=True)
    if failures:
        raise SystemExit(f'Phase A runtime checks failed: {failures}')
    print('\nPASS: Phase A runtime smoke checks. No scored pipeline behavior tested.')
