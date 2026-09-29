"""nDCG@k and Recall@k matching BEIR / pytrec_eval definitions."""
import math


def _ranked(scores: dict[str, float]) -> list[str]:
    # pytrec_eval tie-break: score desc, then doc_id desc
    return [d for d, _ in sorted(scores.items(), key=lambda x: (x[1], x[0]), reverse=True)]


def ndcg_at_k(rels: dict[str, int], scores: dict[str, float], k: int) -> float:
    ranked = _ranked(scores)[:k]
    dcg = sum(rels.get(d, 0) / math.log2(i + 2) for i, d in enumerate(ranked))
    ideal = sorted((r for r in rels.values() if r > 0), reverse=True)[:k]
    idcg = sum(r / math.log2(i + 2) for i, r in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


def recall_at_k(rels: dict[str, int], scores: dict[str, float], k: int) -> float:
    relevant = {d for d, r in rels.items() if r > 0}
    if not relevant:
        return 0.0
    return len(relevant & set(_ranked(scores)[:k])) / len(relevant)


NDCG_KS = (10, 100)
RECALL_KS = (1, 3, 5, 10, 20, 100)


def evaluate(qrels: dict, run: dict[str, dict[str, float]]) -> dict[str, float]:
    """Mean metrics over the queries in `run` (BEIR averages over evaluated queries)."""
    qids = [q for q in run if q in qrels]
    out = {}
    for k in NDCG_KS:
        out[f"nDCG@{k}"] = sum(ndcg_at_k(qrels[q], run[q], k) for q in qids) / len(qids)
    for k in RECALL_KS:
        out[f"Recall@{k}"] = sum(recall_at_k(qrels[q], run[q], k) for q in qids) / len(qids)
    return out


if __name__ == "__main__":
    # self-test against hand-computed values
    assert ndcg_at_k({"a": 1}, {"a": 1.0, "b": 0.5}, 10) == 1.0
    assert abs(ndcg_at_k({"a": 1}, {"b": 1.0, "a": 0.5}, 10) - 1 / math.log2(3)) < 1e-12
    assert recall_at_k({"a": 1, "b": 1}, {"a": 3, "c": 2, "b": 1}, 2) == 0.5
    assert ndcg_at_k({"a": 1}, {"b": 1.0}, 10) == 0.0
    print("metrics self-test OK")
