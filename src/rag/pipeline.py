"""Standalone Phase D proof; deliberately no Airflow DAG or lineage execution."""
import json
from pathlib import Path
from uuid import uuid4

import chromadb
import numpy as np

from src.rag.chunking import make_chunks
from src.rag.retrieval import Retriever, EMBEDDING_MODEL, EMBEDDING_REVISION, RERANKER_MODEL, RERANKER_REVISION
from src.rag.generation import generate

QUERIES = [
    "ما الأهداف الاستراتيجية المتعلقة بإدارة الطلب على المياه والمحافظة على الموارد المائية والبيئة؟",
    "What are the main data sources and statistical scope of Saudi Arabia's water accounts?",
    "What is the approved water tariff for a permanent colony on Mars in 2045?",
]


def main():
    proof_id = str(uuid4())
    evidence = Path('docs/evidence/phase_d') / proof_id
    evidence.mkdir(parents=True, exist_ok=False)
    storage = Path('storage/rag') / proof_id / 'chroma'
    def save(name, value):
        (evidence / name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Phase D proof: {proof_id}',flush=True)
    chunks, extraction = make_chunks()
    assert len({c['chunk_id'] for c in chunks}) == len(chunks)
    assert {c['metadata']['source_id'] for c in chunks} == {'mewa_strategy','gastat_methodology'}
    save('chunks.json',dict(documents=extraction,chunks=chunks))
    print(json.dumps(extraction),flush=True)
    retriever = Retriever(chunks,storage)
    assert retriever.vectors.shape == (len(chunks),384)
    assert np.allclose(np.linalg.norm(retriever.vectors,axis=1),1,atol=1e-5)
    reopened = chromadb.PersistentClient(path=str(storage)).get_collection('aqualens_official_docs')
    assert reopened.count() == len(chunks)
    sample = reopened.get(ids=[chunks[0]['chunk_id']],include=['metadatas','documents'])
    assert sample['metadatas'][0] == chunks[0]['metadata']
    save('index.json',dict(embedding_model=EMBEDDING_MODEL,embedding_revision=EMBEDDING_REVISION,
        reranker_model=RERANKER_MODEL,reranker_revision=RERANKER_REVISION,device='cpu',
        dimension=384,normalized=True,collection=reopened.name,count=reopened.count(),path=str(storage),sample=sample))
    print(f'Real Chroma collection indexed: {len(chunks)} normalized 384-dimensional vectors',flush=True)
    for number,query in enumerate(QUERIES,1):
        result = retriever.retrieve(query)
        assert len(result['dense']) == len(result['bm25']) == 8
        assert len(result['final_chunks']) == 4
        save(f'query_{number}_retrieval.json',result)
        answer = generate(query,result['final_chunks'])
        save(f'query_{number}_answer.json',answer)
        assert answer['insufficient_evidence'] == (number == 3)
        if number < 3:
            assert answer['citations']
        print(f'Query {number} completed; insufficient_evidence={answer["insufficient_evidence"]}; citations={len(answer["citations"])}',flush=True)
    save('result.json',dict(result='PASS',queries=3,proof_id=proof_id,storage=str(storage)))
    print('Phase D real RAG execution PASS',flush=True)


if __name__ == '__main__':
    main()
