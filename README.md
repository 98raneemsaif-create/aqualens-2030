# AquaLens 2030

A Saudi Urban Water Source Intelligence Platform built for the **Modern Data Engineering for AI Systems** program, provided by [SDAIA Academy](https://github.com/SDAIAAcademy) and delivered by Learning Space, **06 September 2026 – 10 September 2026**.

The planned platform uses the immutable GASTAT/DataSaudi water-distribution dataset to produce regional source-composition profiles, with Hybrid RAG explaining official Saudi strategy and methodology. Observed volumes and strategic interpretation remain separate. See [AGENTS.md](AGENTS.md), the [rubric matrix](docs/rubric_matrix.md), and the [approved preflight](docs/preflight_report.md).

## Phase A: local runtime

Phase A provides the repository scaffold and two local Docker services: Kafka 4.2.1 in single-node KRaft mode, and Airflow 3.3.1 on Python 3.11. It contains no business ingestion, Delta transformations, quality rules, RAG implementation, or project DAG. This is a local capstone environment, not a production deployment.

Prerequisites: Docker Desktop running Linux containers with WSL 2, Docker Compose, Git, and enough disk/RAM for the pinned CPU-only stack. The validated host keeps Docker storage on D:. Compose does not change Docker Desktop's disk location. See [dependency installation notes](requirements/README.md).

From the repository root:

```powershell
# Optional: copy .env.example to .env to change localhost ports.
docker compose build airflow
docker compose up -d --wait --wait-timeout 300
docker compose ps
docker compose exec -T airflow python -m pip check
docker compose exec -T -e HF_HUB_OFFLINE=1 airflow python /opt/airflow/tests/phase_a_smoke.py
```

Expected output: both services healthy, `pip check` reports no broken requirements, and all Phase A smoke checks pass. These checks load packages and query broker metadata; they do not load model weights, produce business records, or earn scored rubric credit.

Airflow UI: <http://localhost:8080>. Health API: <http://localhost:8080/api/v2/monitor/health>. Standalone generates local login credentials in its private runtime volume; inspect them only in your local terminal, never paste them into evidence or commit them:

```powershell
docker compose exec airflow cat /opt/airflow/runtime/simple_auth_manager_passwords.json.generated
```

Configuration: `.env.example` documents optional host ports and a blank `GEMINI_API_KEY` for a later phase. No API key is needed for Phase A. Airflow uses `kafka:29092` internally; host Kafka debugging uses `localhost:9092`. All published ports bind to localhost. Source CSV, DAG, code, and RAG-source mounts are read-only. Delta/Chroma/model caches will live in gitignored `storage/`. SQLite and Kafka data use named Linux volumes. OpenLineage is enabled with FileTransport, `append=false`, and a writable `docs/evidence/lineage/raw/` mount; no artificial events are generated.

Stop services while retaining data:

```powershell
docker compose stop
# Alternatively remove containers/network, retaining named volumes:
docker compose down
```

Do not use `down --volumes` unless you deliberately intend to erase local runtime data. Phase A execution evidence and its final audit belong under [docs/evidence/phase_a/](docs/evidence/phase_a/). Do not proceed to Phase B without a separate request.
