# AquaLens 2030 — Configuration

## 1. Configuration principles

AquaLens keeps runtime configuration in environment variables and Docker Compose defaults.

Rules:

- never commit `.env`;
- never commit API keys;
- keep the official analytical CSV immutable;
- keep generated Delta, Chroma, caches, and Airflow runtime files under ignored paths;
- use the Docker-internal Kafka endpoint from containers and the localhost endpoint only for host debugging.

`.env.example` contains only non-secret examples.

---

## 2. User-facing environment variables

| Variable | Default | Required? | Purpose |
|---|---|---|---|
| `AIRFLOW_PORT` | `8080` | No | Host port bound to Airflow UI/API |
| `KAFKA_HOST_PORT` | `9092` | No | Host-only Kafka debugging endpoint |
| `GEMINI_API_KEY` | empty | Only for live generation | Gemini Developer API key |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:29092` | No | Kafka endpoint used by project code inside Docker |
| `KAFKA_RAW_TOPIC` | `aqualens.water.raw.v1` | No | Raw water-event topic |
| `KAFKA_QUARANTINE_TOPIC` | `aqualens.water.quarantine.v1` | No | Malformed-event DLQ/quarantine topic |
| `WATER_SOURCE_CSV` | `data/source/water_distribution_urban_saudi.csv` | No | Immutable analytical source path |
| `INGESTION_OUTPUT_ROOT` | `storage/ingestion` | No | Accepted-ingestion artifact root |
| `INGESTION_TIMEOUT_SECONDS` | `60` | No | Positive bounded-consumer timeout |

`INGESTION_TIMEOUT_SECONDS <= 0` is rejected by configuration validation.

---

## 3. `.env` example

```dotenv
AIRFLOW_PORT=8080
KAFKA_HOST_PORT=9092
GEMINI_API_KEY=
```

For a full success DAG run, set `GEMINI_API_KEY` privately.

Do not paste the key into:

- source code;
- notebooks;
- documentation;
- screenshots;
- execution evidence;
- Git history.

The Colab notebook requests a Gemini key interactively only when live generation is explicitly enabled.

---

## 4. Kafka endpoints

### Inside Docker

```text
kafka:29092
```

This is the default value of `KAFKA_BOOTSTRAP_SERVERS`.

### From the host

```text
localhost:9092
```

or the port selected through `KAFKA_HOST_PORT`.

Published ports bind to `127.0.0.1`, not all network interfaces.

---

## 5. Kafka topics

```text
aqualens.water.raw.v1
aqualens.water.quarantine.v1
```

Topics are real Kafka destinations. The quarantine topic stores the rejected payload plus rejection metadata; it is not a local list or simulated queue.

---

## 6. Airflow configuration

Docker Compose fixes the main local runtime settings:

| Setting | Value |
|---|---|
| `AIRFLOW_HOME` | `/opt/airflow/runtime` |
| DAG folder | `/opt/airflow/dags` |
| Executor | `LocalExecutor` |
| Parallelism | `1` |
| Max active runs per DAG | `1` |
| Max active tasks per DAG | `1` |
| Example DAGs | disabled |
| Metadata DB | SQLite under `/opt/airflow/runtime/airflow.db` |
| Log folder | `/opt/airflow/runtime/logs` |
| OpenLineage namespace | `aqualens2030` |

This compact configuration is intentional for a reproducible local capstone and is not presented as a production-scale Airflow deployment.

---

## 7. OpenLineage transport

OpenLineage is enabled through the Airflow provider.

FileTransport:

```text
/opt/airflow/docs/evidence/lineage/raw/event
```

The repository mount maps emitted files into:

```text
docs/evidence/lineage/raw/
```

`append=false` creates individual event files. Curated summaries are derived from those real emitted files; the project does not synthesize missing task events.

---

## 8. Model and cache configuration

Docker Compose directs model/runtime caches to gitignored storage:

| Variable | Container path |
|---|---|
| `HF_HOME` | `/opt/airflow/storage/models/huggingface` |
| `SENTENCE_TRANSFORMERS_HOME` | `/opt/airflow/storage/models/sentence-transformers` |
| `TORCH_HOME` | `/opt/airflow/storage/models/torch` |
| `XDG_CACHE_HOME` | `/opt/airflow/storage/cache` |

Other runtime controls:

```text
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
TOKENIZERS_PARALLELISM=false
```

The Docker image uses CPU-only PyTorch.

---

## 9. RAG configuration

Final retrieval/generation configuration:

| Component | Value |
|---|---|
| Embedding model | `intfloat/multilingual-e5-small` |
| Vector dimension | `384` |
| Normalization | yes |
| Chroma collection | `aqualens_official_docs` |
| Dense candidates | `8` |
| BM25 candidates | `8` |
| RRF | `k=60` |
| Reranker | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` |
| Final context | top `4` |
| Gemini model | `gemini-3.5-flash` |
| Temperature | `0` |

The embedding and reranker revisions are frozen in the RAG implementation/evidence.

Gemini 3.5 Flash is an explicitly approved runtime fallback after the original Gemini 2.5 Flash Developer API attempt returned HTTP 404.

Phase E uses bounded retries only for transient HTTP statuses:

```text
429, 500, 502, 503, 504
```

The retry mechanism does not change retrieval, grounding, citation rules, model identity, or temperature.

---

## 10. Airflow DAG parameter

The DAG accepts:

```json
{"quality_failure_demo": false}
```

Default: `false`.

To demonstrate the blocking quality path, trigger with:

```json
{"quality_failure_demo": true}
```

When enabled, the producer adds the isolated numeric-negative test fixture. Pydantic accepts its numeric type; Great Expectations later rejects `volume_m3 = -1`.

The test fixture is separate from the immutable analytical CSV.

---

## 11. Mounted repository paths

The Airflow container mounts:

| Host path | Container path | Mode |
|---|---|---|
| `./dags` | `/opt/airflow/dags` | read-only |
| `./src` | `/opt/airflow/src` | read-only |
| `./data/source` | `/opt/airflow/data/source` | read-only |
| `./rag/sources` | `/opt/airflow/rag/sources` | read-only |
| `./tests` | `/opt/airflow/tests` | read-only |
| `./requirements` | `/opt/airflow/requirements` | read-only |
| `./docs/evidence` | `/opt/airflow/docs/evidence` | writable evidence |
| `./storage` | `/opt/airflow/storage` | writable generated runtime |

This prevents the running pipeline from silently rewriting the official source files.

---

## 12. Secret and generated-file handling

`.gitignore` excludes:

- `.env` and local environment variants;
- credentials and key files;
- `/storage/`;
- virtual environments;
- Python/test caches;
- Airflow local runtime databases/logs;
- Delta/Parquet runtime files;
- Chroma runtime files;
- model caches.

Curated `docs/evidence/` files are intentionally committed only after secret-safety review.
