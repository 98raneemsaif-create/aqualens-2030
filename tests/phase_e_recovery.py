"""Narrow run inspection, failed-task recovery, and safe failure-demo trigger."""
import argparse
import json
import os
from pathlib import Path
import subprocess

from airflow.models.dagrun import DagRun
from airflow.models.taskinstance import TaskInstance, clear_task_instances
from airflow.utils.session import create_session

DAG = 'aqualens_2030_pipeline'
FINAL = 'rag_grounded_answer_smoke_test'
ROOT = Path('docs/evidence/phase_e')


def inspect_run(run_id):
    with create_session() as session:
        run = session.query(DagRun).filter_by(dag_id=DAG,run_id=run_id).one()
        tasks=session.query(TaskInstance).filter_by(dag_id=DAG,run_id=run_id).all()
        return dict(dag_id=DAG,run_id=run_id,state=run.state,conf=run.conf,
            tasks=[dict(task_id=t.task_id,state=t.state,try_number=t.try_number,
                        start_date=str(t.start_date),end_date=str(t.end_date)) for t in tasks])


def capture(run_id,label):
    output=ROOT/label
    output.mkdir(parents=True,exist_ok=False)
    state=inspect_run(run_id)
    (output/'states.json').write_text(json.dumps(state,indent=2)+'\n')
    logs=Path('/opt/airflow/runtime/logs')/f'dag_id={DAG}'/f'run_id={run_id}'
    keys=[os.environ[n] for n in ('GEMINI_API_KEY','GOOGLE_API_KEY') if os.environ.get(n)]
    for source in logs.rglob('*.log'):
        text=source.read_text()
        for key in keys:
            if key in text:
                raise RuntimeError('Credential found in task log; refusing capture')
        target=output/source.relative_to(logs)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(text)
    print(json.dumps(state),flush=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['capture','clear','trigger'])
    parser.add_argument('--run-id',default='phase_e_success')
    parser.add_argument('--label')
    args=parser.parse_args()
    if args.action=='capture':
        capture(args.run_id,args.label)
    elif args.action=='clear':
        before=inspect_run(args.run_id)
        assert len(before['tasks'])==9
        assert all(t['state']=='success' for t in before['tasks'] if t['task_id']!=FINAL)
        with create_session() as session:
            failed=session.query(TaskInstance).filter_by(dag_id=DAG,run_id=args.run_id,task_id=FINAL,state='failed').all()
            assert len(failed)==1
            clear_task_instances(failed,session=session)
        print(json.dumps(dict(action='clear_failed_only',run_id=args.run_id,task_id=FINAL)))
    else:
        assert args.run_id=='phase_e_quality_failure'
        assert inspect_run('phase_e_success')['state']=='success'
        subprocess.run(['airflow','dags','trigger',DAG,'--run-id',args.run_id,
                        '--conf',json.dumps({'quality_failure_demo':True})],check=True)


if __name__=='__main__':
    main()
