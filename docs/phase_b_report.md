# Phase B: Kafka Ingestion Boundary and Quarantine

**PASS — 09 September 2026.** The five scored Ingestion requirements, representing the rubric's 20-point category, are now demonstrated with real Kafka execution and Pydantic validation. This is evidence of requirement coverage, not a claim of a grade awarded by the evaluator. No later project phase was started.

## Files changed

Created:

- `src/common/config.py`: environment-based ingestion configuration.
- `src/ingestion/schema.py`: strict Pydantic event contract.
- `src/ingestion/kafka_io.py`: real topic creation and broker-acknowledged JSON publication.
- `src/ingestion/producer.py`: immutable CSV mapping, run IDs, and delivery manifests.
- `src/ingestion/bounded.py`: finite offset/run selection with timeout.
- `src/ingestion/consumer.py`: boundary validation, accepted staging output, and real DLQ publication.
- `src/ingestion/quarantine.py`: original payload preservation, run-ID recovery, reason, and rejection timestamp.
- `src/ingestion/verify.py`: independent Kafka DLQ read and source-value reconciliation.
- `tests/fixtures/malformed_water_event.json` and `tests/fixtures/README.md`: explicitly labeled malformed test fixture, separate from analytical data.
- `tests/test_ingestion.py` and `tests/run_phase_b_proof.py`: focused tests and real-container proof driver.
- `docs/evidence/phase_b/`: actual execution logs, run summaries, topic details, and scope/isolation audits.
- This report.

Updated `docs/rubric_matrix.md` only for demonstrated ingestion requirements and their ingestion-only evidence checklist entries. No change to AGENTS.md, dependency pins, Docker images/configuration, preflight, Phase A report, or official CSV. Existing healthy containers were reused without rebuilding or restarting.

## Topics and schema behavior

Kafka bootstrap: `kafka:29092` from the existing Airflow container, used here as the project Python runtime only. The commands were not Airflow tasks and emitted no OpenLineage events.

| Topic | Purpose | Observed configuration |
| --- | --- | --- |
| `aqualens.water.raw.v1` | Source events and the explicitly requested malformed test event | One partition, replication factor 1, leader/ISR broker 1 |
| `aqualens.water.quarantine.v1` | Rejected records and reasons | One partition, replication factor 1, leader/ISR broker 1 |

Analytical mapping is exactly `Year → year`, `Province → region`, `Source → source`, and `Value → volume_m3`. The business key remains `year + region + source`. JSON events also carry `run_id`, `event_id`, and `record_kind`; Kafka headers carry the run ID for recovery when JSON is malformed.

Pydantic validates required fields and strict types, forbids extra fields, and rejects non-JSON numeric values such as NaN/infinity. Numeric zero and negative values are accepted. There is **no nonnegative-volume rule**. Grand Total is a valid string region. The `-1` assertion is confined to tests and is not published in the official-data proof. Business-quality validation is reserved for the later Great Expectations phase.

Every DLQ payload includes original UTF-8 text, base64 of the original bytes for lossless preservation, recoverable `run_id` (or null), nonempty `rejection_reason`, UTC `rejected_at`, and raw topic/partition/offset. The consumer waits for the DLQ broker acknowledgement before counting a rejected record as handled.

## Real proof results

| Run | Unique run ID | Raw offsets, partition 0 | Produced | Accepted | Quarantined | DLQ offset |
| --- | --- | --- | --- | --- | --- | --- |
| Primary proof | `ea8464c0-722b-4c8a-a83c-252fff68ee33` | 0–56 | 57 | 56 | 1 | 0 |
| Persistent-history isolation proof | `0c7cd058-960e-47c9-a661-5f133533e617` | 57–113 | 57 | 56 | 1 | 1 |

Each run published exactly 56 real source rows plus one malformed fixture. The second run intentionally used the same persistent topics with the first run still present. Offsets and IDs are disjoint, and the second consumer did not count prior-run records. Across both demonstrations, 114 raw records were published; the required per-run result is 57/56/1.

Independent consumers read the actual DLQ messages and confirmed the original `volume_m3="not-a-number"` fixture and its Pydantic `float_type` rejection reason. No valid source record was quarantined. All accepted analytical tuples were independently reconciled against the CSV, including four Grand Total rows and 20 zero-volume rows per run.

Accepted records and manifests are staging artifacts in gitignored `storage/ingestion/<run_id>/`; they are not Bronze tables or another Lakehouse layer. The source SHA-256 before production, after production, and after independent verification remained:

`4df640b65d3341c1e42e64be7582434aa5e19ceabfa952feb35195f8350a849c`

## Bounded execution and tests

The producer records actual broker-acknowledged offsets in its run manifest. The consumer assigns the earliest required offset in each partition and reads only that finite manifest window, checking recoverable run identity and skipping unrelated/duplicate offsets. Unrecoverable metadata does not discard an expected malformed message: it still reaches boundary validation. A contradictory recovered run ID fails the command. No consumer group offset is used to infer a proof's start position.

The default read deadline is 60 seconds; topic creation and producer delivery also have finite timeouts. Missing expected records cause a nonzero exit instead of hanging. Accepted-output creation is exclusive, so an accidental replay cannot silently overwrite a prior run. This small phase does not claim transactional exactly-once recovery between Kafka and local files; use a fresh run after a failed attempt.

**Nine focused tests passed**, covering valid zero/Grand Total, malformed numeric input, negative numeric acceptance, required fields/strict types, quarantine reason/original bytes, invalid JSON run-ID recovery, old/interleaved/duplicate offsets, deadline failure, and unrecoverable run metadata. The original eight-test result is retained; the final nine-test suite includes the additional missing-metadata case. The final bounded-reader code was also used for another independent DLQ verification without producing extra records.

## Evidence and commands

| Proof | Evidence |
| --- | --- |
| Producer acknowledgements, run ID, counts, source hashes | [proof/producer.log](evidence/phase_b/proof/producer.log) |
| Accepted records and malformed rejection with DLQ acknowledgement | [proof/consumer.log](evidence/phase_b/proof/consumer.log) |
| Independent DLQ record, exact original payload and rejection reason | [proof/quarantine_verification.log](evidence/phase_b/proof/quarantine_verification.log) |
| Summary derived from those actual command results | [proof/summary.json](evidence/phase_b/proof/summary.json) |
| Second real run against persistent history | [isolation/summary.json](evidence/phase_b/isolation/summary.json) and its producer/consumer/verification logs |
| Cross-run offsets and count comparison | [isolation_audit.json](evidence/phase_b/isolation_audit.json) |
| Final independent DLQ reread | [quarantine_verification_final.log](evidence/phase_b/quarantine_verification_final.log) |
| Nine tests and printed negative-value acceptance | [unit_tests_final.log](evidence/phase_b/unit_tests_final.log) |
| Real Kafka topic listing and partition details | [topic_list.log](evidence/phase_b/topic_list.log), [topic_details.log](evidence/phase_b/topic_details.log) |
| Healthy services and inspected broker logs | [service_status.log](evidence/phase_b/service_status.log), [kafka_logs.log](evidence/phase_b/kafka_logs.log) |

Commands executed from the repository root:

```powershell
docker compose ps
docker compose exec -T airflow python -c "import pydantic,confluent_kafka; print('pydantic',pydantic.__version__); print('confluent-kafka',confluent_kafka.__version__)"
docker compose exec -T airflow python -m unittest discover -s tests -p test_ingestion.py -v
py -3.11 tests/run_phase_b_proof.py --evidence-dir docs/evidence/phase_b/proof
py -3.11 tests/run_phase_b_proof.py --evidence-dir docs/evidence/phase_b/isolation
docker compose exec -T kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:29092 --list
docker compose exec -T kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:29092 --describe
docker compose ps
docker compose logs --no-color --tail 80 kafka
docker compose exec -T airflow python -m unittest discover -s tests -p test_ingestion.py -v
docker compose exec -T airflow python -m src.ingestion.verify --manifest storage/ingestion/0c7cd058-960e-47c9-a661-5f133533e617/producer_manifest.json
git diff --check
```

Each proof driver invoked `docker compose exec -T airflow python -m src.ingestion.producer --malformed-fixture tests/fixtures/malformed_water_event.json`, then `src.ingestion.consumer --manifest <actual manifest path>` and `src.ingestion.verify --manifest <actual manifest path>`. Exact command arguments and exit codes are retained in the corresponding logs. All executed proof/test commands exited 0. Additional capture used the existing `tests/capture_phase_a.py` utility with Phase B output paths; no Phase A evidence was overwritten. [commands.json](evidence/phase_b/commands.json) indexes captured command arguments.

To reproduce, use a **new** evidence directory, for example `py -3.11 tests/run_phase_b_proof.py --evidence-dir docs/evidence/phase_b/new_run`. Do not overwrite existing proof directories. The driver generates the UUID and passes its exact manifest between commands.

Configuration is read from `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_RAW_TOPIC`, `KAFKA_QUARANTINE_TOPIC`, `WATER_SOURCE_CSV`, `INGESTION_OUTPUT_ROOT`, and `INGESTION_TIMEOUT_SECONDS`; defaults match the approved runtime and paths. No new dependency or service is required.

## Rubric update and stop condition

Advanced these five scored Ingestion rows to **VERIFIED** only after real execution: Kafka producer, Kafka consumer, boundary schema validation, quarantine routing, and recorded rejection reason. Updated their actual component/test/evidence locations. Also advanced the four corresponding ingestion-only execution-evidence checklist rows. No submission requirement or Delta, RAG, Orchestration, Quality Gate, or Lineage requirement changed status.

The log audit found the expected Pydantic rejection and no unexpected traceback, ERROR, or nonzero proof exit. Both original containers remain healthy. **Unresolved Phase B blockers: none.** No Delta write, GX validation, project DAG, OpenLineage execution, Gold, RAG, or Streamlit work was performed. The source CSV remains immutable. **Phase B is complete; stop before Phase C.**
