"""AquaLens 2030 end-to-end Airflow DAG with a blocking GX quality gate."""

import json
from pathlib import Path

from airflow.sdk import dag, get_current_context, task


DAG_ID = "aqualens_2030_pipeline"


def _failure_demo_enabled() -> bool:
    context = get_current_context()
    value = context.get("params", {}).get("quality_failure_demo", False)
    dag_run = context.get("dag_run")
    if dag_run is not None and getattr(dag_run, "conf", None):
        value = dag_run.conf.get("quality_failure_demo", value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


@dag(
    dag_id=DAG_ID,
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["aqualens2030", "capstone"],
    params={"quality_failure_demo": False},
)
def aqualens_2030_pipeline():

    @task(retries=0)
    def produce_events() -> dict:
        from src.common.config import IngestionConfig
        from src.ingestion.producer import produce

        failure_demo = _failure_demo_enabled()
        manifest = produce(
            IngestionConfig.from_env(),
            Path("tests/fixtures/malformed_water_event.json"),
            Path("tests/fixtures/negative_water_event.json") if failure_demo else None,
        )
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        return {
            "run_id": payload["run_id"],
            "manifest_path": str(manifest),
            "failure_demo": failure_demo,
            "produced_count": payload["produced_count"],
        }

    @task(retries=0)
    def consume_and_validate(producer_meta: dict) -> dict:
        from src.common.config import IngestionConfig
        from src.ingestion.consumer import consume

        result = consume(
            IngestionConfig.from_env(), Path(producer_meta["manifest_path"])
        )
        return {
            **producer_meta,
            "accepted_path": result["accepted_path"],
            "accepted_count": result["accepted_count"],
            "quarantined_count": result["quarantined_count"],
        }

    @task(retries=0)
    def bronze_load(ingestion_meta: dict) -> dict:
        from deltalake import DeltaTable
        from src.lakehouse.bronze import append_bronze

        run_root = Path("storage/delta/airflow") / ingestion_meta["run_id"]
        bronze = run_root / "bronze"
        if DeltaTable.is_deltatable(str(bronze)):
            raise FileExistsError(f"Bronze proof path already exists: {bronze}")
        append_bronze(Path(ingestion_meta["accepted_path"]), bronze)
        count = DeltaTable(str(bronze)).to_pyarrow_table().num_rows
        print(json.dumps({"action": "bronze_complete", "path": str(bronze), "rows": count}), flush=True)
        return {**ingestion_meta, "run_root": str(run_root), "bronze_path": str(bronze), "bronze_count": count}

    @task(retries=0)
    def silver_merge(bronze_meta: dict) -> dict:
        from deltalake import DeltaTable
        from src.lakehouse.silver import merge_silver

        silver = Path(bronze_meta["run_root"]) / "silver"
        metrics = merge_silver(Path(bronze_meta["bronze_path"]), silver)
        count = DeltaTable(str(silver)).to_pyarrow_table().num_rows
        print(json.dumps({"action": "silver_complete", "path": str(silver), "rows": count, "merge_metrics": metrics}, default=str), flush=True)
        return {**bronze_meta, "silver_path": str(silver), "silver_count": count, "merge_metrics": metrics}

    @task(retries=0)
    def schema_enforcement_proof(silver_meta: dict) -> dict:
        from src.lakehouse.bronze import read_accepted
        from src.lakehouse.schema_proof import prove_schema_rejection

        proof_path = Path(silver_meta["run_root"]) / "schema_enforcement_proof"
        proof = prove_schema_rejection(
            proof_path, read_accepted(Path(silver_meta["accepted_path"]))
        )
        print(json.dumps({"action": "schema_enforcement_proven", "path": str(proof_path), "unchanged": proof["unchanged"]}), flush=True)
        return {**silver_meta, "schema_proof_path": str(proof_path), "schema_proof_unchanged": bool(proof["unchanged"])}

    @task(retries=0)
    def quality_gate(schema_meta: dict) -> dict:
        from src.quality.gate import validate_silver

        label = "failure" if schema_meta["failure_demo"] else "success"
        evidence = Path("docs/evidence/quality") / f"{label}_{schema_meta['run_id']}.json"
        result = validate_silver(Path(schema_meta["silver_path"]), evidence)
        return {**schema_meta, "quality_evidence": str(evidence), "quality_success": result["success"]}

    @task(retries=0)
    def gold_build(quality_meta: dict) -> dict:
        from deltalake import DeltaTable
        from src.lakehouse.gold import build_gold

        gold = Path(quality_meta["run_root"]) / "gold_regional_water_profile"
        build_gold(Path(quality_meta["silver_path"]), gold)
        count = DeltaTable(str(gold)).to_pyarrow_table().num_rows
        if count != 13:
            raise AssertionError(f"Expected 13 regional Gold rows, found {count}")
        print(json.dumps({"action": "gold_complete", "path": str(gold), "rows": count}), flush=True)
        return {**quality_meta, "gold_path": str(gold), "gold_count": count}

    @task(retries=0)
    def rag_chunk_and_index(gold_meta: dict) -> dict:
        from src.rag.chunking import make_chunks
        from src.rag.retrieval import Retriever

        run_id = gold_meta["run_id"]
        rag_root = Path("storage/rag/airflow") / run_id
        chunks_path = rag_root / "chunks.json"
        chroma_path = rag_root / "chroma"
        rag_root.mkdir(parents=True, exist_ok=False)

        chunks, extraction = make_chunks()
        chunks_path.write_text(
            json.dumps({"chunks": chunks, "documents": extraction}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        retriever = Retriever(chunks, chroma_path)
        if retriever.collection.count() != len(chunks):
            raise AssertionError("Chroma count does not match chunk count")
        print(json.dumps({"action": "rag_index_complete", "chunks": len(chunks), "chroma_path": str(chroma_path)}), flush=True)
        return {**gold_meta, "rag_chunks_path": str(chunks_path), "rag_chroma_path": str(chroma_path), "rag_chunk_count": len(chunks)}

    @task(retries=0)
    def rag_grounded_answer_smoke_test(rag_meta: dict) -> dict:
        from src.rag.generation import generate
        from src.rag.retrieval import Retriever

        payload = json.loads(Path(rag_meta["rag_chunks_path"]).read_text(encoding="utf-8"))
        chunks = payload["chunks"]
        retriever = Retriever.open_existing(chunks, Path(rag_meta["rag_chroma_path"]))
        query = "ما الأهداف الاستراتيجية المتعلقة بإدارة الطلب على المياه والمحافظة على الموارد المائية والبيئة؟"
        retrieval = retriever.retrieve(query)
        answer = generate(query, retrieval["final_chunks"])
        if answer.get("insufficient_evidence") or not answer.get("citations"):
            raise AssertionError("Grounded RAG smoke query did not return supported citations")
        final_ids = {chunk["chunk_id"] for chunk in retrieval["final_chunks"]}
        cited_ids = {citation["chunk_id"] for citation in answer["citations"]}
        if not cited_ids.issubset(final_ids):
            raise AssertionError("RAG answer cited chunks outside final retrieved context")

        evidence = Path("docs/evidence/rag") / f"airflow_{rag_meta['run_id']}.json"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text(
            json.dumps({"query": query, "retrieval": retrieval, "answer": answer}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"action": "rag_grounded_smoke_complete", "citations": len(answer["citations"]), "evidence": str(evidence)}), flush=True)
        return {
            "run_id": rag_meta["run_id"],
            "result": "PASS",
            "quality_evidence": rag_meta["quality_evidence"],
            "gold_path": rag_meta["gold_path"],
            "rag_evidence": str(evidence),
        }

    producer_meta = produce_events()
    ingestion_meta = consume_and_validate(producer_meta)
    bronze_meta = bronze_load(ingestion_meta)
    silver_meta = silver_merge(bronze_meta)
    schema_meta = schema_enforcement_proof(silver_meta)
    quality_meta = quality_gate(schema_meta)
    gold_meta = gold_build(quality_meta)
    rag_meta = rag_chunk_and_index(gold_meta)
    return rag_grounded_answer_smoke_test(rag_meta)


aqualens_2030_pipeline()
