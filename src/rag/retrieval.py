"""Real CPU models, persistent Chroma, BM25 and reciprocal rank fusion."""
import re
import unicodedata

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder

EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
EMBEDDING_REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
RERANKER_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
RERANKER_REVISION = "1427fd652930e4ba29e8149678df786c240d8825"


def tokens(text):
    text = unicodedata.normalize("NFKC", text).lower().replace("ـ", "")
    text = re.sub(r"[\u064b-\u065f\u0670]", "", text)
    text = text.translate(str.maketrans("أإآى", "اااي"))
    return re.findall(r"\w+", text)


def e5_inputs(texts, query=False):
    return [("query: " if query else "passage: ") + t for t in texts]


def rrf(dense, keyword, k=60):
    scores = {}
    for branch in (dense, keyword):
        for rank, row in enumerate(branch, 1):
            scores[row['chunk_id']] = scores.get(row['chunk_id'], 0) + 1 / (k + rank)
    return [dict(chunk_id=i, rrf_score=s) for i,s in sorted(scores.items(), key=lambda x:(-x[1],x[0]))[:10]]


class Retriever:
    @classmethod
    def open_existing(cls, chunks, path):
        """Reuse persisted vectors and cached models; never re-index documents."""
        self = cls.__new__(cls)
        self.chunks = {c['chunk_id']:c for c in chunks}
        self.ids = list(self.chunks)
        self.client = chromadb.PersistentClient(path=str(path))
        self.collection = self.client.get_collection("aqualens_official_docs")
        if set(self.collection.get()['ids']) != set(self.ids):
            raise ValueError("Existing corpus does not match proof chunks")
        self.encoder = SentenceTransformer(EMBEDDING_MODEL, revision=EMBEDDING_REVISION,
                                          device="cpu", local_files_only=True)
        self.reranker = CrossEncoder(RERANKER_MODEL, revision=RERANKER_REVISION,
                                    device="cpu", local_files_only=True)
        self.bm25 = BM25Okapi([tokens(c['text']) for c in chunks])
        return self

    def __init__(self, chunks, path):
        self.chunks = {c['chunk_id']:c for c in chunks}
        self.ids = list(self.chunks)
        self.encoder = SentenceTransformer(EMBEDDING_MODEL, revision=EMBEDDING_REVISION, device="cpu")
        self.reranker = CrossEncoder(RERANKER_MODEL, revision=RERANKER_REVISION, device="cpu")
        self.client = chromadb.PersistentClient(path=str(path))
        self.collection = self.client.get_or_create_collection("aqualens_official_docs", metadata={"hnsw:space":"cosine"})
        # Each proof uses a fresh path; explicit corpus equality prevents stale mixing.
        if self.collection.count():
            if set(self.collection.get()['ids']) != set(self.ids):
                raise ValueError("Persistent collection belongs to a different corpus")
        self.vectors = self.encoder.encode(e5_inputs([c['text'] for c in chunks]), normalize_embeddings=True,
                                           batch_size=16, show_progress_bar=False)
        self.collection.upsert(ids=self.ids, documents=[c['text'] for c in chunks],
                               metadatas=[c['metadata'] for c in chunks], embeddings=self.vectors.tolist())
        self.bm25 = BM25Okapi([tokens(c['text']) for c in chunks])

    def retrieve(self, query):
        vector = self.encoder.encode(e5_inputs([query], query=True), normalize_embeddings=True)
        result = self.collection.query(query_embeddings=vector.tolist(), n_results=min(8,len(self.ids)), include=['distances'])
        dense = [dict(chunk_id=i, distance=float(d), rank=n+1) for n,(i,d) in enumerate(zip(result['ids'][0],result['distances'][0]))]
        scores = self.bm25.get_scores(tokens(query))
        indices = sorted(range(len(self.ids)), key=lambda i:(-scores[i],self.ids[i]))[:8]
        keyword = [dict(chunk_id=self.ids[i], score=float(scores[i]), rank=n+1) for n,i in enumerate(indices)]
        fused = rrf(dense, keyword)
        relevance = self.reranker.predict([(query,self.chunks[r['chunk_id']]['text']) for r in fused])
        reranked = sorted([dict(**r,cross_encoder_score=float(s)) for r,s in zip(fused,relevance)],
                          key=lambda r:(-r['cross_encoder_score'],r['chunk_id']))
        return dict(query=query,dense=dense,bm25=keyword,rrf_k=60,fused=fused,reranked=reranked,
                    final_chunks=[self.chunks[r['chunk_id']] for r in reranked[:4]])
