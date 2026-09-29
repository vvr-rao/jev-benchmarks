"""HotpotQA distractor setting: rerank each question's 10 given paragraphs (2 gold + 8 distractors).

  uv run python -m bench.hotpot --full --limit 10    # subset
  uv run python -m bench.hotpot --full               # all 7,405 dev questions
  uv run python -m bench.hotpot                      # 500-question sample (10-paragraph questions)

No first-stage retrieval: the candidates (10 for all but 60 questions) come with the dataset.
BM25 over them is the baseline and breaks ties in reranker scores. The 500-question sample is
drawn with a fixed seed from the 10-paragraph questions. Cached in results/hotpotqa/cache/.
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
from bench.run import ROOT, probe_latency, run_reranker, tie_break_by_first_stage

URL = "https://huggingface.co/datasets/hotpotqa/hotpot_qa/resolve/refs%2Fconvert%2Fparquet/distractor/validation/0000.parquet"
PARQUET = ROOT / "data" / "hotpotqa_distractor_validation.parquet"
OUT = ROOT / "results" / "hotpotqa"
CACHE = OUT / "cache"
SAMPLE, SEED = 500, 0


def load_sample(n=SAMPLE, seed=SEED):
    """Returns (queries, corpus, qrels, qtype) for a fixed random sample of the dev set,
    or for the whole dev set (all 7,405 questions, in file order) when n is None.

    Doc ids are "<qid>::<paragraph index>" (titles repeat across questions).
    """
    import pyarrow.parquet as pq

    if not PARQUET.exists():
        PARQUET.parent.mkdir(parents=True, exist_ok=True)
        with httpx.stream("GET", URL, follow_redirects=True, timeout=300) as r, open(PARQUET, "wb") as f:
            r.raise_for_status()
            for chunk in r.iter_bytes():
                f.write(chunk)
    # Stream the file in small batches: materialising all 7,405 rows as Python objects at once
    # needs >1.8 GB and took down this 2.7 GB machine.
    pf = pq.ParquetFile(PARQUET)
    cols = ["id", "question", "type", "supporting_facts", "context"]

    def batches():
        for batch in pf.iter_batches(batch_size=256, columns=cols):
            yield from batch.to_pylist()

    if n is None:
        keep = None
    else:
        # same selection as random.sample over the list of 10-paragraph rows
        n_par = []
        for batch in pf.iter_batches(batch_size=1024, columns=["context"]):
            n_par.extend(len(c["title"]) for c in batch.column("context").to_pylist())
        eligible = [i for i, k in enumerate(n_par) if k == 10]
        keep = {i: pos for pos, i in enumerate(random.Random(seed).sample(eligible, n))}

    picked = []
    for i, r in enumerate(batches()):
        if keep is None or i in keep:
            ctx = r["context"]
            paras = [(t, f"{t}\n{''.join(sents).strip()}") for t, sents in zip(ctx["title"], ctx["sentences"])]
            picked.append((keep[i] if keep else i, r["id"], r["question"], r["type"],
                           set(r["supporting_facts"]["title"]), paras))
    picked.sort(key=lambda x: x[0])

    queries, corpus, qrels, qtype = {}, {}, {}, {}
    for _, qid, question, typ, gold, paras in picked:
        queries[qid] = question
        qtype[qid] = typ
        qrels[qid] = {}
        for i, (title, text) in enumerate(paras):
            did = f"{qid}::{i}"
            corpus[did] = text
            if title in gold:
                qrels[qid][did] = 1
    return queries, corpus, qrels, qtype


_tok = re.compile(r"\w+").findall


def bm25(queries, corpus, k1=0.9, b=0.4):
    """BM25 within each question's own paragraphs; idf over the whole pool of paragraphs.

    Two passes and one global document-frequency table, instead of a Counter per paragraph
    (74k Counters for the full dev set is too much for this machine).
    """
    df, total_len, by_q = Counter(), 0, {}
    for d, text in corpus.items():
        toks = [t.lower() for t in _tok(text)]
        total_len += len(toks)
        df.update(set(toks))
        by_q.setdefault(d.rpartition("::")[0], []).append(d)
    n = len(corpus)
    avgdl = total_len / n
    run = {}
    for qid, q in queries.items():
        terms = [t.lower() for t in _tok(q)]
        run[qid] = {}
        for d in by_q[qid]:
            toks = [t.lower() for t in _tok(corpus[d])]
            c, dl = Counter(toks), len(toks)
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
    ap.add_argument("--rerankers", default="jev@hotpotqa-v1,qwen,qwen8b,cohere")
    ap.add_argument("--full", action="store_true", help="all 7,405 dev questions instead of the 500 sample")
    ap.add_argument("--limit", type=int, default=None, help="first N questions only (subset run)")
    ap.add_argument("--latency-probe", type=int, default=50, help="sequential latency probe size (0 = skip)")
    args = ap.parse_args()

    queries, corpus, qrels, qtype = load_sample(None if args.full else SAMPLE)
    qids = list(queries)[: args.limit] if args.limit else list(queries)
    CACHE.mkdir(parents=True, exist_ok=True)
    base = bm25(queries, corpus)
    cands = {q: base[q] for q in qids}
    print(f"HotpotQA distractor: {len(qids)} questions, {sum(len(cands[q]) for q in qids)} paragraphs "
          f"({sum(qtype[q] == 'bridge' for q in qids)} bridge, {sum(qtype[q] == 'comparison' for q in qids)} comparison)")

    runs = {"bm25 (no rerank)": cands}
    latency = {}
    for name in [n.strip() for n in args.rerankers.split(",") if n.strip()]:
        recs = run_reranker(name, qids, queries, corpus, cands, cache_dir=CACHE)
        runs[name] = {q: tie_break_by_first_stage(r["scores"], cands[q]) for q, r in recs.items()}
        if args.latency_probe:
            latency[name] = probe_latency(name, qids, queries, corpus, cands, cache_dir=CACHE, n=args.latency_probe)["p50_s"]

    table = {n: evaluate(qrels, run, qids) for n, run in runs.items()}
    by_type = {t: {n: evaluate(qrels, run, [q for q in qids if qtype[q] == t]) for n, run in runs.items()}
               for t in ("bridge", "comparison")}
    metrics = list(METRICS)
    lines = [f"## HotpotQA distractor (dev) — {len(qids)} questions, up to 10 paragraphs each (2 gold)", "",
             "| system | " + " | ".join(metrics) + " | p50 API latency (sequential) |", "|---|" + "---:|" * (len(metrics) + 1)]
    for n, m in table.items():
        lat = f"{latency[n]:.2f}s" if n in latency else "—"
        lines.append(f"| {n} | " + " | ".join(f"{m[k]:.4f}" for k in metrics) + f" | {lat} |")
    for t, tab in by_type.items():
        nq = sum(qtype[q] == t for q in qids)
        lines += ["", f"### {t} questions ({nq})", "", "| system | nDCG@10 | Recall@2 | Both@2 | Both@5 |", "|---|---:|---:|---:|---:|"]
        for n, m in tab.items():
            lines.append(f"| {n} | {m['nDCG@10']:.4f} | {m['Recall@2']:.4f} | {m['Both@2']:.4f} | {m['Both@5']:.4f} |")
    lines += ["", "Both@k: both gold paragraphs in the top k. Ties in reranker scores are broken by BM25 rank.",
              "jev@<version> = JEV with that prompt version (see bench/rerankers/jev.py).",
              "Latency: one request at a time on the first 50 questions (scoring itself ran 4 requests in parallel)."]
    md = "\n".join(lines)
    print("\n" + md)
    tag = f"n{len(qids)}"
    (OUT / f"summary_{tag}.md").write_text(md + "\n")
    (OUT / f"summary_{tag}.json").write_text(json.dumps({"n_questions": len(qids), "overall": table, "by_type": by_type, "p50_latency_s": latency}, indent=2))
    print(f"\nwrote results/hotpotqa/summary_{tag}.md / .json")


if __name__ == "__main__":
    main()
