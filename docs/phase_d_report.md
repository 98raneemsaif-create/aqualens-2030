# Phase D — Official-Document Hybrid RAG

**PASS — 09 September 2026.** Phase D now demonstrates the complete RAG pipeline required by the capstone: deterministic document chunking, multilingual embeddings, a real persistent vector store, dense retrieval, BM25 keyword retrieval, RRF fusion, cross-encoder reranking, grounded LLM generation, and citations traceable to the retrieved official source chunks. The final generation proof used the explicitly approved `gemini-3.5-flash` Developer API fallback after `gemini-2.5-flash` returned HTTP 404 for this account/runtime. No Phase E work was performed.

## Final result

| Requirement | Observed result |
| --- | --- |
| Official corpus | MEWA National Water Strategy 2030 + GASTAT Methodology and Quality Report of Water Accounts only |
| Extraction | MEWA: PyMuPDF 1.28.2 default unsorted narrative extraction; GASTAT: pypdf 6.17.0 plain extraction |
| Chunking | 445 deterministic chunks: 391 MEWA + 54 GASTAT |
| Embeddings | `intfloat/multilingual-e5-small`, normalized 384-dimensional vectors, CPU |
| Vector store | ChromaDB `PersistentClient`, collection `aqualens_official_docs`, 445 persisted records |
| Keyword retrieval | Real `BM25Okapi` over the same 445-chunk corpus |
| Hybrid fusion | Dense top 8 + BM25 top 8, RRF `k=60`, fused top 10 |
| Reranking | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`, final top 4, CPU |
| LLM generation | `gemini-3.5-flash`, temperature 0, explicit Gemini Developer API client |
| Grounding proof | Two supported questions answered only from supplied retrieved chunks |
| Insufficient-evidence proof | Unsupported Mars-tariff query returned insufficient evidence with zero citations |
| Citation proof | Every emitted citation resolves to a supplied final chunk and carries title, physical PDF page, and canonical official URL |

All nine scored RAG component rows in `docs/rubric_matrix.md` are VERIFIED. This is evidence of requirement coverage, not a claim of an evaluator-awarded score.

## Blocker history and approved runtime amendments

Phase D preserved all unsuccessful attempts instead of overwriting them:

1. The original runtime had no PDF parser, so execution stopped at the prerequisite gate.
2. `pypdf==6.17.0` was explicitly approved as the first narrow dependency amendment. It extracted GASTAT reliably but MEWA Arabic prose failed the readability gate because of ordering/encoding defects.
3. `PyMuPDF==1.28.2` was explicitly approved as the second narrow extraction amendment. Its default `page.get_text("text")` mode produced readable MEWA narrative text with physical-page traceability. Sorted/layout modes were rejected and their evidence retained.
4. The frozen `gemini-2.5-flash` generation request returned HTTP 404 even when an explicit `genai.Client(api_key=os.environ["GEMINI_API_KEY"])` Developer API client was used. No competing Google key, Vertex/enterprise mode, or custom base URL was present.
5. The explicitly approved `gemini-3.5-flash` fallback returned `OK` in the minimal access test and then completed all three real RAG smoke queries. No arbitrary model search or architecture change was made.

`requirements/runtime.in` and `requirements/runtime.lock` contain the original 195 pins plus the two approved parser pins. Runtime evidence confirms Python 3.11.15, Airflow 3.3.1, pypdf 6.17.0, PyMuPDF 1.28.2, all 197 exact package versions, and `pip check` success. Earlier blocker/build/parser/model-failure evidence remains under `docs/evidence/phase_d/`.

## Official sources and provenance

The core RAG corpus contains only the two approved official Saudi government documents. No blog, unofficial mirror, generated summary, or secondary source was indexed.

| Source | Issuer | SHA-256 |
| --- | --- | --- |
| National Water Strategy 2030 | Ministry of Environment, Water and Agriculture (MEWA) | `4abe289ef6c5053d0d819c33e89f3af82f81356e241ec893b20bfc95e31db71c` |
| Methodology and Quality Report of Water Accounts | General Authority for Statistics (GASTAT) | `1ccafbd53efac42a1f8e116b4e46e848c7791a67051c547df69b63cf13b8867a` |

The preserved PDF hashes still match their metadata files. Metadata retains title, issuing organization, canonical official URL, retrieval timestamp, language, source format, and content hash. Citations use one-based **physical PDF page** identity rather than assuming printed-page numbering.

## Extraction decision

### MEWA

Three PyMuPDF modes were evaluated against the preserved official PDF:

| Mode | Nonempty pages | Characters | Decision |
| --- | ---: | ---: | --- |
| `page.get_text("text")` | 122 / 125 | 202,944 | **Selected** — narrative Arabic is readable enough for retrieval |
| `page.get_text("text", sort=True)` | 122 / 125 | 405,497 | Rejected — Arabic word/prose ordering degraded |
| `python -m pymupdf gettext -mode layout` | 119 / 125 | 443,782 | Rejected — reversed character ordering and page-level errors |

The selected MEWA path intentionally indexes narrative prose only. Numeric/table-like fragments that could not be trusted are excluded rather than reconstructed. No string reversal, OCR, AI rewriting, or hardcoded strategy text is used.

### GASTAT

The verified pypdf plain extraction is retained: 20/20 pages with readable text and 31,304 extracted characters.

Extraction evidence is preserved in:

- `docs/evidence/phase_d/pypdf_failure_report.md`
- `docs/evidence/phase_d/pymupdf/summary.json`
- `docs/evidence/phase_d/pymupdf/viability_review.json`
- `docs/evidence/phase_d/extraction/`

## Chunking, embeddings, vector store, and retrieval

`src/rag/chunking.py` creates deterministic chunks targeting approximately 800 characters with 120-character overlap without crossing physical-page/excluded-run boundaries. Each chunk retains stable metadata including chunk ID, document title, organization, physical page, canonical URL, language, source hash, extraction method, and source location metadata.

Actual corpus size:

- MEWA: **391 chunks**
- GASTAT: **54 chunks**
- Total: **445 chunks**

`src/rag/retrieval.py` uses:

- embedding model: `intfloat/multilingual-e5-small`
- E5 `passage:` / `query:` conventions
- normalized 384-dimensional embeddings
- ChromaDB `PersistentClient`
- collection: `aqualens_official_docs`
- BM25Okapi over the same corpus
- dense top 8
- BM25 top 8
- Reciprocal Rank Fusion with `k=60`
- fused top 10
- cross-encoder: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`
- final reranked top 4

The persisted Chroma collection contains all 445 records. A separate process reopened the collection and verified stored documents/metadata, vector dimensions and normalization, both retrieval branches, independent RRF recomputation, finite cross-encoder scores, and final reranking order.

Primary retrieval evidence:

- `docs/evidence/phase_d/402947a2-1f21-445a-82a0-e0e3e4be3b70/chunks.json`
- `docs/evidence/phase_d/402947a2-1f21-445a-82a0-e0e3e4be3b70/index.json`
- `docs/evidence/phase_d/retrieval_verification.log`
- `docs/evidence/phase_d/402947a2-1f21-445a-82a0-e0e3e4be3b70/retrieval_verification.json`

## Gemini access diagnosis and approved fallback

The safe diagnostic did not record any credential value. It established:

- `GEMINI_API_KEY` present
- `GOOGLE_API_KEY` absent
- Vertex/enterprise mode absent/disabled
- no custom Gemini/Vertex base URL
- explicit Developer API client used

Minimal model-access results:

| Model | Result |
| --- | --- |
| `gemini-2.5-flash` | HTTP 404 |
| `gemini-3.5-flash` | HTTP 200; returned exactly `OK` |

The final generation code therefore uses the explicitly approved `gemini-3.5-flash` fallback. `google-genai==2.17.0` and the rest of the architecture remain unchanged. The original 2.5 failure remains documented in `docs/evidence/phase_d/gemini_25_failure_report.md` and the safe diagnostic in `docs/evidence/phase_d/gemini_diagnostic.json`.

## Real grounded-generation proof

The generation-only resume reused the already verified 445-record Chroma corpus and cached retrieval models. It did **not** re-extract, re-chunk, re-embed, or re-index the corpus. The before/after persistent-corpus SHA-256 is identical:

`4cebeddc22c3aa2d8c1d6359b5dfc381658ed123587ab42d9a8e6d804611357a`

The proof executed all three configured queries:

### Query 1 — Arabic strategy context

Question:

`ما الأهداف الاستراتيجية المتعلقة بإدارة الطلب على المياه والمحافظة على الموارد المائية والبيئة؟`

Observed result:

- dense results: 8
- BM25 results: 8
- fused candidates: 10
- cross-encoder final chunks: 4
- grounded answer: produced in Arabic
- citations emitted: **3**
- cited evidence resolves to official MEWA chunks/pages/URL
- manual statement-support review: PASS
- unsupported claims found: none
- water-concentration-to-risk inference: none

### Query 2 — GASTAT methodology context

Question:

`What are the main data sources and statistical scope of Saudi Arabia's water accounts?`

Observed result:

- dense results: 8
- BM25 results: 8
- fused candidates: 10
- cross-encoder final chunks: 4
- grounded answer: produced in English
- citations emitted: **4**
- cited evidence resolves to official GASTAT chunks/pages/URL
- manual statement-support review: PASS
- unsupported claims found: none

### Query 3 — controlled insufficient evidence

Question:

`What is the approved water tariff for a permanent colony on Mars in 2045?`

Observed result:

- all retrieval/reranking stages still executed
- `insufficient_evidence = true`
- answer explicitly states that supplied context contains no Mars/space-colony/2045 tariff information
- citations emitted: **0**
- no tariff was invented

For all emitted citations, the validation script confirmed that the cited chunk ID was actually present in the final retrieved context and that citation metadata includes document title, physical page, and canonical official URL.

Generation evidence:

- `docs/evidence/phase_d/generation_resume.log`
- `docs/evidence/phase_d/generation_resume/result.json`
- `docs/evidence/phase_d/generation_resume/reuse.json`
- `docs/evidence/phase_d/generation_resume/query_1_answer.json`
- `docs/evidence/phase_d/generation_resume/query_1_validation.json`
- `docs/evidence/phase_d/generation_resume/query_2_answer.json`
- `docs/evidence/phase_d/generation_resume/query_2_validation.json`
- `docs/evidence/phase_d/generation_resume/query_3_answer.json`
- `docs/evidence/phase_d/generation_resume/query_3_validation.json`
- `docs/evidence/phase_d/generation_resume/claim_support_review.json`

## Tests and execution evidence

- Seven focused RAG tests passed in `docs/evidence/phase_d/unit_tests.log`.
- Two focused generation/citation contract tests passed in `docs/evidence/phase_d/generation_contract_tests.log`.
- Real model/vector-store/retrieval proof executed before the initial 2.5 generation failure and is retained in `docs/evidence/phase_d/rag_execution.log`.
- Real 3.5 generation/citation proof completed with exit code 0 in `docs/evidence/phase_d/generation_resume.log`.
- Independent persistent-store/retrieval verification passed in `docs/evidence/phase_d/retrieval_verification.log`.
- Manual claim-support review for every generated statement passed in `docs/evidence/phase_d/generation_resume/claim_support_review.json`.
- The generation resume confirms `corpus_unchanged=true`; no reindexing occurred.

A prior runtime sample during retrieval/model execution used approximately 2.39 GiB of Airflow's 5 GiB memory limit. This is a point-in-time observation, not a performance benchmark.

## Rubric disposition

The complete RAG category is now demonstrated:

1. Document chunking — VERIFIED
2. Embeddings — VERIFIED
3. Real vector store — VERIFIED
4. Dense/vector retrieval — VERIFIED
5. Keyword/BM25 retrieval — VERIFIED
6. Fusion of dense and keyword search — VERIFIED
7. Cross-encoder reranking — VERIFIED
8. Answers grounded in retrieved context — VERIFIED
9. Citations in answers — VERIFIED

The grounded-answer/citation execution-evidence checklist row is also VERIFIED using the actual generation-resume artifacts and claim-support review. No Orchestration, Great Expectations, OpenLineage, or unrelated submission status is advanced by Phase D.

## Contributor files added or changed in Phase D

Phase D includes the parser amendments, official source snapshots and provenance metadata, RAG implementation/tests, execution evidence, and this report. Key implementation files are:

- `src/rag/extraction.py`
- `src/rag/chunking.py`
- `src/rag/retrieval.py`
- `src/rag/generation.py`
- `src/rag/pipeline.py`
- `tests/test_rag.py`
- `tests/verify_phase_d_retrieval.py`
- `tests/diagnose_gemini.py`
- `tests/resume_rag_generation.py`
- `rag/sources/mewa_strategy.pdf`
- `rag/sources/mewa_strategy.json`
- `rag/sources/gastat_methodology.pdf`
- `rag/sources/gastat_methodology.json`
- `requirements/runtime.in`
- `requirements/runtime.lock`
- `requirements/README.md`
- `docs/rubric_matrix.md`
- `docs/evidence/phase_d/`

Generated model caches and persistent Chroma storage remain gitignored. The official analytical CSV and Phase B/C evidence were not used as writable RAG inputs.

## Security and phase boundary

The Gemini key value was not written to reports or evidence. The existing safety scan found no API-key value in code/evidence. The generation code reads `GEMINI_API_KEY` from the environment and uses an explicit Developer API client.

Kafka was not required for this standalone RAG phase. No project Airflow DAG, Great Expectations gate, OpenLineage project-stage execution, Streamlit UI, analytical CSV modification, or Delta-table modification is claimed here.

**Phase D: PASS. No unresolved Phase D blocker remains. Stop before Phase E.**
