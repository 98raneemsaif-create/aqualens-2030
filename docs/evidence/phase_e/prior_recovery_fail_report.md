# Phase E recovery report

**FAIL — stopped after the authorized bounded Gemini retries were exhausted on 09 September 2026.** The existing `phase_e_success` run remains failed. Its eight successful tasks were preserved exactly; only `rag_grounded_answer_smoke_test` was requeued. The controlled quality-failure run was not triggered because the required full success path did not complete.

## Minimal fix and validation

Changed only application file `src/rag/generation.py`. The existing Gemini request now permits a maximum of four attempts, retrying only HTTP **429, 500, 502, 503, 504**, with delays **5, 15, 30 seconds**. HTTP 503 indicates service unavailability and is in the explicitly approved transient-status set. Permanent/model/configuration errors are immediately propagated through the existing safe exception handling.

The retry loop is inside the existing client context and around `generate_content` only. E5/CrossEncoder are not reloaded between request retries. SDK retry attempts are explicitly set to one so nested SDK retries cannot exceed the four-request bound. The retry log contains only action, model, HTTP status, attempt and retry delay (Airflow adds its normal log envelope).

Model remains **gemini-3.5-flash**, temperature remains **0**, and the explicit `GEMINI_API_KEY` Developer API client remains in use with `vertexai=False`. Grounding instructions, retrieved context, response schema and citation validation are unchanged. No model, dependency, DAG, service, or architecture change was made.

Targeted validation:

- Generation syntax/compile check: passed.
- Existing focused RAG tests: seven passed; no Phase A/B/C/D suite was run.
- Real DAG import/parse: passed for `aqualens_2030_pipeline`.
- Explicit SDK single-attempt configuration: passed.
- `git diff --check`: passed (only ordinary Windows line-ending notices).

The initial validation command used the unsupported `include_examples` argument with Airflow 3.3's `DagBag`. Only that command was corrected; the successful corrected check and original failure are both preserved. This was a validation-tool invocation issue, not a DAG regression.

## Actual recovery result

Run: **`aqualens_2030_pipeline / phase_e_success`**. DAG state: **failed**.

| Task | Final state | Airflow try number |
| --- | --- | ---: |
| produce_events | success | 1 |
| consume_and_validate | success | 1 |
| bronze_load | success | 1 |
| silver_merge | success | 1 |
| schema_enforcement_proof | success | 1 |
| quality_gate | success | 1 |
| gold_build | success | 1 |
| rag_chunk_and_index | success | 1 |
| rag_grounded_answer_smoke_test | failed | 3 |

The before/after audit compares all eight successful task records, including try numbers and start/end timestamps: they are identical. None reran. The DAG was requeued through Airflow's supported `clear_task_instances` API, selecting exactly the one failed task for the existing run; no new success run was triggered.

The recovered final task ran from 15:28:31.365772 to 15:30:35.554965 UTC. Inside this single Airflow attempt:

| Gemini request attempt | Actual status | Following delay |
| --- | ---: | ---: |
| 1 | 503 | 5 seconds |
| 2 | 503 | 15 seconds |
| 3 | 503 | 30 seconds |
| 4 | 503 | None; task failed |

The terminal safe error is `RuntimeError: Gemini execution failed; HTTP status 503`. No final grounded answer or task-success result was produced in this recovery. Previous Phase D PASS evidence remains authoritative and unchanged; this is a failure of the current Phase E service call.

## Great Expectations and controlled failure path

The existing success-run GX result remains successful for 56 Silver rows at `storage/delta/airflow/be770adc-2479-456e-aa2f-2715eac4f484/silver`. Its actual result is [success_be770adc-2479-456e-aa2f-2715eac4f484.json](evidence/quality/success_be770adc-2479-456e-aa2f-2715eac4f484.json).

The existing negative-volume fixture and GX implementation were inspected and not modified. The DAG already accepts `quality_failure_demo=true`; the fixture has numeric `volume_m3=-1.0`. The focused GX tests reported in the handoff were not unnecessarily rerun.

**No `phase_e_quality_failure` run was triggered.** The user explicitly requires successful completion of the existing success run first, and requires stopping if bounded Gemini retries still fail. Therefore no quality-failure DAG state, negative-volume GX failure within that DAG, or downstream `upstream_failed` evidence is claimed by this recovery. Those integration proofs remain outstanding.

## Real OpenLineage evidence

Derived summaries read only actual FileTransport files and filter by the Airflow run ID in emitted facets. No event was manufactured or removed.

For `phase_e_success`, task-stage events across all attempts are:

- **11 START**: eight successful stages plus three attempts of the final RAG task.
- **8 COMPLETE**: the eight successful stages.
- **3 FAIL**: the three failed RAG task attempts, including the new bounded-retry attempt.

Including DAG-level events, totals are 14 START, 8 COMPLETE and 6 FAIL. These totals must not be mistaken for nine successfully completed stages. Event file paths, timestamps, attempt numbers and OpenLineage run IDs are retained in [lineage summary](evidence/phase_e/lineage_recovery/summary.json), with derived START/COMPLETE/FAIL JSONL files beside it. Prior attempt-1/2 START/FAIL events remain intact. No controlled-quality-failure event or event for an unexecuted downstream stage is claimed.

## Evidence and commands

New evidence lives under `docs/evidence/phase_e/`:

- `before_recovery/`: original task states and copied task logs, including both earlier 503 attempts.
- `after_recovery/`: final task/DAG states and all existing task logs, including attempt 3.
- `recovery_audit.json`: unchanged upstream records and exact four-request status history.
- `targeted_checks.log`, `targeted_checks_corrected.log`, `targeted_final.log`, `rag_focused_tests.log`: validation outcomes and exit codes.
- `before_recovery.log`, `clear_final_task.log`, `after_recovery.log`: supported recovery commands and actual states.
- `lineage_recovery.log`, `lineage_recovery/`: actual emitted-event correlation.
- `service_status.log`: both existing containers healthy; neither rebuilt nor recreated.

Captured commands use the existing `tests/capture_phase_a.py` wrapper, with `$env:PYTHONIOENCODING='utf-8'`. Each log records command arguments, timestamps and exit code. Key commands:

```powershell
docker compose exec -T airflow airflow tasks states-for-dag-run aqualens_2030_pipeline phase_e_success --output json
docker compose exec -T airflow python -m unittest discover -s tests -p test_rag.py -v
docker compose exec -T airflow python tests/phase_e_recovery.py capture --label before_recovery
docker compose exec -T airflow python tests/phase_e_recovery.py clear
docker compose exec -T airflow python tests/phase_e_recovery.py capture --label after_recovery
docker compose exec -T airflow python tests/summarize_phase_e_lineage.py phase_e_success docs/evidence/phase_e/lineage_recovery
docker compose ps -a
git diff --check
```

Additional read-only checks inspected the actual failed logs, installed SDK retry configuration, current code and DAG parsing. The log-capture helper refuses to copy a task log containing either configured API key. Neither credential was printed or included in retry logs.

## Files and rubric scope

This recovery modified `src/rag/generation.py` and added `tests/phase_e_recovery.py`, `tests/summarize_phase_e_lineage.py`, this report, and the new evidence above. The helpers inspect/capture existing runs and derive lineage; they do not replace Airflow or emit synthetic events. The failure-trigger helper uses a subprocess argument list for JSON-safe invocation but was not executed.

Pre-existing staged Phase E DAG, ingestion fixture support, GX gate and tests were preserved. AGENTS.md, Phase D report/evidence, existing VERIFIED Ingestion/Delta/RAG rows, source CSV, and prior Phase B/C evidence were not changed. No commit was created.

**Rubric rows advanced: none.** Full orchestration success and controlled downstream-blocking evidence are still incomplete. Real partial lineage and GX success are recorded without claiming the entire Phase E objective.

## Unresolved issue and stop

Gemini 3.5 Flash returned HTTP 503 on all four authorized requests. Recovery requires a later successful service call; no further task clear, model substitution, architecture change, or automatic retry was attempted. Both Phase E PASS conditions remain unfulfilled as a pair: the nine-task success path has not completed, and the controlled GX failure path has not yet been run. **Phase E: FAIL. Stopped before Phase F and submission cleanup.**
