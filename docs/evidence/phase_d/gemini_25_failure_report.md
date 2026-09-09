# Phase D - official-document Hybrid RAG

**FAIL - extraction and real hybrid retrieval are demonstrated; Gemini generation returned HTTP 404 for the required `gemini-2.5-flash`.** No grounded answer was produced. Stopped as required without substituting another model or proceeding to Phase E.

## Blocker history and approved runtime amendments

1. The initial runtime had no PDF parser. The original [prerequisite report](evidence/phase_d/prerequisite_report.md) and [presence/parser check](evidence/phase_d/prerequisites.log) remain preserved.
2. Explicitly approved `pypdf==6.17.0` was added to source/lock. Its Windows build-capture encoding failure and successful retry remain in `build_pypdf.log` and `build_pypdf_retry.log`. GASTAT extraction passed; MEWA plain extraction failed the readability gate. The [pypdf failure report](evidence/phase_d/pypdf_failure_report.md) and all original extraction evidence remain unchanged.
3. Explicitly approved `PyMuPDF==1.28.2` was added as the second narrow extraction amendment. pypdf remains installed. No OCR, Tesseract, fontTools, pymupdf-layout, pdfplumber, LangChain, or other dependency was added.

`requirements/runtime.in` and `requirements/runtime.lock` contain the original 195 pins plus these two approved pins; `requirements/README.md` documents the 197-package inventory. [Actual runtime verification](evidence/phase_d/runtime_pymupdf.log) confirms Python 3.11.15 at `/opt/aqualens/venv/bin/python`, Airflow 3.3.1, pypdf 6.17.0, PyMuPDF 1.28.2, all 197 exact package versions, and successful `pip check`.

Only Airflow was rebuilt and recreated. It is healthy. Kafka remains stopped as found, with unchanged container identity and data volume; no Kafka operation was performed. The Compose file and architecture are unchanged. Gemini key presence was checked without exposing its value. A [safety scan](evidence/phase_d/secret_safety_check.log) confirms the actual key is absent from code and captured evidence. Presence does not establish model access.

## Official PDFs and extraction decision

The existing snapshots were reused; neither PDF was redownloaded or modified. Exact canonical URLs, titles, issuers, languages, retrieval timestamps and formats are preserved in [MEWA metadata](../rag/sources/mewa_strategy.json) and [GASTAT metadata](../rag/sources/gastat_methodology.json). The MEWA webpage is provenance only. No publication date was invented.

| Source | Retrieved UTC | SHA-256 |
| --- | --- | --- |
| MEWA National Water Strategy 2030, Arabic | 2026-09-09T07:42:00.197442+00:00 | `4abe289ef6c5053d0d819c33e89f3af82f81356e241ec893b20bfc95e31db71c` |
| GASTAT Methodology and Quality Report of Water Accounts, English | 2026-09-09T07:42:00.856723+00:00 | `1ccafbd53efac42a1f8e116b4e46e848c7791a67051c547df69b63cf13b8867a` |

All extraction modes preserve physical PDF page identity; citations use one-based physical pages, not assumed printed pagination.

| MEWA mode | Nonempty / total pages | Characters | Readability decision |
| --- | ---: | ---: | --- |
| `page.get_text("text")`, default unsorted | 122 / 125 | 202,944 | Selected for narrative strategic context |
| `page.get_text("text", sort=True)` | 122 / 125 | 405,497 | Rejected: fragmented/reordered Arabic prose |
| `python -m pymupdf gettext -mode layout` | 119 / 125 | 443,782 | Rejected: reversed character ordering; errors on pages 11, 19, 56 |

The layout mode exists in 1.28.2. Its first invocation stopped at page 11; the comparison script was corrected to capture per-page failures and finish assessing remaining pages while reusing completed default/sorted outputs. Both logs are preserved. Default mode maintains readable sentence/argument order on the required pages 15, 30, 50, 70, 90, 110, 124 and additional narrative pages 6, 14, 16, 17. Minor ligature/diacritic artifacts remain; it is not a typographically exact transcription. Numeric sequences and tables are not dependable. Sorted/layout modes do not improve narrative reliability and were not combined with default output.

[Mode summary and samples](evidence/phase_d/pymupdf/summary.json), [readability decision](evidence/phase_d/pymupdf/viability_review.json), and full `text_pages.json`, `sorted_pages.json`, `layout_pages.json` preserve the comparison. Default mode passes for narrative context with explicit exclusions. No strings were reversed, no paragraphs reconstructed, and no strategy text hardcoded.

GASTAT retains its already verified pypdf plain extraction: 20/20 nonempty pages, 31,304 characters. Original pypdf MEWA output remains 122/125 nonempty pages and 220,748 characters; that failed output is not indexed.

## Implemented flow and corpus limitations

`chunking.py` extracts MEWA using the selected default mode and GASTAT using pypdf. Normalization uses Unicode NFKC, tatweel removal and whitespace normalization only. MEWA lines containing numbers, replacement/question-mark characters, Latin text, or fewer than 15 letters break prose runs. Excluded lines are not stitched across; runs below 100 characters are excluded. This deliberately limits the MEWA corpus to narrative excerpts rather than numerical targets or complete table coverage. It is not a claim that every chart or table was parsed. Raw PDFs and per-page text remain available for provenance.

Chunks target 800 characters with 120-character overlap, do not cross physical pages or excluded runs, and retain stable SHA-256 IDs, title, issuer, physical page, URL, language, source hash, method, line bounds and run offset. Actual counts: **391 MEWA + 54 GASTAT = 445 chunks**.

`retrieval.py` uses the frozen CPU models:

- `intfloat/multilingual-e5-small`, revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`, with passage/query prefixes and normalized 384-dimensional vectors.
- `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`, revision `1427fd652930e4ba29e8149678df786c240d8825`, real sentence-transformers CrossEncoder.

Model downloads/caches are runtime-only under gitignored storage, not baked into the image. Chroma `PersistentClient` stores collection `aqualens_official_docs` at `storage/rag/402947a2-1f21-445a-82a0-e0e3e4be3b70/chroma`. It contains 445 real vectors with retrievable documents/metadata. BM25Okapi uses the same corpus with light deterministic Arabic normalization. Dense top 8 and BM25 top 8 execute separately; RRF k=60 produces up to 10 candidates, then the cross-encoder selects top 4.

`generation.py` requests only `gemini-2.5-flash`, temperature 0, through google-genai 2.17.0. It supplies retrieved context, requires the query language, forbids outside facts and concentration-to-risk inference, separates observations from interpretation, and requires insufficient-evidence responses when appropriate. Structured statements must cite available chunk IDs; rendering resolves them to document/page/official URL. Empty context returns a deterministic insufficient-evidence result without calling Gemini. These generation/citation contracts pass unit tests but have **not** produced a verified model answer.

## Real proof and tests

Proof ID: `402947a2-1f21-445a-82a0-e0e3e4be3b70`.

[Execution log](evidence/phase_d/rag_execution.log) records model loading, indexing, and HTTP 404 on the first Gemini request. SDK exception details and credentials were not captured; only the HTTP status is reported. The evidence does not establish why this model request returned 404 (model availability, endpoint support, or account access remain unresolved). No alternate model or second generation request was attempted.

The first query asks in Arabic about strategic objectives for water-demand management and preserving water resources and the environment. Its exact Arabic text and actual outputs are in [retrieval evidence](evidence/phase_d/402947a2-1f21-445a-82a0-e0e3e4be3b70/query_1_retrieval.json): dense ranks/distances, BM25 scores/ranks, fused scores/order, all reranker scores, and four selected MEWA chunks from physical pages 13, 63, 68 and 69.

Two further configured queries were **not executed**, because the first generation failure triggered the required stop:

- What are the main data sources and statistical scope of Saudi Arabia's water accounts?
- What is the approved water tariff for a permanent colony on Mars in 2045?

No answer, final citation, methodology smoke answer, or real-model insufficient-evidence response is claimed. No fake response files were created.

[Seven unit tests](evidence/phase_d/unit_tests.log) pass: deterministic chunks/metadata, overlap, E5 prefixes and Arabic token normalization, RRF math/order, invalid citation rejection, grounding/empty-context behavior, and exclusion boundaries. A [separate-process verification](evidence/phase_d/retrieval_verification.log) reopened Chroma, checked all 445 documents/metadata, vector shape and norms, both ranked branches, independent RRF recomputation, finite reranker scores/order, and selection of the final four chunks. [Index evidence](evidence/phase_d/402947a2-1f21-445a-82a0-e0e3e4be3b70/index.json) records exact model identities, collection and sample metadata. [Chunk evidence](evidence/phase_d/402947a2-1f21-445a-82a0-e0e3e4be3b70/chunks.json) preserves the entire indexed corpus.

Runtime sample: 2.39 GiB / 5 GiB RAM and 95.65% of one CPU core during RAG execution. This is a point-in-time observation, not a benchmark. See `resources_rag.log` and `services_disposition.log`. No persistent service error was found. Library notices about unauthenticated public HF downloads and a deprecated cache argument did not prevent model execution.

## Rubric disposition

Verified seven scored RAG component rows: chunking, embeddings, real vector store, dense retrieval, BM25 retrieval, fusion, and cross-encoder reranking. Four corresponding retrieval evidence rows are verified. Grounded-answer and citation rows retain their prior unverified status; implementation code alone does not earn credit. No points were invented for individual rows of the 25-point category. All non-RAG rows remain unchanged.

## Commands

All captured commands ran from the repository root, with `$env:PYTHONIOENCODING='utf-8'`. Logs record timestamps, exact arguments and exit status.

```powershell
python tests/capture_phase_a.py docs/evidence/phase_d/build_pymupdf.log docker compose --progress plain build airflow
python tests/capture_phase_a.py docs/evidence/phase_d/recreate_pymupdf.log docker compose up -d --no-deps --no-build airflow
python tests/capture_phase_a.py docs/evidence/phase_d/runtime_pymupdf.log docker compose exec -T airflow python tests/phase_d_runtime.py
docker compose exec -T airflow python -m pymupdf gettext -h
python tests/capture_phase_a.py docs/evidence/phase_d/pymupdf_gate.log docker compose exec -T airflow python tests/phase_d_pymupdf_gate.py
python tests/capture_phase_a.py docs/evidence/phase_d/pymupdf_gate_resume.log docker compose exec -T airflow python tests/phase_d_pymupdf_gate.py
python tests/capture_phase_a.py docs/evidence/phase_d/rag_execution.log docker compose exec -T airflow python -m src.rag.pipeline
python tests/capture_phase_a.py docs/evidence/phase_d/unit_tests.log docker compose exec -T airflow python -m unittest discover -s tests -p test_rag.py -v
python tests/capture_phase_a.py docs/evidence/phase_d/retrieval_verification.log docker compose exec -T airflow python tests/verify_phase_d_retrieval.py docs/evidence/phase_d/402947a2-1f21-445a-82a0-e0e3e4be3b70
```

Additional captured checks: `docker stats --no-stream`, narrow Kafka identity/mount inspection, `docker compose ps -a`, and a boolean-only secret safety scan. Local audits compared pins/protected files to Git and ran `git diff --check`. For later approved retries use new evidence-log filenames; pipeline runs create fresh UUID proof/storage paths. Do not overwrite failed proof evidence.

## Exact changed contributor files across Phase D

The following inventory includes the initial prerequisite attempt, both approved parser amendments, and current RAG work. Runtime/model/Chroma artifacts remain gitignored. Existing official PDFs are listed because they were first added in Phase D, not because they were redownloaded in this resume.

- `docs/evidence/phase_d/402947a2-1f21-445a-82a0-e0e3e4be3b70/chunks.json`
- `docs/evidence/phase_d/402947a2-1f21-445a-82a0-e0e3e4be3b70/index.json`
- `docs/evidence/phase_d/402947a2-1f21-445a-82a0-e0e3e4be3b70/query_1_retrieval.json`
- `docs/evidence/phase_d/402947a2-1f21-445a-82a0-e0e3e4be3b70/retrieval_verification.json`
- `docs/evidence/phase_d/build_pymupdf.log`
- `docs/evidence/phase_d/build_pypdf.log`
- `docs/evidence/phase_d/build_pypdf_retry.log`
- `docs/evidence/phase_d/extraction.log`
- `docs/evidence/phase_d/extraction/gastat_methodology_pages.json`
- `docs/evidence/phase_d/extraction/mewa_strategy_pages.json`
- `docs/evidence/phase_d/extraction/summary.json`
- `docs/evidence/phase_d/extraction/viability_review.json`
- `docs/evidence/phase_d/final_scope_audit.json`
- `docs/evidence/phase_d/kafka_identity_pymupdf.log`
- `docs/evidence/phase_d/prerequisite_report.md`
- `docs/evidence/phase_d/prerequisites.log`
- `docs/evidence/phase_d/pymupdf/layout_pages.json`
- `docs/evidence/phase_d/pymupdf/sorted_pages.json`
- `docs/evidence/phase_d/pymupdf/summary.json`
- `docs/evidence/phase_d/pymupdf/text_pages.json`
- `docs/evidence/phase_d/pymupdf/viability_review.json`
- `docs/evidence/phase_d/pymupdf_gate.log`
- `docs/evidence/phase_d/pymupdf_gate_resume.log`
- `docs/evidence/phase_d/pypdf_failure_report.md`
- `docs/evidence/phase_d/rag_execution.log`
- `docs/evidence/phase_d/recreate_airflow.log`
- `docs/evidence/phase_d/recreate_pymupdf.log`
- `docs/evidence/phase_d/resources_rag.log`
- `docs/evidence/phase_d/retrieval_verification.log`
- `docs/evidence/phase_d/runtime_pymupdf.log`
- `docs/evidence/phase_d/runtime_verified.log`
- `docs/evidence/phase_d/scope_audit.json`
- `docs/evidence/phase_d/secret_safety_check.log`
- `docs/evidence/phase_d/service_status_final.log`
- `docs/evidence/phase_d/services_disposition.log`
- `docs/evidence/phase_d/source_download.log`
- `docs/evidence/phase_d/unit_tests.log`
- `docs/phase_d_report.md`
- `docs/rubric_matrix.md`
- `rag/sources/gastat_methodology.json`
- `rag/sources/gastat_methodology.pdf`
- `rag/sources/mewa_strategy.json`
- `rag/sources/mewa_strategy.pdf`
- `requirements/README.md`
- `requirements/runtime.in`
- `requirements/runtime.lock`
- `src/rag/chunking.py`
- `src/rag/extraction.py`
- `src/rag/generation.py`
- `src/rag/pipeline.py`
- `src/rag/retrieval.py`
- `tests/acquire_rag_sources.py`
- `tests/phase_d_pymupdf_gate.py`
- `tests/phase_d_runtime.py`
- `tests/test_rag.py`
- `tests/verify_phase_d_retrieval.py`

## Unresolved issue and boundary

The required Gemini model request must succeed before Phase D can receive PASS. Its HTTP 404 remains unresolved; two required end-to-end smoke answers and real cited generation are still outstanding. The approved extraction remedy succeeded for narrative content, and real retrieval is preserved for reuse. No further dependency or model change was made.

AGENTS.md, the analytical CSV, Delta tables, Phase B/C evidence, Compose configuration, and unrelated rubric statuses remain unchanged. Earlier blocker, pypdf failure, Windows encoding failure, layout error and Gemini failure evidence remain preserved. No commit, Airflow project DAG, Great Expectations gate, OpenLineage project event, UI or Phase E work was performed. **Phase D: FAIL; stopped at the configured-model execution blocker.**
