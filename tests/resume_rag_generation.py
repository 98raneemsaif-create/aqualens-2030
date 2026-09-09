"""Only missing real generation proofs, reusing the verified 445-chunk store."""
import hashlib
import json
from pathlib import Path

from src.rag.retrieval import Retriever
from src.rag.generation import generate, MODEL
from src.rag.pipeline import QUERIES

previous = Path('docs/evidence/phase_d/402947a2-1f21-445a-82a0-e0e3e4be3b70')
output = Path('docs/evidence/phase_d/generation_resume')
output.mkdir(exist_ok=False)
chunks = json.loads((previous/'chunks.json').read_text())['chunks']
index = json.loads((previous/'index.json').read_text())
retriever = Retriever.open_existing(chunks,index['path'])
def snapshot():
    stored = retriever.collection.get(include=['documents','metadatas','embeddings'])
    payload = sorted((i,d,m,e.tolist()) for i,d,m,e in zip(stored['ids'],stored['documents'],stored['metadatas'],stored['embeddings']))
    return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
before = snapshot()
def save(name,data):
    (output/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
save('reuse.json',dict(previous_proof=str(previous),collection_path=index['path'],chunk_count=len(chunks),
    model=MODEL,corpus_before_sha256=before,cached_models_only=True,reindexed=False))
for number,query in enumerate(QUERIES,1):
    retrieved = retriever.retrieve(query)
    save(f'query_{number}_retrieval.json',retrieved)
    answer = generate(query,retrieved['final_chunks'])
    save(f'query_{number}_answer.json',answer)
    available={c['chunk_id']:c for c in retrieved['final_chunks']}
    assert answer['insufficient_evidence'] == (number==3)
    if number < 3:
        assert answer['citations']
    for citation in answer['citations']:
        assert citation['chunk_id'] in available
        assert citation['page']>0 and citation['title'] and citation['canonical_url'].startswith('https://')
        assert available[citation['chunk_id']]['metadata']['canonical_url']==citation['canonical_url']
    save(f'query_{number}_validation.json',dict(citations_resolve=True,
        cited_chunks=[c['chunk_id'] for c in answer['citations']],physical_page_metadata=True,
        insufficient_evidence=answer['insufficient_evidence']))
    print(f'Query {number}: generation succeeded; citations={len(answer["citations"])}; insufficient={answer["insufficient_evidence"]}',flush=True)
after=snapshot()
assert before==after
save('result.json',dict(result='PASS',queries=3,model=MODEL,corpus_unchanged=True,
    corpus_before_sha256=before,corpus_after_sha256=after))
print('Generation and citation execution PASS; manual claim-support review still required.',flush=True)
