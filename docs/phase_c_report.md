# Phase C — Real Delta Lakehouse

**PASS — executed on 09 September 2026 using deltalake 1.6.3 in the existing Python 3.11 container.** All six integration tests passed. Phase C demonstrates the six component rows of the 25-point Delta category; final rubric credit remains subject to evaluation. No Phase D work was started.

## Input and execution

The deterministically selected input is the first successful Phase B proof run, `ea8464c0-722b-4c8a-a83c-252fff68ee33`, at `storage/ingestion/ea8464c0-722b-4c8a-a83c-252fff68ee33/accepted.jsonl`. Its successful consumer result and all input run IDs were checked. Exactly 56 accepted source observations were used; the second Phase B run was not combined with it. Accepted-file SHA-256: `4f3889080602b4616e2dfc61e5f92ce58f358033e051982570a98e905720d29a`.

The successful proof root is `storage/delta/proofs/phase_c/5f9e3c82-8804-4488-b183-f885a650c017/`. Every test execution creates a new UUID directory with `exist_ok=False`, so reruns cannot inflate the primary Bronze count. Generated tables remain gitignored. The modules take explicit paths; no environment variables or additional dependencies are required for this phase.

Transformation flow is accepted JSONL → Bronze Delta → Silver Delta → Gold Delta. Only the independent provenance test reads the immutable official CSV.

## Demonstrated results

| Requirement | Actual result |
| --- | --- |
| Bronze | Real Delta log, schema, history, and 56 rows; all accepted fields and metadata preserved. `delta.appendOnly=true`; loader always appends. An isolated second-append test proves 56 → 112 with both copies preserved; primary Bronze remains 56. |
| Silver | Empty typed Delta initialization followed by the normal real `DeltaTable.merge` loader. First MERGE inserts 56; replay inserts zero and leaves 56 unique `year + region + source` keys. Both MERGE histories and metrics captured. |
| Update/insert and deduplication | Separate labeled test fixtures prove one existing-key update, two inserts, and collapse of an identical duplicate. Conflicting volumes within a Bronze batch raise explicitly; identical observations retain metadata chosen deterministically by run/event ID. No fixtures enter official proof tables. |
| Schema enforcement | Actual Delta exception: `Cast error: Cannot cast string 'not-a-number' to value of Float64 type`. Invalid string Arrow data reaches the writer with no schema evolution. Isolated table version remains 0, count remains 56, and schema remains identical. Unrelated exceptions are re-raised. |
| Gold | Real Delta table named `gold_regional_water_profile`, 13 unique year/region rows, derived only from Silver. All profiles are captured and independently checked using Decimal arithmetic. |
| Grand Total and zeros | All four Grand Total observations and all 20 zero-volume observations remain in Bronze and Silver. Gold excludes Grand Total only. |
| Source integrity | Silver analytical tuples match both accepted staging and an independent read of the official CSV. CSV SHA-256 remains `4df640b65d3341c1e42e64be7582434aa5e19ceabfa952feb35195f8350a849c`. |

Gold provides `year`, `region`, `total_water_volume_m3`, `dominant_source`, `dominant_source_volume_m3`, `dominant_source_share_pct`, and `active_source_count`. Total is the sum of source volumes; dominant is maximum volume with source-name ascending tie-breaking; share is dominant/total × 100; active count includes strictly positive volumes. An isolated tie/zero test confirms the tie-break and positive-count behavior. A zero-total group would have a null share (undefined division); all official regional totals are positive. Gold is a replaceable derived snapshot; Bronze is append-only and Silver uses MERGE.

This is Water Source Concentration, with no risk classes, thresholds, forecasts, or inferred explanations.

## Source provenance observations

These are reported as supplied, without correction or a national-total quality gate:

| Source | Regional sum m³ | Supplied Grand Total m³ | Difference m³ |
| --- | ---: | ---: | ---: |
| Desalinated water (SWCC) | 2,767,383,011 | 2,767,383,012 | -1 |
| Groundwater | 907,363,749 | 907,363,749 | 0 |
| Surface water | 32,809,799 | 32,809,800 | -1 |
| Other sources | 10,981,765 | 10,981,765 | 0 |

## Evidence and commands

- [Successful execution log](evidence/phase_c/execution_final.log): six tests, actual schema exception, timestamps, command arguments, exit code 0.
- [Successful results](evidence/phase_c/5f9e3c82-8804-4488-b183-f885a650c017/results.json): selected input, actual Delta versions/schemas/log filenames/history, MERGE metrics, schema before/after, all Gold profiles, independent checks, and provenance.
- [Original failed execution](evidence/phase_c/execution.log) and [partial results](evidence/phase_c/ccf12138-71d7-4352-b417-42891742af09/results.json) are retained. The initial run found that `is_deltatable` needs a string path and this writer raises a general cast exception rather than `SchemaMismatchError`. Corrected API handling and deprecated schema serialization, then reran in fresh storage. No runtime change was necessary.
- [Service status](evidence/phase_c/service_status.log): both existing services remain healthy; no rebuild or restart.
- [Scope audit](evidence/phase_c/scope_audit.json): changed-file inventory, source/code hashes, protected-file checks, and matrix scope.

From the repository root, successful execution used:

```powershell
python tests/capture_phase_a.py docs/evidence/phase_c/execution_final.log docker compose exec -T airflow python -m unittest discover -s tests -p test_lakehouse.py -v
python tests/capture_phase_a.py docs/evidence/phase_c/service_status.log docker compose ps
git diff --check
```

To reproduce without overwriting curated evidence, use a new log filename with the same unittest command. Each run automatically selects the same Phase B artifact and creates fresh table and JSON evidence directories. The isolated schema rejection is the explicit failure-demo path, executed by `test_03_schema_rejection`; its test passes only after actual rejection and unchanged-state verification. Existing Phase B artifacts are prerequisites. Initial inspection also ran `git status --short`, read the authoritative documents/PDF, and inspected installed Delta signatures and `docker compose ps`.

## Exact files changed

Created:

- `src/lakehouse/bronze.py`
- `src/lakehouse/silver.py`
- `src/lakehouse/gold.py`
- `src/lakehouse/schema_proof.py`
- `tests/test_lakehouse.py`
- `docs/phase_c_report.md`
- `docs/evidence/phase_c/execution.log`
- `docs/evidence/phase_c/execution_final.log`
- `docs/evidence/phase_c/service_status.log`
- `docs/evidence/phase_c/scope_audit.json`
- `docs/evidence/phase_c/ccf12138-71d7-4352-b417-42891742af09/results.json`
- `docs/evidence/phase_c/5f9e3c82-8804-4488-b183-f885a650c017/results.json`

Modified only `docs/rubric_matrix.md`: six scored Delta component rows and four corresponding Delta execution-evidence rows advanced to VERIFIED with actual evidence paths. All other rows retain their prior status. Runtime Delta files are generated under the two isolated proof roots above, not contributor files.

## Remaining issues and boundary

No unresolved Phase C execution failure or architecture change. The first failed proof is explicitly superseded by the successful fresh run. Tests run directly in the existing container; they do not establish Airflow orchestration or quality-gate credit. AGENTS.md, the source CSV, Phase B evidence, runtime configuration, and dependencies were not changed. No commit was created. Great Expectations, project DAG, OpenLineage execution, RAG, Gemini, and UI work remain outside this phase. **Stop after Phase C.**
