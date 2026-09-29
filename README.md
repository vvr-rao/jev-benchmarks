# Reranker benchmark: BEIR SciFact

Compares JEV (TypeSafe `jev-latest`), Cohere Rerank 4 Pro (`rerank-v4.0-pro`), and
Qwen3-Reranker 0.6B / 8B (hosted on DeepInfra) on the BEIR SciFact test split (300 queries).

**Pipeline:** Chroma (local, built-in ONNX all-MiniLM-L6-v2, cosine) retrieves the top 100
per query → each reranker rescores exactly that list → nDCG@10/100 and Recall@1/3/5/10/20/100.

Results: [`results/summary_n300.md`](results/summary_n300.md),
significance: [`results/significance_n300.md`](results/significance_n300.md).

## Setup

```bash
uv sync
cp .env.example .env   # fill in TYPESAFE_API_KEY, COHERE_API_KEY, DEEPINFRA_API_KEY (.env is gitignored)
uv run python -m bench.ping          # one tiny request per API to validate keys
```

## Run

```bash
uv run python -m bench.retrieve                        # build Chroma index + top-100 candidates (one-time)
uv run python -m bench.run --limit 10                  # subset
uv run python -m bench.run --rerankers jev,cohere,qwen,qwen8b
uv run python -m bench.significance                    # paired bootstrap between rerankers
```

Per-query scores are cached in `results/cache/<reranker>.jsonl` and committed, so the
tables and significance tests can be regenerated without calling any API.

## Method notes

- Document text for every reranker is `title + "\n" + abstract`.
- **JEV:** query + up to 30 docs per call, one `noul` question per doc, following
  [hev-rerank](https://github.com/hev/jev-rerank) and using its `generic-1` prompt. Scores come back rounded to
  2 decimals (~12 distinct values per query).
- **Ties** in any reranker's scores are broken by Chroma rank (not doc id).
- **Latency** is API time of the successful call only (excludes client pacing and 429 backoff).
  JEV = wall time of 4 concurrent 30-doc calls. Qwen latency reflects DeepInfra load
  (8B measured 17.5s p50 on the subset, 5.5s on the full run).
- **Cohere** trial keys allow ~10 calls/min; the client paces at one call per 6.5s
  (`COHERE_MIN_INTERVAL_S=0` in `.env` for production keys). Early Cohere timings included
  backoff and were discarded, so its latency has only n=3 samples. `cohere.usage.json`
  undercounts (the first run crashed before saving usage); the true total is ~600 search units.
- Recall@100 is identical for all rerankers (0.9217): it is capped by the Chroma candidates.
