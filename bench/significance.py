"""Paired bootstrap significance tests between rerankers, using cached per-query scores.

  uv run python -m bench.significance
"""
import itertools
import json
import random

from bench.data import load
from bench.metrics import ndcg_at_k, recall_at_k
from bench.retrieve import candidates
from bench.run import CACHE, RESULTS, load_cache, tie_break_by_first_stage

RERANKERS = ("jev", "cohere", "qwen8b", "qwen")
METRICS = (("nDCG@10", ndcg_at_k, 10), ("Recall@1", recall_at_k, 1), ("Recall@5", recall_at_k, 5))
B = 10_000


def main():
    _, queries, qrels = load()
    cands = candidates(100)
    qids = [q for q in queries if q in cands]
    per = {}
    for n in RERANKERS:
        cache = load_cache(CACHE / f"{n}.jsonl")
        per[n] = {q: tie_break_by_first_stage(cache[q]["scores"], cands[q]) for q in qids}

    rng = random.Random(0)
    rows = []
    for a, b in itertools.combinations(RERANKERS, 2):
        for label, f, k in METRICS:
            d = [f(qrels[q], per[a][q], k) - f(qrels[q], per[b][q], k) for q in qids]
            mean = sum(d) / len(d)
            boots = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(B))
            p = min(1.0, 2 * min(sum(x <= 0 for x in boots), sum(x >= 0 for x in boots)) / B)
            rows.append({"a": a, "b": b, "metric": label, "diff": mean,
                         "ci95": [boots[int(0.025 * B)], boots[int(0.975 * B)]], "p": p})

    lines = [f"## Paired bootstrap: A − B ({len(qids)} queries, {B:,} resamples, seed 0)", "",
             "| A | B | metric | A − B | 95% CI | p |", "|---|---|---|---:|---|---:|"]
    for r in rows:
        sig = " *" if r["p"] < 0.05 else ""
        lines.append(f"| {r['a']} | {r['b']} | {r['metric']} | {r['diff']:+.4f} | "
                     f"[{r['ci95'][0]:+.4f}, {r['ci95'][1]:+.4f}] | {r['p']:.3f}{sig} |")
    lines += ["", f"\\* p < 0.05 (uncorrected; {len(rows)} comparisons, so treat p ≈ 0.01–0.05 as borderline)."]
    md = "\n".join(lines)
    print(md)
    tag = f"n{len(qids)}"
    (RESULTS / f"significance_{tag}.md").write_text(md + "\n")
    (RESULTS / f"significance_{tag}.json").write_text(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
