# JEV-Benchmarks

Compares JEV (TypeSafe `jev-latest`), Cohere Rerank 4 Pro (`rerank-v4.0-pro`), and
Qwen3-Reranker 0.6B / 8B (hosted on DeepInfra) on the BEIR SciFact test split (300 queries)
and the full HotpotQA distractor dev set (7,405 questions).

Current results use dataset-specific JEV prompts (`scifact-v1`, `hotpotqa-v1`); see
[Prompt versions](#prompt-versions).

### BEIR SciFact

**Pipeline:** Chroma (local, built-in ONNX all-MiniLM-L6-v2, cosine) retrieves the top 100
per query → each reranker rescores exactly that list → nDCG@10/100 and Recall@1/3/5/10/20/100.

Results: [`results/summary_n300.md`](results/summary_n300.md),
significance: [`results/significance_n300.md`](results/significance_n300.md).

### HotpotQA distractor

All 7,405 questions of the HotpotQA **dev distractor** set. Each question comes with its own
paragraphs (10 for all but 60 questions): 2 gold supporting paragraphs + distractors. No
first-stage retrieval: each reranker ranks the given paragraphs; BM25 over them is the
baseline and tie-breaker. **Both@k** = both gold paragraphs in the top k (what multi-hop QA
needs). Results are also split into bridge (5,918) and comparison (1,487) questions.

Results: [`results/hotpotqa/summary_n7405.md`](results/hotpotqa/summary_n7405.md),
significance: [`results/hotpotqa/significance_n7405.md`](results/hotpotqa/significance_n7405.md).

JEV scores all of a question's paragraphs within one request (one state, one question per
paragraph), so it can use the other paragraphs as context; Cohere and Qwen score each
(query, paragraph) pair independently. This is how each API is designed to be used, and likely
explains JEV's lead on bridge questions. On comparison questions JEV is slightly but
significantly behind Qwen 8B.

## Setup

```bash
uv sync
cp .env.example .env   # fill in TYPESAFE_API_KEY, COHERE_API_KEY, DEEPINFRA_API_KEY (.env is gitignored)
uv run python -m bench.ping jev@scifact-v1,jev@hotpotqa-v1,cohere,qwen,qwen8b   # validate keys
```

## Run

```bash
# SciFact
uv run python -m bench.retrieve                        # build Chroma index + top-100 candidates (one-time, ~1.5 h here)
uv run python -m bench.run --limit 10                  # subset
uv run python -m bench.run                             # jev@scifact-v1, cohere, qwen, qwen8b
uv run python -m bench.significance

# HotpotQA distractor
uv run python -m bench.hotpot --full --limit 10        # subset
bash scripts/run_hotpot_full.sh                        # all 7,405 questions + significance, 1 GB memory watchdog
uv run python -m bench.hotpot                          # 500-question sample (seed 0) instead of the full set
```

Per-query scores are cached in `results/cache/` (SciFact) and `results/hotpotqa/cache/`
(HotpotQA) as `<reranker>.jsonl` and committed, so tables and significance tests can be
regenerated without calling any API. Reranker names: `jev@<prompt-version>`, `cohere`,
`qwen` (0.6B), `qwen8b`.

## Prompt versions

JEV prompts live in `bench/rerankers/jev.py` (`PROMPTS`):

| version | used for | idea |
|---|---|---|
| `generic-1` | first SciFact run and the HotpotQA 500-question sample | [hev-rerank](https://github.com/hev/jev-rerank)'s domain-neutral prompt |
| `scifact-v1` | SciFact (current) | evidence that supports **or refutes** the claim counts |
| `hotpotqa-v1` | HotpotQA (current) | answer facts, comparison facts and intermediate (bridge) entities count |

Measured effect of the dataset-specific prompts (paired bootstrap, same queries): SciFact
nDCG@10 −0.009 (95% CI −0.023 to +0.004, n.s.); HotpotQA 500-sample nDCG@10 +0.002 (n.s.),
Both@2 +0.000. The tailored prompts made no measurable difference.

Caveats:
- Only JEV gets task instructions. Cohere's rerank API has no instruction field and DeepInfra
  doesn't document one for Qwen, so both receive only the raw query.
- `hotpotqa-v1` was written after seeing results on a 500-question sample of the same dev set
  it is evaluated on.

Earlier results with `generic-1` (SciFact n=300, HotpotQA n=500) are in git history
(commit `a1bb667`); `results/hotpotqa/summary_n500.md` and `significance_n500.md` are kept
from that run.

## Method notes

- Document text for every reranker is `title + "\n" + text`.
- **JEV:** query + up to 30 docs per call, one `noul` question per doc. Scores come back rounded
  to 2 decimals (~12–20 distinct values per query).
- **Ties** in any reranker's scores are broken by the first stage (Chroma rank for SciFact, BM25
  for HotpotQA), not doc id. Worst case (every tie broken against gold) moves JEV's HotpotQA
  Both@2 from 0.871 to 0.867.
- **Latency** is measured by a separate probe: the first 50 queries, one request at a time,
  API time of the successful call only (no client pacing, no 429 backoff). Scoring itself runs
  4 requests in parallel, which on this 2-core machine inflates per-call timings. JEV on
  SciFact = wall time of 4 concurrent 30-doc calls. Qwen latency reflects DeepInfra load.
- **Cohere** defaults assume a production key (no pacing, 4 in flight). For a trial key
  (~10 calls/min) set `COHERE_MIN_INTERVAL_S=6.5` and `COHERE_CONCURRENCY=1` in `.env`.
- **Memory:** this VM has 2.7 GB RAM and no swap. The HotpotQA loader streams the parquet
  file and BM25 keeps one global document-frequency table (peak ~400 MB for the full set;
  the naive version needed >1.8 GB and crashed the VM).
- Recall@100 on SciFact is identical for all rerankers (0.9217): it is capped by the Chroma
  candidates.
