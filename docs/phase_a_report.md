# Phase A Runtime and Scaffold Report

**Result: PASS.** Built and started on 08 September 2026; remaining validation completed on 09 September 2026. Phase A was resumed against the existing working tree and running containers without rebuilding, restarting, or overwriting completed setup evidence.

The approved two-service environment works. No business ingestion, Delta transformation, Great Expectations rule, RAG implementation, model download, or project DAG was implemented. Phase B has not started.

## Files created or changed

- Repository safety: `.gitignore`, `.dockerignore`, `.env.example` with a blank API-key placeholder.
- Runtime: `Dockerfile`, `docker-compose.yml`.
- Reproducible dependencies: `requirements/runtime.in`, `requirements/runtime.lock`, the unmodified official `requirements/airflow-3.3.1-python3.11.constraints.txt`, and `requirements/README.md`.
- Scaffold: empty package markers in `src/` and its six approved subpackages; placeholders in `dags/`, `rag/sources/`, `tests/fixtures/`, and `docs/evidence/lineage/raw/`; local gitignored `storage/` directory.
- Runtime validation utilities: `tests/phase_a_smoke.py`, `tests/phase_a_host_audit.py`, and `tests/capture_phase_a.py`. The resumed work corrected the smoke check's plugin-manager inspection API and added selection of individual checks.
- Documentation: root `README.md` with Phase A start/stop instructions, this report, and captured output under `docs/evidence/phase_a/`.

`AGENTS.md`, `docs/rubric_matrix.md`, and `docs/preflight_report.md` remain unchanged. Runtime execution did not disprove an architectural or dependency assumption in the preflight. All 66 matrix statuses remain `NOT IMPLEMENTED`; environment readiness does not earn scored pipeline credit. The source CSV retains SHA-256 `4df640b65d3341c1e42e64be7582434aa5e19ceabfa952feb35195f8350a849c`. The repository still has no commits; no commit or publication was performed in this phase.

## Runtime results and evidence

| Check | Observed result | Captured evidence |
| --- | --- | --- |
| Image build | Approved image built successfully; all dependency pins retained | [build.log](evidence/phase_a/build.log) |
| Compose services | Exactly `airflow` and `kafka`; both running and healthy after approximately 12 hours | [service_status_final.log](evidence/phase_a/service_status_final.log), [host_audit.log](evidence/phase_a/host_audit.log) |
| Kafka | 4.2.1, single-node combined broker/controller KRaft, persistent data volume | [kafka_version.log](evidence/phase_a/kafka_version.log), [kafka_logs.log](evidence/phase_a/kafka_logs.log) |
| Airflow | 3.3.1, LocalExecutor, parallelism 1, max active runs per DAG 1, examples disabled | [airflow_version.log](evidence/phase_a/airflow_version.log), [runtime_smoke.log](evidence/phase_a/runtime_smoke.log) |
| Container Python | 3.11.15, within the approved Python 3.11 target | [runtime_smoke.log](evidence/phase_a/runtime_smoke.log) |
| Dependencies | All 195 installed versions match the frozen inventory; all required packages import | [runtime_smoke.log](evidence/phase_a/runtime_smoke.log) |
| pip check | `No broken requirements found.`; exit code 0, also passed during image build | [pip_check.log](evidence/phase_a/pip_check.log) |
| CPU-only runtime | `torch==2.14.0+cpu`; CUDA build is `None`; no NVIDIA/CUDA, Spark, Celery, or Redis distributions in the active environment | [runtime_smoke.log](evidence/phase_a/runtime_smoke.log) |
| Airflow to Kafka | Real AdminClient broker-metadata request succeeded at `kafka:29092`; broker 1 returned; no business records produced | [runtime_smoke.log](evidence/phase_a/runtime_smoke.log) |
| UI/API | Host HTTP 200 for `/` and `/api/v2/monitor/health` at localhost:8080; database, scheduler, triggerer, and DAG processor healthy | [host_audit.log](evidence/phase_a/host_audit.log) |
| SQLite | Actual `PRAGMA journal_mode` returned `wal`; database stored on Linux named volume | [runtime_smoke.log](evidence/phase_a/runtime_smoke.log) |
| OpenLineage | Provider 2.20.0 and its plugin load; no plugin import errors; namespace `aqualens2030`; FileTransport; append false | [lineage_configuration_final.log](evidence/phase_a/lineage_configuration_final.log) |
| Evidence permissions | Create/write/read/delete probe succeeded under mounted `docs/evidence/lineage/raw/`; probe removed; no event emitted | [lineage_configuration_final.log](evidence/phase_a/lineage_configuration_final.log) |
| Immutable source mount | Docker reports `RW=false`; write-open without truncation rejected with `EROFS`; host and container hashes agree | [runtime_smoke.log](evidence/phase_a/runtime_smoke.log), [host_audit.log](evidence/phase_a/host_audit.log) |
| Prohibited services | Only the two approved containers running; no ZooKeeper, Redis, Celery, Spark, Marquez, or Chroma server | [host_audit.log](evidence/phase_a/host_audit.log) |
| Scope/safety | No `.env`, no model/runtime files in `storage/`, no DAG Python files, empty source package markers only, raw lineage directory contains only `.gitkeep` | [scope_audit.json](evidence/phase_a/scope_audit.json), [gitignore.log](evidence/phase_a/gitignore.log) |

The initial `runtime_smoke.log` ends with a failed **test-inspection** check because it used removed `plugins_manager.import_errors` and `plugins_manager.plugins` attributes. The other four check groups passed. Inspection established that Airflow 3.3.1 exposes `get_import_errors()` and `get_plugin_info()` instead. Only the test was corrected, and the affected check was rerun successfully in `lineage_configuration_final.log`. The original failed output is retained rather than replaced. No library or service change was necessary.

## Runtime resources and log audit

| Observation | Airflow | Kafka |
| --- | --- | --- |
| During package-import validation | 104.43% CPU, 1.256 GiB RAM | 3.22% CPU, 378.1 MiB RAM |
| After validation, idle sample | 8.30% CPU, 1.057 GiB RAM | 2.35% CPU, 387.8 MiB RAM |
| Configured limit | 2 CPUs, 5 GiB | 1 CPU, 1 GiB |
| Restart count / OOM killed | 0 / false | 0 / false |

Docker CPU percentages are relative to one core, so 104.43% during imports is approximately one busy core and below Airflow's two-core limit. Combined idle memory was about 1.44 GiB, reasonable within Docker Desktop's approximately 7.66 GiB allocation. These are point-in-time setup observations, not pipeline-load benchmarks. See [resources_final.log](evidence/phase_a/resources_final.log) and [resources_idle.log](evidence/phase_a/resources_idle.log).

Docker's post-build inventory reported about 6.97 GB of images and 3.738 GB of build cache; these categories can share storage and should not be added as unique physical usage. Docker Desktop retains the pre-existing D:-backed storage configuration. No system configuration was changed. The host audit records exact image IDs, mount destinations, limits, and container state.

Inspected Airflow standalone/subprocess logs and Kafka logs. Airflow reported one transient triggerer scheduling-delay message (0.27 seconds versus a 0.20-second warning threshold), and Great Expectations imports logged documentation-registration messages. Kafka logged an informational controller-channel disconnection followed by continued operation and successful metadata requests. No fatal service error or persistent unhealthy state was found. There are no project DAGs or task logs yet. Credential-related log lines are visibly redacted by the capture utility; it does not manufacture success output. See [airflow_logs_final.log](evidence/phase_a/airflow_logs_final.log) and [kafka_logs_final.log](evidence/phase_a/kafka_logs_final.log).

## Commands executed

All commands below ran from `D:/Projects/aqualens-2030`. Captured commands are invoked through:

```text
python tests/capture_phase_a.py <evidence-output-path> <command-and-arguments>
```

The complete captured argument arrays, mapped to log files, are in [commands.json](evidence/phase_a/commands.json). Each captured log contains its own UTC timestamps, actual command arguments, and exit code. The initial build used PowerShell `Tee-Object`; its output was subsequently converted from UTF-16 to UTF-8 without changing the build messages.

Setup commands, executed before the resume:

```powershell
docker pull apache/airflow:3.3.1-python3.11
docker compose config --quiet
docker compose --progress plain build airflow 2>&1 | Tee-Object -FilePath docs/evidence/phase_a/build.log
docker compose pull kafka
docker compose up -d --wait --wait-timeout 180 kafka
docker compose exec -T kafka /opt/kafka/bin/kafka-topics.sh --version
docker compose logs --no-color --tail 150 kafka
docker version
docker compose version
docker system df
docker compose up -d --wait --wait-timeout 300
docker compose logs --no-color --tail 100 airflow
docker compose exec -T airflow python -m pip check
docker compose exec -T airflow airflow version
```

Resume inspection and remaining validation commands:

```powershell
git status --short
docker compose ps
docker ps --format '{{.Names}} {{.Image}} {{.Status}}'
docker compose exec -T -e HF_HUB_OFFLINE=1 airflow python /opt/airflow/tests/phase_a_smoke.py
python tests/phase_a_host_audit.py
docker stats --no-stream
docker compose logs --no-color --tail 120 airflow
docker compose logs --no-color --tail 60 kafka
docker compose exec -T airflow python -c "from airflow import plugins_manager as p; p.ensure_plugins_loaded(); print([n for n in dir(p) if 'error' in n or 'plugin' in n]); print([(x.name,type(x).__name__) for x in p.plugins])"
docker compose exec -T airflow python -c "from airflow import plugins_manager as p; p.ensure_plugins_loaded(); print('Errors:', p.get_import_errors()); print('Plugins:', p.get_plugin_info())"
docker compose exec -T airflow python /opt/airflow/tests/phase_a_smoke.py lineage_configuration
docker stats --no-stream
git diff --check
```

The first diagnostic plugin command also encounters the removed `plugins` attribute; the second confirms the supported methods and empty error set. The host-audit script executes Docker configuration, inspect, image inspect, and running-container queries, then HTTP requests and source hashing. The smoke script performs the package, broker, SQLite, provider, and permission checks documented above. Additional local inspection verified the frozen constraints hash, ignore patterns, unchanged CSV, empty scaffold, and unchanged matrix statuses; [scope_audit.json](evidence/phase_a/scope_audit.json) records those assertions.

## Final disposition

**Phase A: PASS. No unresolved Phase A environment failures.** Existing services are left running and healthy. Start/stop instructions are in the root [README](../README.md); `docker compose stop` or `docker compose down` preserves named-volume data.

Real ingestion/quarantine, Delta MERGE/schema proof, quality gates, hybrid retrieval/generation, and executed task lineage remain future phases. Account-specific Gemini access and model loading were not exercised. None is claimed as complete, and no scored rubric status was advanced. **Stop after Phase A; do not proceed to Phase B.**
