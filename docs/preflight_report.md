# AquaLens 2030 Pre-flight Report

Validation date: 08 September 2026. Scope: documentation, read-only environment/data inspection, official-source research, package metadata resolution, and inspection of selected library source. Read [AGENTS.md](../AGENTS.md), both pages of the [Capstone Rubric](reference/Capstone%20Rubric%20-%20Modern%20Data%20Engineering%20for%20AI%20Systems.pdf), and [rubric_matrix.md](rubric_matrix.md).

**Finding: the approved architecture is feasible and has a dependency-compatible Python 3.11 plan.** The dataset needs explicit national-total handling, and the final RAG task must include generation and citations. The decisions below resolve these planning details without replacing any approved technology.

No application code, DAG, Docker configuration, source snapshot, or pipeline component was created. No source data, repository guide, or rubric status was changed. No project dependencies, images, or model weights were installed/downloaded. Only `uv==0.12.10` was installed as isolated temporary validation tooling under `%TEMP%/aqualens-preflight/tooling/`; the previously available temporary PDF reader was reused. Package metadata, constraints, small library archives, model configuration files, and image manifests were examined without installing the stack. Preflight is not scored implementation evidence.

## 1. Local environment

Read-only commands included `Get-CimInstance Win32_OperatingSystem`, `py -0p`, version commands, `docker info`, `docker system df`, `docker manifest inspect`, logical-disk inspection, `wsl --list --verbose`, and Git status/root/history inspection.

| Item | Observed result |
| --- | --- |
| OS | Microsoft Windows 11 Home, 64-bit, version/build `10.0.26200` |
| Repository root | `D:/Projects/aqualens-2030` |
| Python 3.11 | `3.11.9`, `C:/Users/HUAWEI/AppData/Local/Programs/Python/Python311/python.exe` |
| Other registered Python installations | `3.12.0` at `C:/Users/HUAWEI/AppData/Local/Programs/Python/Python312/python.exe`; `3.8.2` at `C:/Program Files/Python38/python.exe` |
| Python launcher default outside sandbox | Python 3.12; use `py -3.11` explicitly for host validation |
| Git | `2.55.0.windows.3` |
| Git status | Branch `main` has no commits. `AGENTS.md`, `data/`, and `docs/` were untracked at inspection. Git repository root is correct; publication is not established by this check |
| Docker CLI | `29.7.2`, build `a7dcaa6` |
| Docker Compose | `v5.5.1` |
| Docker server | Running, version `29.7.2`, Docker Desktop, Linux containers; inspected local image reports `linux/amd64` |
| WSL | `docker-desktop` running under WSL 2 |
| Docker resources | 8 CPUs; `8,220,442,624` bytes memory, approximately 7.66 GiB |
| Host RAM | `16,571,704` KiB total, approximately 15.8 GiB; free physical memory at observation about 3.2 GiB |
| C: volume | `128,849,014,784` bytes total; `14,750,212,096` bytes free at initial host check, approximately 13.7 GiB |
| D: volume | `362,095,308,800` bytes total; `334,189,137,920` bytes free, approximately 311.2 GiB |
| Docker storage | Engine reports `/var/lib/docker`; Docker Desktop configuration points to `D:/DockerData/DockerDesktopWSL` |
| Docker disk files | `disk/docker_data.vhdx`: `2,422,210,560` bytes; `main/ext4.vhdx`: `100,663,296` bytes |
| Existing Docker usage | 1 image, 1 stopped container, 0 local volumes, no build cache; no AquaLens services were started |

The sandbox initially exposed only Python 3.8 and denied Docker access. Read-only host checks outside the sandbox established the actual results above. Those first errors were access restrictions, not evidence that Python 3.11 or Docker was absent. One later automatic approval review timed out; its retry succeeded. No system-wide setting was changed.

The backing D: drive has ample physical headroom for this project. WSL `df` exposed the small Docker system root and host drives, not the engine data filesystem's internal free-block count. Do not mistake the 53.8 MiB free on that system root for the capacity of `docker_data.vhdx`. The data disk's internal capacity/quota was not independently measured. Keep runtime volumes and model caches on D:; allow roughly 10–20 GiB for image builds, package caches, models, and runtime data as a planning allowance, not a measured final footprint. Use CPU inference, one active DAG run, and low task concurrency because RAM is more constrained than disk.

## 2. Python/runtime decision

Retain **Python 3.11**. Airflow 3.3.1 documents support for it, and the selected package metadata and Linux-target resolver accept it. Airflow should run inside the Linux Docker image, not native Windows Python. The host's default Python version does not determine the container runtime. [Airflow 3.3.1 quick start](https://airflow.apache.org/docs/apache-airflow/3.3.1/start.html)

Package metadata declares these Python ranges: Airflow `>=3.10,!=3.15`; OpenLineage provider/client `>=3.10`; Great Expectations `>=3.10,<3.14`; deltalake `>=3.10`; confluent-kafka `>=3.8`; Pydantic and ChromaDB `>=3.9`; sentence-transformers, torch, transformers, and google-genai `>=3.10`. All include 3.11. `rank-bm25` has no declared `Requires-Python` bound; its pure-Python distribution and NumPy dependency resolve on the target. This is metadata compatibility, not a claim of executed imports or model inference. Version-specific package metadata is available through each [PyPI JSON endpoint](https://pypi.org/pypi/apache-airflow/3.3.1/json), using the package/version pairs below.

## 3. Dependency compatibility and pinned plan

Use the official [Airflow 3.3.1 Python 3.11 constraints](https://raw.githubusercontent.com/apache/airflow/constraints-3.3.1/constraints-3.11.txt), retrieved successfully. SHA-256 of retrieved bytes:

`9fe2d4a54b8ac8450f63ffce0b195de8d9027ddc21bc40653b62be91a63fa366`

Constraints are a compatibility input, not a list of packages to install. Do not install every provider in that file, and do not copy a Celery-based quick-start example. Keep `apache-airflow==3.3.1` explicit whenever extending the Airflow image. Apply the official constraints to Airflow/provider installation and to the combined project dependency resolution.

| Package | Selected pin | Basis |
| --- | --- | --- |
| apache-airflow | 3.3.1 | Fixed project decision; PyPI release and image manifest available |
| apache-airflow-providers-openlineage | 2.20.0 | Official constraints |
| openlineage-python | 1.52.0 | Official constraints and provider requirement |
| openlineage-integration-common | 1.52.0 | Provider dependency in official constraints |
| great-expectations | 1.22.0 | Published release; combined resolution succeeds |
| deltalake | 1.6.3 | Published release; combined resolution succeeds |
| confluent-kafka | 2.15.0 | Official constraints |
| pydantic | 2.13.4 | Official constraints |
| chromadb | 1.5.9 | Published release; combined resolution succeeds |
| sentence-transformers | 6.0.1 | Published release; supports both model interfaces |
| rank-bm25 | 0.2.2 | Published release; combined resolution succeeds |
| google-genai | 2.17.0 | Official constraints |
| torch | 2.14.0+cpu | Official PyTorch CPU distribution; avoid default CUDA dependency set |
| transformers | 5.16.1 | Meets sentence-transformers `>=5,<6` requirement |
| sentencepiece | 0.2.1 | Explicit tokenizer support for selected multilingual models |
| tokenizers | 0.23.1 | Satisfies transformers range `>=0.23.1,<0.24` |
| huggingface-hub | 1.27.0 | Meets both model-library requirements |
| safetensors | 0.8.0 | Model weight format dependency |
| pyarrow | 25.0.0 | Official constraints; explicit Delta/Arrow conversion support |
| numpy | 2.4.6 | Official constraints |
| pandas | 3.0.5 | Official constraints; quality validation/data conversion only, not a Delta substitute |
| protobuf | 6.33.6 | Official constraints; common Chroma/telemetry dependency |
| opentelemetry-api / opentelemetry-sdk | 1.44.0 / 1.44.0 | Consistent official constraints across Airflow and Chroma |

Validation used `uv pip compile`, targeting `--python-version 3.11 --python-platform x86_64-unknown-linux-gnu`, with the official constraints. The first resolution succeeded but selected CUDA dependencies through default PyTorch. Repeating with `--torch-backend cpu` removed that unnecessary footprint. The final run, including PyArrow, resolved **195 packages** without a declared dependency conflict. No packages from this resolved stack were installed. A nonfatal warning normalized a legacy quoted version specifier; resolution still exited successfully.

Reproducible resolver shape, to be run using temporary input containing the package pins above (this is documentation, not a created requirements file):

```text
uv pip compile requirements.in --constraint constraints-3.11.txt --python-version 3.11 --python-platform x86_64-unknown-linux-gnu --torch-backend cpu --output-file resolved-cpu.txt --no-header --no-annotate
```

Use PyPI for ordinary packages and the [official PyTorch CPU index](https://download.pytorch.org/whl/cpu) specifically for the CPU torch build. Do not rely on a bare version-only lock to remember the CPU package source. The final temporary lock SHA-256 is `0e60073c50a85906671c7b31cb7cacf1b1bfdd087225fa733ec25365e5a0081f`; its package listing is preserved below for review. During Phase A, create the actual lock/install inputs, retain the official constraints, and verify the built image with imports and dependency checks. Metadata resolution cannot establish ABI compatibility, working Great Expectations APIs, or successful end-to-end execution.

## 4. Minimal Docker architecture

Use two Compose services: Kafka and one local Airflow standalone service. No ZooKeeper, Redis, Celery, Spark, Marquez, or Chroma server is needed.

- **Kafka:** official `apache/kafka:4.2.1`, JVM image, one KRaft node combining broker/controller roles for this local capstone. Set node/cluster identity, controller listener/quorum configuration, internal advertised broker address reachable by Airflow, and single-node replication settings. Retain broker storage in a named volume. This is real Kafka; KRaft removes ZooKeeper. [Apache Kafka Docker instructions](https://kafka.apache.org/42/getting-started/docker/), [KRaft operations](https://kafka.apache.org/42/operations/kraft/)
- **Airflow:** extend official `apache/airflow:3.3.1-python3.11`, using constrained dependencies. Run `airflow standalone` for the local demonstration: its real scheduler, API server, DAG processor, and supporting components run in the service. Use `LocalExecutor`, `parallelism=1`, `max_active_runs=1`, no example DAGs, and SQLite in its supported local WAL configuration, on a Linux named volume rather than a Windows-bound database file. Airflow 3.3.1 supports this local setup; do not import an older assumption that LocalExecutor always requires PostgreSQL. This is a development deployment, not a production proposal. [Standalone quick start](https://airflow.apache.org/docs/apache-airflow/3.3.1/start.html), [3.3.1 release notes](https://airflow.apache.org/docs/apache-airflow/3.3.1/release_notes.html), [LocalExecutor](https://airflow.apache.org/docs/apache-airflow/3.3.1/core-concepts/executor/local.html)

Both image manifests were fetched without pulling images. Linux/amd64 platform manifest digests:

| Image | Platform digest |
| --- | --- |
| `apache/airflow:3.3.1-python3.11` | `sha256:efff0a36fb367437fb45ae61f1139fce2a0df255ca9d4ef357e02783e845170f` |
| `apache/kafka:4.2.1` | `sha256:2d2f77837385f202b1947fc3ed62421de344f0ced47dde360ca5afdad11b51fa` |

Bind the source data read-only. Use `storage/` for Delta, persistent Chroma, and model cache; keep it gitignored. Use named volumes for Kafka and Airflow internal state, backed by the existing D: Docker data disk. RAG runs in-process in Airflow tasks and through the CLI; serialize Chroma writes. Model downloads and library imports must happen during setup/task execution, not DAG parsing. Start with a small Kafka heap, for example 512 MiB, and bounded CPU thread counts. Actual container memory usage remains a Phase A runtime check.

## 5. Analytical dataset inspection

File: `data/source/water_distribution_urban_saudi.csv`. Read-only inspection used Python's standard CSV parser, decimal parsing, duplicate counting, and SHA-256 hashing.

| Property | Result |
| --- | --- |
| Size | 2,577 bytes |
| SHA-256 | `4df640b65d3341c1e42e64be7582434aa5e19ceabfa952feb35195f8350a849c` |
| Encoding | All bytes are ASCII; valid UTF-8, no BOM. The original producer's encoding label cannot be uniquely inferred from ASCII-only bytes |
| Delimiter | Comma |
| Exact columns, in order | `Province ID`, `Province`, `Source ID`, `Source`, `Year`, `Value` |
| Data rows | 56, excluding header |
| Blank/null cells | 0 in each of the six columns; no failed numeric parses |
| Unique years | `2024` only |
| Province values | 14: 13 actual regions plus `Grand Total` |
| Water-source values | 4 |
| Minimum/maximum Value, all rows | `0.0` / `2767383012.0` |
| Minimum/maximum Value, regional rows only | `0.0` / `865255663.0` |
| Exact duplicate rows | 0 |
| Duplicate excess rows on Year + Province + Source | 0; 56 distinct keys |

Inferred types: `Province ID`, `Source ID`, and `Year` are integers; `Province` and `Source` are strings; `Value` is decimal numeric, serialized with `.0` in this snapshot. IDs are identifiers even though they parse as integers. All observed volumes are finite, nonnegative, and whole-valued; preserve numeric precision rather than deriving significance from the `.0` formatting.

Exact province values: `Al-Riyadh`, `Makkah Al-Mokarramah`, `Al-Madinah Al-Monawarah`, `Al-Qaseem`, `Eastern Region`, `Aseer`, `Tabouk`, `Hail`, `Northern Borders`, `Jazan`, `Najran`, `Al-Baha`, `Al-Jouf`, `Grand Total`. Province IDs are `1` through `13`, plus `15` for Grand Total.

Exact source values: `Desalinated water (SWCC)`, `Groundwater`, `Surface water`, `Other sources`, with IDs `1`, `2`, `3`, `4` respectively.

| Canonical field | Exact source mapping | Treatment |
| --- | --- | --- |
| `year` | `Year` | Parse integer; no date extrapolation |
| `region` | `Province` | Preserve source spelling; separately identify the total sentinel |
| `source` | `Source` | Preserve source label |
| `volume_m3` | `Value` | Parse numeric directly, scale factor 1 |

The official DataSaudi catalog identifies the exact dataset as **Water Distribution in Urban Sector by Source - Annual**, sourced from GASTAT, with the metric **Volume of water (m³)**. This supports direct mapping without a million-to-unit conversion. The CSV has no unit column, so consistency is supported by the dataset-level declaration and uniform numeric representation, not an independent row-level unit audit. [DataSaudi dataset catalog](https://datasaudi.sa/en/data-explorer/datasets)

The business key is unique and requires no correction. Preserve all 56 source records in Bronze; retain the four national totals in Silver as source observations, but exclude `Province ID=15` / `region=Grand Total` from regional Gold aggregation. This produces 13 regional profiles from 52 regional source rows. Total rows are valid data, not quarantine records. This is a filtering rule, not a change of dataset or business key.

There are small reconciliation differences already present in the source:

| Source | Sum of 13 regions | Supplied Grand Total | Regional sum minus total |
| --- | --- | --- | --- |
| Desalinated water (SWCC) | 2,767,383,011 | 2,767,383,012 | -1 |
| Groundwater | 907,363,749 | 907,363,749 | 0 |
| Surface water | 32,809,799 | 32,809,800 | -1 |
| Other sources | 10,981,765 | 10,981,765 | 0 |

Do not silently repair these values or claim rounding caused the differences; the cause is undocumented. Use regional Silver rows as the Gold reconciliation basis. Report differences from supplied national totals as provenance observations, not a mandatory exact-equality gate or an invented tolerance. Gate on structural/domain validity and key uniqueness. Zero volume is valid; define active sources as volume greater than zero. Keep the approved key and original file unchanged. One year is sufficient for rubric aggregates and MERGE proof; use isolated update/insert fixtures to demonstrate MERGE without inventing analytical history.

## 6. Official RAG source readiness

No local snapshot files were found under `rag/`; this is expected before snapshot creation and does not mean the sources are unavailable.

| Source | Verified official availability and language | Text/citations | Simplest faithful snapshot plan |
| --- | --- | --- | --- |
| National Water Strategy 2030 — MEWA | The [official Arabic page](https://www.mewa.gov.sa/ar/Ministry/Agencies/TheWaterAgency/Topics/Pages/Strategy.aspx) links to the downloadable [الاستراتيجية الوطنية للمياه ٢٠٣٠.pdf](https://www.mewa.gov.sa/ar/Ministry/Agencies/TheWaterAgency/Topics/PublishingImages/Pages/Strategy/%D8%A7%D9%84%D8%A7%D8%B3%D8%AA%D8%B1%D8%A7%D8%AA%D9%8A%D8%AC%D9%8A%D8%A9%20%D8%A7%D9%84%D9%88%D8%B7%D9%86%D9%8A%D8%A9%20%D9%84%D9%84%D9%85%D9%8A%D8%A7%D9%87%20%D9%A2%D9%A0%D9%A3%D9%A0.pdf) | Use the complete official Arabic PDF as the primary MEWA RAG document for page-aware chunking and citations; retain physical PDF page indices and printed page/section labels during extraction | Preserve original PDF bytes plus deterministic per-page UTF-8 text or JSONL; keep the official MEWA webpage as provenance/fallback metadata |
| Methodology and Quality Report of Water Accounts — GASTAT | [Official English PDF](https://www.stats.gov.sa/documents/20117/2435133/Methodology%2Band%2BQuality%2BReport%2Bof%2BWater%2BAccounts_EN.pdf/223b46cb-b870-b8dd-0c0d-a732f295f600), 20 pages, accessible and text-bearing | Extractable English text, numbered sections, contents, and printed page numbers; retain physical PDF page index as well | Preserve original PDF bytes plus deterministic per-page UTF-8 text or JSONL; cite page and section |

Preserve title, issuing organization, canonical URL, retrieval timestamp, language, content hash, source format, heading/paragraph or page identity, and later chunk ID. Include publication/update date only when actually present; never substitute the retrieval date. Keep snapshots faithful, removing navigation only by deterministic extraction and retaining the raw original. Do not rewrite passages or use AI summaries as the knowledge base. The primary MEWA snapshot must contain faithful text from the official Arabic strategy PDF, with page-aware citation metadata; retain the official webpage as provenance/fallback metadata. Both sources satisfy the approved official-source restriction.

The GASTAT report discusses multiple unit families and historical coverage; it supplies methodological context, not a license to rescale this CSV or imply that its publication-specific time coverage describes the 2024 snapshot. Preserve that distinction in prompts and citations. [GASTAT report, sections 3.8 and 4](https://www.stats.gov.sa/documents/20117/2435133/Methodology%2Band%2BQuality%2BReport%2Bof%2BWater%2BAccounts_EN.pdf/223b46cb-b870-b8dd-0c0d-a732f295f600)

## 7. Embedding and reranking models

AGENTS.md specified model families, not exact IDs. Select these compact multilingual models; model API metadata and small configuration files were retrieved, with no authentication and no weight downloads:

| Role | Exact model ID / revision | Readiness and approximate storage |
| --- | --- | --- |
| Embedding | `intfloat/multilingual-e5-small` at `614241f622f53c4eeff9890bdc4f31cfecc418b3` | Public, ungated; Arabic `ar` explicitly listed; 384-dimensional embeddings; `model.safetensors` is 470,641,600 bytes |
| Cross-encoder | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` at `1427fd652930e4ba29e8149678df786c240d8825` | Public, ungated; Arabic `ar` explicitly listed; query/passage relevance scoring; `model.safetensors` is 470,592,698 bytes |

Use `SentenceTransformer` for embeddings and `CrossEncoder` for reranking with the resolved sentence-transformers/transformers/torch stack. The model configurations identify supported BERT/XLM-RoBERTa families and XLM-R tokenization; include SentencePiece. E5 requires its documented `query: ` and `passage: ` prefixes, including for non-English text, and normalized embeddings for the intended similarity setup. Bound chunks to the tokenizer's supported length. [E5 model card](https://huggingface.co/intfloat/multilingual-e5-small), [cross-encoder model card](https://huggingface.co/cross-encoder/mmarco-mMiniLMv2-L12-H384-v1)

Each model adds approximately 22 MB of tokenizer files to approximately 471 MB of weights: budget about 0.5 GB per model, or approximately 1 GB combined. Allow 1.2–1.5 GB cache headroom; Python libraries and Docker layers are additional. Download only the chosen safetensors representation, not duplicate `.bin`, ONNX, and OpenVINO copies. Pin revisions and place cache in gitignored D:-backed storage. Public accessibility and dependency resolution are established; Arabic retrieval quality and actual loading remain implementation smoke tests, not preflight claims.

## 8. Gemini readiness

Use model ID **`gemini-2.5-flash`**, package **`google-genai==2.17.0`**, and project environment variable **`GEMINI_API_KEY`**. The SDK supports this model family; Google's current model/deprecation pages list the stable model with no announced shutdown date. Do not substitute a retired preview ID. [Gemini 2.5 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash), [deprecation schedule](https://ai.google.dev/gemini-api/docs/deprecations)

An API key and eligible project/quota are required before real RAG generation. The SDK can also read `GOOGLE_API_KEY`, which takes precedence if both variables are present; configure one unambiguous project key. No key was requested, printed, or tested, and no authenticated generation request was made. Public API availability is verified; this user's account access/quota is not. Provisioning credentials privately is a runtime prerequisite, not an instruction to expose them in this report. [Google API-key documentation](https://ai.google.dev/gemini-api/docs/api-key)

## 9. OpenLineage design validation

**A pipeline stage for rubric purposes corresponds to an Airflow task representing that stage.** Functions inside a combined task do not become separate lineage stages merely because they have separate module names.

Select `apache-airflow-providers-openlineage==2.20.0` with `openlineage-python==1.52.0`. The provider requires Airflow `>=2.11.0` and the selected client/common versions; it is also pinned by the official 3.3.1 constraints. [Provider requirements](https://airflow.apache.org/docs/apache-airflow-providers-openlineage/2.20.0/index.html)

The published wheel source was inspected without installation: `plugins/listener.py` has task-running, task-success, and task-failed hooks, including the Airflow 3 runtime-task path; `plugins/adapter.py` constructs real `RunState.START`, `RunState.COMPLETE`, and `RunState.FAIL` events. The client `transport/file.py` implements supported file capture and serialization. These are library capabilities, not executed AquaLens event evidence. [Provider package](https://pypi.org/project/apache-airflow-providers-openlineage/2.20.0/), [client package](https://pypi.org/project/openlineage-python/1.52.0/)

Select **FileTransport**, with one JSON file per event (`append=false`), avoiding shared JSONL append races across scheduler/task processes. No collector server or Marquez is needed. The client appends a timestamp to the configured filename prefix. [OpenLineage transport documentation](https://openlineage.io/docs/client/python/configuration/)

Planned configuration values, not installed configuration:

```text
AIRFLOW__OPENLINEAGE__DISABLED=false
AIRFLOW__OPENLINEAGE__NAMESPACE=aqualens2030
AIRFLOW__OPENLINEAGE__TRANSPORT={"type":"file","log_file_path":"/opt/airflow/docs/evidence/lineage/raw/event","append":false}
AIRFLOW__OPENLINEAGE__EXECUTE_IN_THREAD=true
AIRFLOW__OPENLINEAGE__EMISSION_POLICY=[]
```

The provider supports JSON transport configuration and thread-based task-event emission. Keep the provider enabled in all standalone processes, with no task/DAG opt-out. [Provider configuration](https://airflow.apache.org/docs/apache-airflow-providers-openlineage/2.20.0/configurations-ref.html)

Evidence capture contract:

1. Create and bind-mount writable `docs/evidence/lineage/raw/` before running the DAG. Check permissions for the Airflow container user.
2. Let the provider/client write untouched `event-<timestamp>.json` payloads. Preserve raw events and the associated Airflow task logs.
3. For each demonstration, inventory raw filenames and run IDs in `docs/evidence/lineage/manifest.json`. Separate DAG-level events from task-level stage events.
4. Derive `start.jsonl`, `complete.jsonl`, and `fail.jsonl` under `docs/evidence/lineage/` by filtering actual captured `eventType` values; do not construct replacement events. Record original filename/run ID for traceability.
5. Capture a happy run for START/COMPLETE across all stages and controlled stage-failure runs for START/FAIL. Correlate job name, namespace, run ID, task identity, event times, and task states. Check for missing, duplicate, truncated, or unparseable payloads and fail the evidence audit if capture is incomplete.

An executed failing task emits FAIL; a task blocked before execution does not need a fabricated START/FAIL pair. A schema-proof task that correctly catches its deliberately rejected write normally finishes successfully and emits COMPLETE. Use actual propagated exceptions for lineage failure demonstrations. Installing the provider alone never satisfies the rubric. Custom Python data operations may require explicit dataset metadata later for useful table/topic lineage; basic lifecycle events must still be real provider events.

## 10. Airflow DAG and quality-gate contract

Preserve the requested task order:

```text
produce_events
→ consume_and_validate
→ bronze_load
→ silver_merge
→ schema_enforcement_proof
→ quality_gate
→ gold_build
→ rag_chunk_and_index
→ rag_grounded_answer_smoke_test
```

Every edge requires `all_success`. The final task's contract must explicitly include dense retrieval, BM25, RRF, cross-encoder reranking, **Gemini grounded generation, and citation verification/output**. The approved task name is `rag_grounded_answer_smoke_test`. Keeping these in that final task preserves the requested topology and completes the RAG coverage already present in the matrix. Do not leave generation only as a manual CLI action outside the DAG.

`produce_events` waits for real Kafka acknowledgements. `consume_and_validate` uses a run-specific bounded record/offset manifest, validation, and acknowledged dead-letter writes; it must terminate after the finite input batch, with a timeout that fails on missing records. Accepted staging records can be persisted for `bronze_load`, with only paths/counts passed through XCom. Such staging is a handoff after real Kafka ingestion, not a Kafka or Delta substitute.

`schema_enforcement_proof` targets an isolated table. It succeeds only if an incompatible Delta write is actually refused and the table remains unchanged. `quality_gate` executes Great Expectations on Silver and raises an exception on an unsuccessful result. For reproducible failure demonstrations set retries to zero; otherwise a failed attempt can first enter `up_for_retry` before terminal failure.

With a terminal quality failure, expect `quality_gate=failed`; Gold and both RAG tasks settle to `upstream_failed` under the linear `all_success` chain and never execute. `skipped` is not the expected literal state for this exception-driven contract. The DAG run fails. Reject `all_done`, `always`, `one_success`, or any other bypass on output-producing tasks; no detached Gold/RAG branch is allowed. Lineage collection happens through listeners rather than a downstream processing task that bypasses the gate. [Airflow trigger rules](https://airflow.apache.org/docs/apache-airflow/3.3.1/core-concepts/dags.html)

This is a validated dependency design, not an inspection of an existing DAG. During implementation, assert task dependencies/trigger rules and capture an actual failed run and unchanged downstream outputs.

## 11. Rubric audit and remaining checks

| Area | Preflight finding | Disposition |
| --- | --- | --- |
| Ingestion — 20 | Real Kafka/client/Pydantic and Kafka quarantine feasible | Keep finite consumer contract and rejection reasons; execution proof pending |
| Delta Lakehouse — 25 | Real deltalake stack resolves; source key is unique | Keep append-only Bronze, real Silver MERGE, isolated rejected-write proof, and regional aggregate |
| RAG — 25 | Official texts and multilingual models accessible; stack resolves | Explicitly include generation/citations in final DAG task; preserve faithful snapshots |
| Orchestration — 15 | Official Airflow image exists; standalone/LocalExecutor avoids prohibited services | Enforce linear all-success dependencies and fail quality task on failed validation |
| Quality + lineage — 15 | Real GX available; provider/client code supports lifecycle events and file capture | Run GX success/failure and inspect task-correlated event payloads during implementation |
| Submission/documentation | Matrix covers mandatory requirements | Publication, README, real incremental history, attribution, and all other tracked requirements remain NOT IMPLEMENTED |

**Blockers:** no known platform, package-availability, declared dependency, business-key, or official-source blocker remains for starting Phase A with the decisions in this report. No unavailable selected model was found. The official Arabic MEWA page links to the complete downloadable strategy PDF, which is the primary MEWA RAG document; retain the webpage as provenance/fallback metadata.

**Incorrect or incomplete previous assumptions corrected:** not every province value is a region; regional sums do not exactly equal every supplied total; the data is 2024-only; a reranking-only final task would miss generation; installing OpenLineage alone is insufficient; Windows default Python and sandbox visibility do not describe the approved Linux runtime. These findings refine implementation plans without modifying AGENTS.md or matrix statuses.

**Risks to credit if ignored:** including national totals as regions, silently modifying values, skipping real schema failure/quality failure proofs, using a CLI-only generation stage, missing task-level FAIL events, using mocks as evidence, or claiming this preflight demonstrates scored execution. None requires a replacement architecture.

**Implementation validations still outstanding:** image build/import/ABI checks, actual CPU model loading and Arabic retrieval quality, Kafka listener connectivity, bind-mount permissions, measured memory use, real GX API behavior, real task-state/event capture, and authenticated Gemini access/quota. They were intentionally not exercised because this is pre-implementation validation. They must be tested in their implementation phases, not marked as already satisfied. Obtain the API key privately before generation, capture snapshots before indexing, and commit incremental work before final submission. No additional project-level approval or technology change is identified as necessary before Phase A.

## Resolved dependency inventory

The following is the temporary resolver's final Linux/Python 3.11 package inventory, preserved as documentation only. It is not an installed environment or a project requirements file. Use the CPU torch index routing described above when reproducing it.

```text
a2wsgi==1.10.10
aiohappyeyeballs==2.7.1
aiohttp==3.14.3
aiosignal==1.4.0
aiosmtplib==5.1.2
aiosqlite==0.22.1
alembic==1.19.0
altair==6.2.2
annotated-doc==0.0.5
annotated-types==0.8.0
anyio==4.14.2
apache-airflow==3.3.1
apache-airflow-core==3.3.1
apache-airflow-providers-common-compat==1.18.0
apache-airflow-providers-common-io==1.8.0
apache-airflow-providers-common-sql==2.1.0
apache-airflow-providers-openlineage==2.20.0
apache-airflow-providers-smtp==3.0.3
apache-airflow-providers-standard==1.17.0
apache-airflow-task-sdk==1.3.1
argcomplete==3.7.2
arro3-core==0.8.2
arrow==1.4.0
asgiref==3.12.1
attrs==26.1.0
babel==2.18.0
bcrypt==5.0.0
build==1.6.0
cachetools==6.2.6
cadwyn==7.0.0
certifi==2026.7.22
cffi==2.1.1
charset-normalizer==3.4.9
chromadb==1.5.9
click==8.4.2
colorlog==6.12.0
confluent-kafka==2.15.0
cron-descriptor==2.1.0
croniter==6.2.4
cryptography==50.0.0
deltalake==1.6.3
deprecated==1.3.1
dill==0.4.1
distro==1.9.0
dnspython==2.8.0
durationpy==0.10
email-validator==2.3.0
fastapi==0.136.3
fastapi-cli==0.0.32
filelock==3.32.2
flatbuffers==25.12.19
frozenlist==1.8.0
fsspec==2026.7.0
google-auth==2.56.3
google-genai==2.17.0
googleapis-common-protos==1.75.1
great-expectations==1.22.0
greenback==1.3.0
greenlet==3.5.4
grpcio==1.83.0
h11==0.16.0
hf-xet==1.6.0
httpcore==1.0.9
httptools==0.8.0
httpx==0.28.1
huggingface-hub==1.27.0
idna==3.18
importlib-metadata==8.9.0
importlib-resources==7.1.0
isoduration==20.11.0
itsdangerous==2.2.0
jinja2==3.1.6
joblib==1.5.3
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
kubernetes==36.0.3
lazy-object-proxy==1.12.0
libcst==1.9.0
linkify-it-py==2.1.0
lockfile==0.12.2
mako==1.4.1
markdown-it-py==4.2.0
markupsafe==3.0.3
marshmallow==4.3.0
mdurl==0.1.2
methodtools==0.4.7
mistune==3.3.4
mmh3==5.2.1
more-itertools==11.1.0
mpmath==1.3.0
msgspec==0.21.1
multidict==6.7.1
narwhals==2.24.0
natsort==8.4.0
networkx==3.6.1
numpy==2.4.6
oauthlib==3.3.1
onnxruntime==1.29.0
openlineage-integration-common==1.52.0
openlineage-python==1.52.0
openlineage-sql==1.52.0
opentelemetry-api==1.44.0
opentelemetry-exporter-otlp==1.44.0
opentelemetry-exporter-otlp-proto-common==1.44.0
opentelemetry-exporter-otlp-proto-grpc==1.44.0
opentelemetry-exporter-otlp-proto-http==1.44.0
opentelemetry-proto==1.44.0
opentelemetry-sdk==1.44.0
opentelemetry-semantic-conventions==0.65b0
orjson==3.11.9
outcome==1.3.0.post0
overrides==7.7.0
packaging==26.3
pandas==3.0.5
pathlib-abc==0.5.2
pathspec==1.1.1
pendulum==3.2.0
pluggy==1.6.0
propcache==0.5.2
protobuf==6.33.6
psutil==7.2.2
pyarrow==25.0.0
pyasn1==0.6.4
pyasn1-modules==0.4.2
pybase64==1.5.0
pycparser==3.0
pydantic==2.13.4
pydantic-core==2.46.4
pydantic-extra-types==2.11.1
pydantic-settings==2.15.0
pygments==2.20.0
pygtrie==2.5.0
pyjwt==2.13.0
pyparsing==3.3.2
pypika==0.51.1
pyproject-hooks==1.2.0
python-daemon==3.1.2
python-dateutil==2.9.0.post0
python-dotenv==1.2.2
python-multipart==0.0.32
python-slugify==8.0.4
pyyaml==6.0.3
rank-bm25==0.2.2
referencing==0.37.0
regex==2026.7.19
requests==2.34.2
requests-oauthlib==2.0.0
rich==14.3.4
rich-argparse==1.8.0
rich-toolkit==0.20.3
rpds-py==2026.6.3
ruamel-yaml==0.19.1
safetensors==0.8.0
scikit-learn==1.9.0
scipy==1.17.1
sentence-transformers==6.0.1
sentencepiece==0.2.1
setproctitle==1.3.7
setuptools==84.0.0
shellingham==1.5.4
six==1.17.0
sniffio==1.3.1
sqlalchemy==2.0.51
sqlparse==0.5.5
starlette==1.5.0
structlog==26.1.0
svcs==26.1.0
sympy==1.14.0
tabulate==0.10.0
tenacity==9.1.4
termcolor==3.3.0
text-unidecode==1.3
threadpoolctl==3.6.0
tokenizers==0.23.1
torch==2.14.0+cpu
tqdm==4.70.0
transformers==5.16.1
typer==0.27.1
typing-extensions==4.16.0
typing-inspection==0.4.2
tzdata==2026.3
tzlocal==5.4.4
uc-micro-py==2.0.0
universal-pathlib==0.3.10
urllib3==2.7.0
uuid6==2025.0.1
uvicorn==0.52.1
uvloop==0.22.1
watchfiles==1.2.0
websocket-client==1.8.0
websockets==16.1.1
wirerope==1.0.0
wrapt==2.3.0
yarl==1.24.5
zipp==4.1.0
```

## 12. Final decision

**GO — ready for Phase A**

Freeze Python 3.11 in the official Airflow 3.3.1 Python 3.11 Linux/amd64 image; Kafka 4.2.1 in single-node KRaft mode; the package pins and CPU torch selection in section 3 and the resolved inventory; official Airflow constraints with the recorded hash; one Airflow standalone service with LocalExecutor/SQLite WAL and concurrency one; D:-backed runtime/model storage; the two model IDs/revisions; stable `gemini-2.5-flash`; file-based OpenLineage capture; the exact CSV field mapping and unchanged business key; exclusion of supplied national totals from regional Gold; faithful official PDF RAG snapshots, with the Arabic MEWA strategy PDF primary and its webpage retained as provenance/fallback metadata; and the task/gate contract including final grounded generation and citations.

The approved project can cover **all 100 scored points**, subject to the rubric's real execution and evidence requirements. Every mandatory submission requirement remains covered in the matrix and unfulfilled until demonstrated. No scored requirement is IMPLEMENTED or VERIFIED by this report. **Stop here: Phase A has not been started.**
