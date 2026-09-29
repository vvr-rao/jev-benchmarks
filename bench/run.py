"""Rerank the cached Chroma top-N with each reranker and report nDCG / Recall.

  uv run python -m bench.run --limit 10                 # subset run
  uv run python -m bench.run                            # all 300 test queries
  uv run python -m bench.run --rerankers jev@scifact-v1,cohere

Scores are cached per query in results/cache/<reranker>.jsonl, so reruns resume
and never pay twice for the same query.
"""
import argparse
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from tqdm import tqdm

from bench.data import load
from bench.metrics import evaluate
from bench.retrieve import CANDIDATES, candidates

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "results" / "cache"
RESULTS = ROOT / "results"


def get_reranker(name):
    """Names: jev | jev@<prompt-version> | cohere | qwen | qwen8b. The name is also the cache file stem."""
    if name == "jev" or name.startswith("jev@"):
        from bench.rerankers.jev import Jev
        rr = Jev(name.partition("@")[2] or "generic-1")
        rr.name = name
        return rr
    if name == "cohere":
        from bench.rerankers.cohere import Cohere
        return Cohere()
    if name == "qwen":
        from bench.rerankers.qwen import Qwen
        return Qwen()
    if name == "qwen8b":
        from bench.rerankers.qwen import Qwen
        rr = Qwen("8B")
        rr.name = "qwen8b"
        return rr
    raise SystemExit(f"unknown reranker {name!r}")


def load_cache(path: Path) -> dict:
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text().splitlines():
        if line.strip():
            rec = json.loads(line)
            out[rec["qid"]] = rec
    return out


def run_reranker(name, qids, queries, corpus, cands, cache_dir: Path = CACHE):
    path = cache_dir / f"{name}.jsonl"
    cache = load_cache(path)
    todo = [q for q in qids if q not in cache]
    if todo:
        rr = get_reranker(name)
        lock = threading.Lock()

        def one(qid):
            doc_ids = list(cands[qid])
            t = time.perf_counter()
            scores, api_s, retries = rr.score(queries[qid], [corpus[d] for d in doc_ids])
            rec = {
                "qid": qid, "api_latency_s": api_s, "wall_s": time.perf_counter() - t,
                "retries": retries, "scores": dict(zip(doc_ids, scores)),
            }
            with lock, open(path, "a") as f:
                f.write(json.dumps(rec) + "\n")
            return rec

        with ThreadPoolExecutor(rr.concurrency) as ex:
            futs = [ex.submit(one, q) for q in todo]
            for fut in tqdm(as_completed(futs), total=len(futs), desc=name):
                rec = fut.result()
                cache[rec["qid"]] = rec

        usage_path = cache_dir / f"{name}.usage.json"
        usage = json.loads(usage_path.read_text()) if usage_path.exists() else {}
        for k, v in rr.usage.items():
            usage[k] = usage.get(k, 0) + v
        if getattr(rr, "model_version", None):
            usage["model_version"] = rr.model_version
        if getattr(rr, "prompt_version", None):
            usage["prompt_version"] = rr.prompt_version
        usage_path.write_text(json.dumps(usage, indent=2))
        print(f"{name}: this session usage {rr.usage}")
    return {q: cache[q] for q in qids}


def probe_latency(name, qids, queries, corpus, cands, cache_dir: Path = CACHE, n: int = 50) -> dict:
    """Latency measured one request at a time on the first n queries (scores are discarded).

    Scoring runs with several requests in flight for throughput; on this 2-core machine that
    inflates per-call timings, so reported latency comes from this sequential probe instead.
    Cached in <cache_dir>/<name>.latency.json.
    """
    path = cache_dir / f"{name}.latency.json"
    probe_q = qids[:n]
    if path.exists():
        cached = json.loads(path.read_text())
        if cached["qids"] == probe_q:
            return cached["summary"]
    rr = get_reranker(name)
    lats = []
    for q in tqdm(probe_q, desc=f"{name} latency probe"):
        _, api_s, _ = rr.score(queries[q], [corpus[d] for d in cands[q]])
        lats.append(api_s)
    lats.sort()
    summary = {"p50_s": lats[len(lats) // 2], "p95_s": lats[max(0, int(len(lats) * 0.95) - 1)], "n": len(lats)}
    path.write_text(json.dumps({"qids": probe_q, "latencies_s": lats, "summary": summary, "usage": rr.usage}, indent=2))
    return summary


def tie_break_by_first_stage(scores: dict[str, float], first_stage: dict[str, float]) -> dict[str, float]:
    """Turn reranker scores into rank-based scores; ties fall back to the Chroma order.

    Some rerankers return coarse scores (JEV rounds to 2 decimals, so dozens of candidates
    can share a score). Without this, ties are broken by doc id, which is arbitrary.
    """
    fs_rank = {d: i for i, d in enumerate(sorted(first_stage, key=first_stage.get, reverse=True))}
    order = sorted(scores, key=lambda d: (-scores[d], fs_rank[d]))
    return {d: float(len(order) - i) for i, d in enumerate(order)}


def sanity(name, recs, qrels):
    """Score range, and how often the top-ranked doc is relevant."""
    allscores = [s for r in recs.values() for s in r["scores"].values()]
    top1 = sum(max(r["scores"], key=r["scores"].get) in qrels[q] for q, r in recs.items())
    distinct = sorted(len(set(r["scores"].values())) for r in recs.values())
    return {
        "min": min(allscores), "max": max(allscores), "median_distinct_scores": distinct[len(distinct) // 2],
        "top1_relevant": f"{top1}/{len(recs)}",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rerankers", default="jev@scifact-v1,cohere,qwen,qwen8b")
    ap.add_argument("--limit", type=int, default=None, help="first N test queries (subset run)")
    ap.add_argument("--depth", type=int, default=100)
    ap.add_argument("--latency-probe", type=int, default=50, help="sequential latency probe size (0 = skip)")
    args = ap.parse_args()

    corpus, queries, qrels = load()
    cands = candidates(args.depth)
    qids = [q for q in queries if q in cands]
    if args.limit:
        qids = qids[: args.limit]
    print(f"{len(qids)} queries x top-{args.depth} candidates (from {CANDIDATES.name})")

    runs = {"chroma (no rerank)": {q: cands[q] for q in qids}}
    latency, sanity_rows = {}, {}
    for name in [n.strip() for n in args.rerankers.split(",") if n.strip()]:
        recs = run_reranker(name, qids, queries, corpus, cands)
        runs[name] = {q: tie_break_by_first_stage(r["scores"], cands[q]) for q, r in recs.items()}
        if args.latency_probe:
            latency[name] = probe_latency(name, qids, queries, corpus, cands, n=args.latency_probe)
        sanity_rows[name] = sanity(name, recs, qrels)

    table = {name: evaluate(qrels, run) for name, run in runs.items()}
    metrics = list(next(iter(table.values())))
    lines = [
        f"## BEIR SciFact test — {len(qids)} queries, rerank depth {args.depth}",
        "",
        "| system | " + " | ".join(metrics) + " | p50 API latency (sequential) |",
        "|---|" + "---:|" * (len(metrics) + 1),
    ]
    for name, m in table.items():
        lat = f"{latency[name]['p50_s']:.2f}s (n={latency[name]['n']})" if name in latency else "—"
        lines.append(f"| {name} | " + " | ".join(f"{m[k]:.4f}" for k in metrics) + f" | {lat} |")
    lines += ["", "Recall@100 is identical for all systems: rerankers reorder the same Chroma top-100.",
              "Ties in reranker scores are broken by Chroma rank.", ""]
    lines += ["### Sanity checks", "", "| reranker | score min | score max | distinct scores / query (median) | top-1 doc relevant |", "|---|---:|---:|---:|---:|"]
    for name, s in sanity_rows.items():
        lines.append(f"| {name} | {s['min']:.4f} | {s['max']:.4f} | {s['median_distinct_scores']} | {s['top1_relevant']} |")
    md = "\n".join(lines)
    print("\n" + md)

    tag = f"n{len(qids)}"
    (RESULTS / f"summary_{tag}.md").write_text(md + "\n")
    (RESULTS / f"summary_{tag}.json").write_text(
        json.dumps({"n_queries": len(qids), "depth": args.depth, "metrics": table, "latency": latency, "sanity": sanity_rows}, indent=2)
    )
    print(f"\nwrote results/summary_{tag}.md / .json")


if __name__ == "__main__":
    main()
