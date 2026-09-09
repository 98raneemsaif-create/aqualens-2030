# Configuration documentation review

`docs/configuration.md` was cross-checked with the repository configuration and Docker Compose defaults.

Verified documented settings include:
- `AIRFLOW_PORT=8080` default host UI port;
- `KAFKA_HOST_PORT=9092` default host Kafka port;
- `KAFKA_BOOTSTRAP_SERVERS=kafka:29092`;
- `KAFKA_RAW_TOPIC=aqualens.water.raw.v1`;
- `KAFKA_QUARANTINE_TOPIC=aqualens.water.quarantine.v1`;
- `WATER_SOURCE_CSV=data/source/water_distribution_urban_saudi.csv`;
- `INGESTION_OUTPUT_ROOT=storage/ingestion`;
- `INGESTION_TIMEOUT_SECONDS=60`;
- Airflow LocalExecutor / local runtime settings;
- OpenLineage namespace / FileTransport;
- model-cache paths;
- RAG model/retrieval settings;
- `quality_failure_demo` DAG configuration;
- read-only source mounts vs writable runtime/evidence mounts;
- secret and generated-file handling.

`GEMINI_API_KEY` is documented as a private local/runtime value and is never embedded in committed project files.

Result: PASS.
