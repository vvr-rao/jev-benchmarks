"""First stage: Chroma + built-in ONNX all-MiniLM-L6-v2. Caches top-N candidates per query.

The cached candidate list is the single input to every reranker, so all of them
rescore the exact same documents.
"""
import json
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from bench.data import load

ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIR = ROOT / "chroma"
CANDIDATES = ROOT / "results" / "cache" / "candidates.json"
COLLECTION = "scifact"
BATCH = 32


def build_index(corpus: dict[str, str]):
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    col = client.get_or_create_collection(
        COLLECTION, embedding_function=DefaultEmbeddingFunction(), metadata={"hnsw:space": "cosine"}
    )
    if col.count() == len(corpus):
        return col
    done = set(col.get(include=[])["ids"])  # resume after interruption
    ids = [d for d in corpus if d not in done]
    for i in range(0, len(ids), BATCH):
        chunk = ids[i : i + BATCH]
        col.upsert(ids=chunk, documents=[corpus[d] for d in chunk])
        print(f"  indexed {len(done) + min(i + BATCH, len(ids))}/{len(corpus)}", flush=True)
    return col


def candidates(depth: int = 100) -> dict[str, dict[str, float]]:
    """{qid: {doc_id: cosine_similarity}} for the top-`depth` docs; cached on disk."""
    if CANDIDATES.exists():
        cached = json.loads(CANDIDATES.read_text())
        if cached["depth"] == depth:
            return cached["run"]
    corpus, queries, _ = load()
    col = build_index(corpus)
    qids = list(queries)
    res = col.query(query_texts=[queries[q] for q in qids], n_results=depth)
    run = {q: {d: 1.0 - dist for d, dist in zip(ids, dists)} for q, ids, dists in zip(qids, res["ids"], res["distances"])}
    CANDIDATES.parent.mkdir(parents=True, exist_ok=True)
    CANDIDATES.write_text(json.dumps({"depth": depth, "run": run}))
    return run


if __name__ == "__main__":
    from bench.metrics import evaluate

    run = candidates()
    _, _, qrels = load()
    for k, v in evaluate(qrels, run).items():
        print(f"{k:>10}: {v:.4f}")
