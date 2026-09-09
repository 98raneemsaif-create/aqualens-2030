# Phase D - official-document Hybrid RAG

**FAIL - stopped at the PDF extraction viability gate on 09 September 2026.** The approved pypdf amendment passes runtime validation. GASTAT extraction passes; MEWA extraction is not reliable enough for grounded retrieval and citations. No downstream RAG component was implemented or executed; no rubric row was advanced.

## Runtime amendment and resume

Added only `pypdf==6.17.0` to `requirements/runtime.in` and `requirements/runtime.lock`; documented the resulting 196-package inventory in `requirements/README.md`. All original 195 pins and official constraints remain unchanged. No OCR, fontTools, other parser, or other dependency was added.

The first build capture hit a Windows `UnicodeEncodeError`; its partial `build_pypdf.log` is retained. The UTF-8 retry completed successfully at 07:48:11 UTC with exit code 0 in `build_pypdf_retry.log`. Resume inspection confirmed that the build had completed, so it was not rebuilt. Only Airflow was recreated using the completed image `sha256:ad94dddd2a3b716dbea7436f8950095cd1dcacc1eeb3ec8033ec3d6c296f5b72`.

[Runtime verification](evidence/phase_d/runtime_verified.log) proves Python 3.11.15 at `/opt/aqualens/venv/bin/python`, Airflow 3.3.1, imported pypdf 6.17.0, all 196 exact frozen pins, and `pip check` success with no broken requirements. Key presence is true; the value was never printed or recorded. Gemini was not called.

Airflow is healthy. Kafka remains stopped as found, with unchanged container ID `0586330cf70e12b2683def8dfec7e0e03372b5a0ae7aa89b67541bb824ff97d3` and data volume `aqualens2030_kafka_data` mounted at `/var/lib/kafka/data`. No Kafka operation was performed. This is service continuity inspection, not orchestration or lineage evidence.

## Official snapshots and extraction

Both PDFs were downloaded from the exact preflight canonical URLs before the interruption and reused without redownloading. Raw bytes remain unchanged. Metadata preserves title, issuer, canonical/resolved URL, retrieval timestamp, language, PDF format, and SHA-256; MEWA also retains its official webpage as provenance. No publication date was invented.

| Document | Snapshot | Retrieved UTC | SHA-256 |
| --- | --- | --- | --- |
| MEWA National Water Strategy 2030, Arabic | `rag/sources/mewa_strategy.pdf` | 2026-09-09T07:42:00.197442+00:00 | `4abe289ef6c5053d0d819c33e89f3af82f81356e241ec893b20bfc95e31db71c` |
| GASTAT Methodology and Quality Report of Water Accounts, English | `rag/sources/gastat_methodology.pdf` | 2026-09-09T07:42:00.856723+00:00 | `1ccafbd53efac42a1f8e116b4e46e848c7791a67051c547df69b63cf13b8867a` |

Exact official URLs are in [MEWA metadata](../rag/sources/mewa_strategy.json), [GASTAT metadata](../rag/sources/gastat_methodology.json), and [download evidence](evidence/phase_d/source_download.log). No unofficial source was used.

Used pypdf 6.17.0 `extract_text(extraction_mode="plain")`, separately for each physical page. Page identity is one-based physical PDF index, not assumed printed pagination. Extracted text was preserved without rewriting.

| Document | Total pages | Nonempty pages | Extracted characters | Viability |
| --- | ---: | ---: | ---: | --- |
| MEWA | 125 | 122 | 220,748 | FAIL |
| GASTAT | 20 | 20 | 31,304 | PASS |

MEWA is text-bearing, not image-only. However, body samples on physical pages 15, 30, 50, 70, 90, 110, and 124 show systematic reversed word order, split/reordered words, and garbled numeric/table content. Page 30 mixes table numbers with modifier-like symbols; page 110 contains reordered word fragments. Unicode NFKC inspection resolves presentation forms but does not repair ordering. The parser also reports missing fontTools support for CFF Type1 font encoding and malformed object-pointer warnings. The actual content defects, not warnings alone, cause the failure. No speculative text reconstruction was attempted; fontTools has not been established as a sufficient remedy and was not installed.

GASTAT body samples are readable English, with preserved headings and paragraphs. Physical page 5 describes the environmental/economic scope and mainly administrative-record basis of water accounts. Additional body pages 6, 7, 10, 15, and 20 were inspected.

[Final viability review](evidence/phase_d/extraction/viability_review.json) preserves representative body samples and records overall FAIL. [Summary](evidence/phase_d/extraction/summary.json) contains initial samples, counts, and provenance. Full page text is in [MEWA pages](evidence/phase_d/extraction/mewa_strategy_pages.json) and [GASTAT pages](evidence/phase_d/extraction/gastat_methodology_pages.json).

The [extraction log](evidence/phase_d/extraction.log) has exit code 0 because the parser produced text and the basic quantity checks passed. That does not establish readability: the script explicitly requires sample review. The manual readability gate failed. Both documents must pass before indexing.

## Commands and evidence

Captured commands use `tests/capture_phase_a.py`; each log records actual arguments, timestamps, and exit status. Set `$env:PYTHONIOENCODING='utf-8'` for Windows log capture.

```powershell
# Completed before interruption; not rerun on resume:
python tests/capture_phase_a.py docs/evidence/phase_d/build_pypdf_retry.log docker compose --progress plain build airflow
# Resume inspection:
git status --short
docker compose ps -a
docker image inspect aqualens2030-airflow:phase-a --format '{{.Id}} {{.Created}}'
docker inspect aqualens2030-airflow-1 --format '{{.Image}} {{.State.Status}}'
# Apply completed image and validate:
python tests/capture_phase_a.py docs/evidence/phase_d/recreate_airflow.log docker compose up -d --no-deps --no-build airflow
python tests/capture_phase_a.py docs/evidence/phase_d/runtime_verified.log docker compose exec -T airflow python tests/phase_d_runtime.py
python tests/capture_phase_a.py docs/evidence/phase_d/extraction.log docker compose exec -T airflow python -m src.rag.extraction
python tests/capture_phase_a.py docs/evidence/phase_d/service_status_final.log docker compose ps -a
git diff --check
```

The first runtime inspection found the old container stopped; only then was the completed image applied. No resolved Compose environment or full secret-bearing inspection output was displayed. [Scope audit](evidence/phase_d/scope_audit.json) verifies protected files remain unchanged and pypdf is the only added pin. Runtime checks passed; no RAG model/algorithm tests were run because the viability gate failed.

## Exact files changed across Phase D

Modified: `requirements/runtime.in`, `requirements/runtime.lock`, `requirements/README.md`.

Created or updated:

- `src/rag/extraction.py`
- `tests/acquire_rag_sources.py`
- `tests/phase_d_runtime.py`
- `rag/sources/mewa_strategy.pdf`
- `rag/sources/mewa_strategy.json`
- `rag/sources/gastat_methodology.pdf`
- `rag/sources/gastat_methodology.json`
- `docs/phase_d_report.md`
- `docs/evidence/phase_d/prerequisites.log`
- `docs/evidence/phase_d/prerequisite_report.md`
- `docs/evidence/phase_d/build_pypdf.log`
- `docs/evidence/phase_d/build_pypdf_retry.log`
- `docs/evidence/phase_d/source_download.log`
- `docs/evidence/phase_d/recreate_airflow.log`
- `docs/evidence/phase_d/runtime_verified.log`
- `docs/evidence/phase_d/extraction.log`
- `docs/evidence/phase_d/extraction/summary.json`
- `docs/evidence/phase_d/extraction/mewa_strategy_pages.json`
- `docs/evidence/phase_d/extraction/gastat_methodology_pages.json`
- `docs/evidence/phase_d/extraction/viability_review.json`
- `docs/evidence/phase_d/service_status_final.log`
- `docs/evidence/phase_d/scope_audit.json`

The initial missing-parser blocker was resolved by the explicitly approved dependency. Its [original report](evidence/phase_d/prerequisite_report.md), original evidence, and Windows encoding-error evidence remain preserved.

## Unresolved issue and stopping point

Reliable Arabic extraction from the preserved official MEWA PDF remains unresolved. The user explicitly requires stopping on unusable extraction, and no further dependency is authorized. An approved extraction remedy is required before resuming.

Chunking, embeddings, Chroma, BM25, RRF, mMARCO, Gemini answers/citations, and end-to-end tests are not implemented or executed. No RAG row or unrelated rubric status was advanced. No CSV, Lakehouse table, Phase B/C evidence, AGENTS.md, or Docker configuration was changed. No commit, project DAG, quality gate, OpenLineage event, UI, or Phase E work was performed. **Phase D: FAIL; stopped at the required gate.**
