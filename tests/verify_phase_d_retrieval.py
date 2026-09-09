"""Independent saved-proof checks; no new model or Gemini call."""
import json
from pathlib import Path
import sys

import chromadb
import numpy as np

root = Path(sys.argv[1])
corpus = json.loads((root / 'chunks.json').read_text())
index = json.loads((root / 'index.json').read_text())
retrieval = json.loads((root / 'query_1_retrieval.json').read_text())
chunks = {c['chunk_id']:c for c in corpus['chunks']}
collection = chromadb.PersistentClient(path=index['path']).get_collection('aqualens_official_docs')
assert collection.count() == len(chunks) == 445
stored = collection.get(include=['documents','metadatas','embeddings'])
assert set(stored['ids']) == set(chunks)
vectors = np.asarray(stored['embeddings'])
assert vectors.shape == (445,384)
assert np.allclose(np.linalg.norm(vectors,axis=1),1,atol=1e-5)
for i,chunk_id in enumerate(stored['ids']):
    assert stored['documents'][i] == chunks[chunk_id]['text']
    assert stored['metadatas'][i] == chunks[chunk_id]['metadata']
assert len(retrieval['dense']) == len(retrieval['bm25']) == 8
assert any(r['score'] > 0 for r in retrieval['bm25'])
scores = {}
for branch in ['dense','bm25']:
    for rank,row in enumerate(retrieval[branch],1):
        assert row['rank'] == rank
        scores[row['chunk_id']] = scores.get(row['chunk_id'],0) + 1/(60+rank)
expected = sorted(scores,key=lambda i:(-scores[i],i))[:10]
assert [r['chunk_id'] for r in retrieval['fused']] == expected
for row in retrieval['fused']:
    assert abs(row['rrf_score'] - scores[row['chunk_id']]) < 1e-12
reranked = retrieval['reranked']
assert set(r['chunk_id'] for r in reranked) == set(expected)
assert all(np.isfinite(r['cross_encoder_score']) for r in reranked)
assert reranked == sorted(reranked,key=lambda r:(-r['cross_encoder_score'],r['chunk_id']))
assert [c['chunk_id'] for c in retrieval['final_chunks']] == [r['chunk_id'] for r in reranked[:4]]
for c in retrieval['final_chunks']:
    assert c == chunks[c['chunk_id']]
result = dict(result='PASS',separate_process_persistence=True,stored_chunks=445,
    embedding_shape=list(vectors.shape),unit_norm=True,metadata_matches=True,
    dense_results=8,bm25_results=8,rrf_independently_recomputed=True,
    cross_encoder_order_verified=True,final_evidence_chunks=4,
    grounded_answer_verified=False,citations_verified=False)
(root/'retrieval_verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
