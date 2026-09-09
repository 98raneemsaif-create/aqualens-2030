"""Correlate actual emitted events by Airflow run ID, stage and attempt."""
import json
from pathlib import Path
import sys

run_id, destination = sys.argv[1:]
output = Path(destination)
output.mkdir(parents=True,exist_ok=False)
records=[]
events=[]
for path in sorted(Path('docs/evidence/lineage/raw').glob('event-*.json')):
    event=json.loads(path.read_text())
    facets=event['run'].get('facets',{})
    airflow=facets.get('airflow',facets.get('airflowDagRun',{}))
    if airflow.get('dagRun',{}).get('run_id') != run_id:
        continue
    events.append(event)
    records.append(dict(file=str(path),event_type=event['eventType'],job=event['job']['name'],
        lineage_run_id=event['run']['runId'],airflow_run_id=run_id,
        attempt=airflow.get('taskInstance',{}).get('try_number'),event_time=event['eventTime']))
for kind in ['START','COMPLETE','FAIL']:
    (output/f'{kind.lower()}.jsonl').write_text(''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in events if e['eventType']==kind),encoding='utf-8')
summary=dict(run_id=run_id,counts={k:sum(r['event_type']==k for r in records) for k in ['START','COMPLETE','FAIL']},records=records)
(output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(dict(run_id=run_id,counts=summary['counts'])))
