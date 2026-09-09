"""Inspect only Phase A service state, mounts, resource settings, and host HTTP."""

import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request


def docker_json(*arguments):
    return json.loads(subprocess.check_output(['docker', *arguments], text=True, encoding='utf-8'))


if __name__ == '__main__':
    services = subprocess.check_output(['docker', 'compose', 'config', '--services'], text=True).split()
    assert set(services) == {'airflow', 'kafka'}, services
    print('Exactly two Compose services:', services)
    ids = subprocess.check_output(['docker', 'compose', 'ps', '-q'], text=True).split()
    assert len(ids) == 2, ids
    containers = docker_json('inspect', *ids)
    for container in containers:
        state = container['State']
        assert state['Running'] and state['Health']['Status'] == 'healthy'
        image = docker_json('image', 'inspect', container['Image'])[0]
        print(json.dumps({
            'name': container['Name'], 'image': container['Config']['Image'],
            'image_id': container['Image'], 'image_size_bytes': image['Size'],
            'platform': image['Os'] + '/' + image['Architecture'],
            'health': state['Health']['Status'], 'running': state['Running'],
            'restart_count': container['RestartCount'], 'oom_killed': state['OOMKilled'],
            'memory_limit_bytes': container['HostConfig']['Memory'],
            'nano_cpus': container['HostConfig']['NanoCpus'], 'mounts': container['Mounts'],
        }, indent=2))
        assert container['RestartCount'] == 0 and not state['OOMKilled']
        if container['Config']['Labels']['com.docker.compose.service'] == 'airflow':
            source = next(m for m in container['Mounts'] if m['Destination'] == '/opt/airflow/data/source')
            assert source['RW'] is False
    config = docker_json('compose', 'config', '--format', 'json')
    port = config['services']['airflow']['ports'][0]['published']
    for endpoint in ['/', '/api/v2/monitor/health']:
        with urllib.request.urlopen('http://127.0.0.1:' + str(port) + endpoint, timeout=15) as response:
            print('Host HTTP:', endpoint, response.status)
            assert response.status == 200
            if endpoint.endswith('health'):
                print(response.read().decode())
    running = subprocess.check_output(['docker', 'ps', '--format', '{{.Names}} {{.Image}}'], text=True)
    print('All running containers:\n' + running)
    assert not any(word in running.lower() for word in ['zookeeper', 'redis', 'celery', 'spark', 'marquez', 'chromadb'])
    source = Path('data/source/water_distribution_urban_saudi.csv')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest == '4df640b65d3341c1e42e64be7582434aa5e19ceabfa952feb35195f8350a849c'
    print('Host source SHA-256:', digest)
    print('PASS: host service/mount/HTTP audit. No pipeline implementation tested.')
