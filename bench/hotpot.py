"""HotpotQA distractor setting: rerank each question's 10 given paragraphs (2 gold + 8 distractors).

  uv run python -m bench.hotpot --limit 10
  uv run python -m bench.hotpot                      # 500-question sample

No first-stage retrieval: the 10 candidates come with the dataset. BM25 over those 10 is the
baseline and breaks ties in reranker scores. Sample: 500 questions with exactly 10 paragraphs,
drawn with a fixed seed from the 7,405-question dev set. Cached in results/hotpotqa/cache/.
"""
import argparse
import json
import math
import random
import re
from collections import Counter
from pathlib import Path

import httpx

from bench.metrics import ndcg_at_k, recall_at_k
from bench.run import ROOT, run_reranker, tie_break_by_first_stage

URL = "https://huggingface.co/datasets/hotpotqa/hotpot_qa/resolve/refs%2Fconvert%2Fparquet/distractor/validation/0000.parquet"
PARQUET = ROOT / "data" / "hotpotqa_distractor_validation.parquet"
OUT = ROOT / "results" / "hotpotqa"
CACHE = OUT / "cache"
SAMPLE, SEED = 500, 0


def load_sample(n=SAMPLE, seed=SEED):
    """Returns (queries, corpus, qrels, qtype) for a fixed random sample of the dev set.

    Doc ids are "<qid>::<paragraph index>" (titles repeat across questions).
    """
    import pyarrow.parquet as pq

    if not PARQUET.exists():
        PARQUET.parent.mkdir(parents=True, exist_ok=True)
        with httpx.stream("GET", URL, follow_redirects=True, timeout=300) as r, open(PARQUET, "wb") as f:
            r.raise_for_status()
            for chunk in r.iter_bytes():
                f.write(chunk)
    rows = pq.read_table(PARQUET).to_pylist()
    rows = [r for r in rows if len(r["context"]["title"]) == 10]
    rows = random.Random(seed).sample(rows, n)

    queries, corpus, qrels, qtype = {}, {}, {}, {}
    for r in rows:
        qid = r["id"]
        queries[qid] = r["question"]
        qtype[qid] = r["type"]
        gold = set(r["supporting_facts"]["title"])
        qrels[qid] = {}
        for i, (title, sents) in enumerate(zip(r["context"]["title"], r["context"]["sentences"])):
            did = f"{qid}::{i}"
            corpus[did] = f"{title}\n{''.join(sents).strip()}"
            if title in gold:
                qrels[qid][did] = 1
    return queries, corpus, qrels, qtype


_tok = re.compile(r"\w+").findall


def bm25(queries, corpus, k1=0.9, b=0.4):
    """BM25 within each question's 10 paragraphs; idf over the whole sampled pool."""
    docs = {d: Counter(t.lower() for t in _tok(text)) for d, text in corpus.items()}
    n = len(docs)
    avgdl = sum(sum(c.values()) for c in docs.values()) / n
    df = Counter(t for c in docs.values() for t in c)
    run = {}
    for qid, q in queries.items():
        terms = [t.lower() for t in _tok(q)]
        run[qid] = {}
        for i in range(10):
            d = f"{qid}::{i}"
            c, dl = docs[d], sum(docs[d].values())
            run[qid][d] = sum(
                math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5)) * c[t] * (k1 + 1) / (c[t] + k1 * (1 - b + b * dl / avgdl))
                for t in terms if t in c
            )
    return run


def both_at_k(rels, scores, k):
    top = sorted(scores, key=scores.get, reverse=True)[:k]
    return float(all(d in top for d in rels))


METRICS = {
    "nDCG@10": lambda r, s: ndcg_at_k(r, s, 10),
    "Recall@1": lambda r, s: recall_at_k(r, s, 1),
    "Recall@2": lambda r, s: recall_at_k(r, s, 2),
    "Recall@3": lambda r, s: recall_at_k(r, s, 3),
    "Recall@5": lambda r, s: recall_at_k(r, s, 5),
    "Both@2": lambda r, s: both_at_k(r, s, 2),
    "Both@3": lambda r, s: both_at_k(r, s, 3),
    "Both@5": lambda r, s: both_at_k(r, s, 5),
}


def evaluate(qrels, run, qids):
    return {m: sum(f(qrels[q], run[q]) for q in qids) / len(qids) for m, f in METRICS.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rerankers", default="jev,qwen,qwen8b,cohere")
    ap.add_argument("--limit", type=int, default=None, help="first N of the 500-question sample")
    args = ap.parse_args()

    queries, corpus, qrels, qtype = load_sample()
    qids = list(queries)[: args.limit] if args.limit else list(queries)
    CACHE.mkdir(parents=True, exist_ok=True)
    base = bm25(queries, corpus)
    cands = {q: base[q] for q in qids}
    print(f"HotpotQA distractor: {len(qids)} questions x 10 paragraphs "
          f"({sum(qtype[q] == 'bridge' for q in qids)} bridge, {sum(qtype[q] == 'comparison' for q in qids)} comparison)")

    runs = {"bm25 (no rerank)": cands}
    latency = {}
    for name in [n.strip() for n in args.rerankers.split(",") if n.strip()]:
        recs = run_reranker(name, qids, queries, corpus, cands, cache_dir=CACHE)
        runs[name] = {q: tie_break_by_first_stage(r["scores"], cands[q]) for q, r in recs.items()}
        lats = sorted(r["api_latency_s"] for r in recs.values() if "api_latency_s" in r)
        latency[name] = lats[len(lats) // 2]

    table = {n: evaluate(qrels, run, qids) for n, run in runs.items()}
    by_type = {t: {n: evaluate(qrels, run, [q for q in qids if qtype[q] == t]) for n, run in runs.items()}
               for t in ("bridge", "comparison")}
    metrics = list(METRICS)
    lines = [f"## HotpotQA distractor (dev) — {len(qids)} questions, 10 paragraphs each (2 gold)", "",
             "| system | " + " | ".join(metrics) + " | p50 API latency |", "|---|" + "---:|" * (len(metrics) + 1)]
    for n, m in table.items():
        lat = f"{latency[n]:.2f}s" if n in latency else "—"
        lines.append(f"| {n} | " + " | ".join(f"{m[k]:.4f}" for k in metrics) + f" | {lat} |")
    for t, tab in by_type.items():
        nq = sum(qtype[q] == t for q in qids)
        lines += ["", f"### {t} questions ({nq})", "", "| system | nDCG@10 | Recall@2 | Both@2 | Both@5 |", "|---|---:|---:|---:|---:|"]
        for n, m in tab.items():
            lines.append(f"| {n} | {m['nDCG@10']:.4f} | {m['Recall@2']:.4f} | {m['Both@2']:.4f} | {m['Both@5']:.4f} |")
    lines += ["", "Both@k: both gold paragraphs in the top k. Ties in reranker scores are broken by BM25 rank."]
    md = "\n".join(lines)
    print("\n" + md)
    tag = f"n{len(qids)}"
    (OUT / f"summary_{tag}.md").write_text(md + "\n")
    (OUT / f"summary_{tag}.json").write_text(json.dumps({"n_questions": len(qids), "overall": table, "by_type": by_type, "p50_latency_s": latency}, indent=2))
    print(f"\nwrote results/hotpotqa/summary_{tag}.md / .json")


if __name__ == "__main__":
    main()
