# AquaLens 2030 Repository Guidelines

## Authority and scope

This file is the authoritative contributor and agent guide for AquaLens 2030. The primary source of truth is [Capstone Rubric - Modern Data Engineering for AI Systems](docs/reference/Capstone%20Rubric%20-%20Modern%20Data%20Engineering%20for%20AI%20Systems.pdf). If any project instruction conflicts with that rubric, the rubric wins.

Read the rubric before making architectural or dependency changes. Use real required technologies: simulations and custom substitutes do not earn rubric credit. Code existence is not execution evidence.

## Project purpose

AquaLens 2030 is a Saudi Urban Water Source Intelligence Platform. It processes real Saudi urban water-source data through Kafka and a Delta Lakehouse, produces regional water-source composition profiles, validates pipeline quality, emits lineage events, and provides Hybrid RAG answers grounded in official Saudi water-strategy and statistical-methodology sources.

Keep the project intentionally small enough to complete within 1–2 days while satisfying the full capstone rubric. The rubric totals 100 points and sets a pass mark of 60; this project's target is to demonstrate every scored requirement.

## Mandatory rubric requirements

### Ingestion — 20 points

- Use a real Kafka producer and consumer with `confluent-kafka`.
- Validate records at the ingestion boundary using Pydantic.
- Route malformed records to a Kafka quarantine/dead-letter topic.
- Record the rejection reason for every rejected record.

### Delta Lakehouse — 25 points

- Use real Delta Lake tables through `deltalake`, with Bronze, Silver, and Gold layers.
- Keep Bronze append-only.
- Perform a real Delta MERGE/upsert in Silver using the composite business key `year + region + source`.
- Demonstrate Delta schema enforcement with a deliberately rejected invalid write.
- Make Gold a genuine aggregate, not a copy of Silver.

### RAG pipeline — 25 points

Include every component below, using real libraries and executed evidence:

- Document chunking.
- Multilingual sentence-transformer embeddings.
- A real vector store using ChromaDB `PersistentClient`.
- Dense/vector retrieval.
- BM25 keyword retrieval using `BM25Okapi`.
- Reciprocal Rank Fusion (RRF) of dense and keyword results.
- Multilingual cross-encoder reranking.
- Grounded LLM generation using Gemini 2.5 Flash.
- Citations supporting answers with retrieved source context.

Vector-only RAG is not acceptable.

### Orchestration — 15 points

- Use Apache Airflow 3.3.1.
- Represent the complete pipeline in a real Airflow DAG wiring every stage together.
- Configure task dependencies so a failed quality gate prevents downstream execution. Do not use trigger rules that let dependent stages bypass a failed gate.

### Quality gate and lineage — 15 points

- Use Great Expectations as a real quality gate.
- A failed validation must fail the Airflow task and halt dependent downstream stages.
- Use OpenLineage through the OpenLineage Airflow Provider and its real OpenLineage client integration.
- Emit and capture START, COMPLETE, and FAIL lineage events per stage as appropriate to its execution outcome. Demonstrate success and failure runs.

## Approved architecture

Use Python 3.11, Docker Compose, Apache Kafka, `confluent-kafka`, Pydantic, `deltalake`, Great Expectations, Apache Airflow 3.3.1, OpenLineage Airflow Provider, ChromaDB `PersistentClient`, multilingual sentence-transformer embeddings, `BM25Okapi`, Reciprocal Rank Fusion, a multilingual cross-encoder reranker, Gemini 2.5 Flash, Git, and GitHub.

Do not introduce Spark, ZooKeeper, Redis, Celery, Marquez, Chroma Server, Schema Registry, ML forecasting, anomaly detection, synthetic analytical datasets, or large UI frameworks unless strictly required to satisfy the rubric. Prefer the smallest implementation that fully satisfies it.

## Business rules

The analytical dataset is real Saudi water-distribution data. Permitted analytical outputs include:

- Total regional water volume.
- Dominant source.
- Dominant source volume.
- Dominant source share.
- Active source count.

Do not label regions as HIGH/MEDIUM/LOW risk or invent water-risk thresholds. Keep observed data and strategic interpretation separate: the Lakehouse answers what the data shows; RAG explains official strategic and methodological context.

### Approved analytical dataset

The only approved analytical dataset for the core project is:

**Water Distribution in Urban Sector by Source – Annual**

Source:

- General Authority for Statistics (GASTAT)
- accessed through DataSaudi

Expected analytical dimensions:

- Source
- Geography Province
- Year

Metric:

- Volume of water (m³)

The immutable local snapshot must be stored at:

`data/source/water_distribution_urban_saudi.csv`

Do not replace this dataset or introduce additional analytical datasets without explicit approval.

### Approved RAG sources

The core RAG knowledge base is restricted to these official Saudi government sources:

1. **National Water Strategy 2030**
   - Organization: Ministry of Environment, Water and Agriculture (MEWA)

2. **Methodology and Quality Report of Water Accounts**
   - Organization: General Authority for Statistics (GASTAT)

Local curated source snapshots belong under:

`rag/sources/`

Do not add blogs, Kaggle content, Wikipedia, commercial reports, or unofficial secondary sources to the core RAG knowledge base.

## Repository structure

| Path              | Purpose                                                  |
| ----------------- | -------------------------------------------------------- |
| `dags/`           | Airflow DAGs                                             |
| `src/ingestion/`  | Kafka producer, consumer, and schema validation          |
| `src/lakehouse/`  | Bronze, Silver, Gold, MERGE, and schema proof            |
| `src/quality/`    | Great Expectations logic                                 |
| `src/rag/`        | Chunking, indexing, retrieval, reranking, and generation |
| `src/app/`        | CLI                                                      |
| `src/common/`     | Shared configuration                                     |
| `data/source/`    | Immutable real source dataset                            |
| `rag/sources/`    | Official Saudi government source snapshots               |
| `tests/`          | Automated tests and failure fixtures                     |
| `docs/evidence/`  | Execution evidence                                       |
| `docs/reference/` | Capstone rubric                                          |
| `storage/`        | Generated Delta and Chroma data; gitignored              |

Do not modify the original file in `data/source/`. Keep deliberately malformed test records in failure fixtures, separate from the analytical source dataset.

## Rubric tracking

Maintain `docs/rubric_matrix.md`. For every scored rubric item, include requirement, points, implementation, test/proof, evidence location, and status. Track individual required components within the five scored deliverables without double-counting category points.

Never mark a requirement complete unless it has been executed successfully and its evidence is available. For a failure-path requirement, success means the intended rejection or blocking behavior was observed and captured. Distinguish implemented but unverified work from demonstrated completion.

## Evidence rules

Every major requirement must have reproducible execution evidence under `docs/evidence/`. Capture actual run logs or executed notebooks with output, including the command or steps, relevant configuration without secrets, expected behavior, and observed result. Include happy and failure paths where relevant.

Required proof includes:

- Kafka producer and consumer execution.
- Malformed-record quarantine and a recorded rejection reason.
- Real Delta tables and a real MERGE/upsert.
- A rejected schema write.
- Great Expectations success and failure.
- Airflow downstream tasks skipped or blocked after quality failure; preserve actual task states such as `upstream_failed` rather than relabeling them.
- OpenLineage START, COMPLETE, and FAIL events emitted and captured per stage across relevant runs.
- Dense retrieval, BM25 retrieval, RRF fusion, and cross-encoder reranking.
- A grounded answer with citations.

Do not fabricate evidence or treat mocks as proof that a required technology works.

## Coding guidelines

- Keep modules small and single-purpose.
- Prefer simple Python over unnecessary abstractions.
- Use type hints where practical and descriptive `snake_case` names.
- Keep configuration in environment variables or shared configuration modules.
- Never commit secrets.
- Do not silently swallow exceptions.
- Log important pipeline events and validation failures clearly.

## Testing

Tests must cover valid ingestion, malformed ingestion, quarantine behavior, Delta MERGE, schema enforcement failure, Great Expectations success and failure, hybrid retrieval components, and grounded citation output.

Include an explicit, reproducible failure-demo path that demonstrates rejected ingestion, schema enforcement, and quality-gate failure with downstream blocking and failure lineage. Run integration proofs against the actual required technologies; isolated unit tests alone do not establish rubric completion.

## Git and submission guidelines

Use incremental, meaningful commits. Examples:

- `chore: scaffold AquaLens runtime environment`
- `feat: implement Kafka ingestion and quarantine`
- `feat: build Delta bronze silver gold pipeline`
- `feat: add Great Expectations quality gate`
- `feat: integrate Airflow and OpenLineage`
- `feat: implement hybrid RAG pipeline`
- `docs: add rubric evidence and final documentation`

Do not commit `.env`, API keys, generated Delta tables, generated Chroma files, caches, or local runtime artifacts. Maintain a `.gitignore` that excludes secrets and generated files. Keep curated execution evidence free of secrets.

The rubric also requires:

- Each trainee to create and activate a GitHub account if needed.
- The project to be published to GitHub, documented, and continuously updated; an unpublished project is not a complete submission.
- A clear project description on the repository landing page explaining the problem, purpose, and scope.
- A professional README covering prerequisites, installation/setup, execution, usage, and expected output.
- Technical documentation covering architecture or pipeline overview, key components/modules, and required configuration/environment variables.
- Training attribution naming **Modern Data Engineering for AI Systems**, SDAIA Academy, delivered via Learning Space, and the actual cohort/session dates.
- Training attribution must state:
  - Program: **Modern Data Engineering for AI Systems**
  - Provider: **SDAIA Academy**
  - Delivery: **Learning Space**
  - Cohort/session dates: **06 September 2026 – 10 September 2026**
- A relevant README link to [SDAIA Academy on GitHub](https://github.com/SDAIAAcademy).

Supporting Saudi projects through stars, follows, contributions, forks, pull requests, issues, or sharing is encouraged by the rubric but is not scored and is not required for completion.

## Agent-specific workflow

Before making architectural or dependency changes:

1. Read the Capstone Rubric.
2. Check `docs/rubric_matrix.md`; if it does not exist, report the gap and establish it when within the requested phase's scope.
3. Explain why the change is necessary.
4. Prefer the smallest implementation that fully satisfies the rubric.

Do not continue automatically into the next project phase after completing a requested phase.

After each implementation phase:

1. Run the code.
2. Run relevant tests.
3. Inspect logs.
4. Update execution evidence.
5. Audit against the rubric and update the rubric matrix accurately.
6. Report unresolved issues, including anything not executed or verified.

The goal is a working, executed, well-documented project that can demonstrate every scored requirement in the Capstone Rubric.
