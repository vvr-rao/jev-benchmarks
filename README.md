# JEV-Benchmarks

Compares JEV (TypeSafe `jev-latest`), Cohere Rerank 4 Pro (`rerank-v4.0-pro`), and
Qwen3-Reranker 0.6B / 8B (hosted on DeepInfra) on the BEIR SciFact test split (300 queries)
and the full HotpotQA distractor dev set (7,405 questions).

Current results use dataset-specific JEV prompts (`scifact-v1`, `hotpotqa-v1`); see
[Prompt versions](#prompt-versions).

## Results

### BEIR SciFact (300 queries)

Chroma (local, built-in ONNX all-MiniLM-L6-v2, cosine) retrieves the top 100 per query; each
reranker rescores exactly that list.

| system | nDCG@10 | Recall@1 | Recall@5 | Recall@10 | p50 latency |
|---|---:|---:|---:|---:|---:|
| Chroma (no rerank) | 0.6417 | 0.479 | 0.735 | 0.780 | — |
| JEV (`scifact-v1`) | 0.7838 | **0.657** | 0.838 | 0.881 | **0.63s** |
| Cohere Rerank 4 Pro | **0.7868** | 0.651 | **0.863** | **0.893** | 1.29s |
| Qwen3-Reranker-8B | 0.7799 | 0.650 | 0.830 | 0.877 | 4.41s |
| Qwen3-Reranker-0.6B | 0.7507 | 0.613 | 0.807 | 0.862 | 1.84s |

JEV, Cohere and Qwen 8B are statistically tied on nDCG@10 (paired bootstrap, p ≈ 0.75–0.77);
all three are significantly ahead of Qwen 0.6B. Recall@100 is 0.9217 for every system (capped
by the Chroma candidates).

### HotpotQA distractor — all 7,405 dev questions

Each question comes with its own paragraphs (10 for all but 60 questions): 2 gold supporting
paragraphs + distractors. No first-stage retrieval: each reranker ranks the given paragraphs;
BM25 over them is the baseline. **Both@k** = both gold paragraphs in the top k, which is what
multi-hop QA needs. (Recall@1 is capped at 0.5 with 2 gold paragraphs, so it is not shown.)

| system | nDCG@10 | Recall@2 | **Both@2** | Both@3 | Both@5 | p50 latency | cost (full run) |
|---|---:|---:|---:|---:|---:|---:|---:|
| BM25 (no rerank) | 0.803 | 0.555 | 0.232 | 0.340 | 0.472 | — | — |
| **JEV (`hotpotqa-v1`)** | **0.979** | **0.932** | **0.871** | **0.950** | **0.983** | 0.31s | ~$0.93 |
| Cohere Rerank 4 Pro | 0.959 | 0.865 | 0.741 | 0.869 | 0.948 | 0.31s | ~$18.50 |
| Qwen3-Reranker-8B | 0.957 | 0.861 | 0.733 | 0.860 | 0.938 | 0.61s | $0.85 |
| Qwen3-Reranker-0.6B | 0.927 | 0.782 | 0.584 | 0.727 | 0.843 | 0.31s | $0.17 |

JEV's lead over every other reranker is significant on nDCG@10, Recall@2 and Both@2
(p < 0.001; Both@2 +13.1 points over Cohere, 95% CI +12.0 to +14.1).

#### Bridge questions (5,918)

The answer needs a chain: the first paragraph names an entity, the second is about that entity
(e.g. *"The director of film X was born in which city?"*). The second paragraph often shares
few words with the question.

| system | nDCG@10 | Recall@2 | Recall@3 | Recall@5 | **Both@2** | Both@3 | Both@5 |
|---|---:|---:|---:|---:|---:|---:|---:|
| BM25 (no rerank) | 0.803 | 0.553 | 0.618 | 0.697 | 0.220 | 0.317 | 0.436 |
| **JEV** | **0.979** | **0.934** | **0.977** | **0.993** | **0.877** | **0.957** | **0.986** |
| Cohere Rerank 4 Pro | 0.953 | 0.848 | 0.920 | 0.968 | 0.708 | 0.847 | 0.938 |
| Qwen3-Reranker-8B | 0.949 | 0.840 | 0.913 | 0.961 | 0.696 | 0.833 | 0.925 |
| Qwen3-Reranker-0.6B | 0.913 | 0.742 | 0.828 | 0.901 | 0.509 | 0.668 | 0.806 |

#### Comparison questions (1,487)

Two entities named in the question are compared (e.g. *"Were Scott Derrickson and Ed Wood of
the same nationality?"*), so both gold paragraphs are about entities the question names.

| system | nDCG@10 | Recall@2 | Recall@3 | Recall@5 | **Both@2** | Both@3 | Both@5 |
|---|---:|---:|---:|---:|---:|---:|---:|
| BM25 (no rerank) | 0.803 | 0.562 | 0.663 | 0.785 | 0.276 | 0.428 | 0.613 |
| JEV | 0.977 | 0.923 | 0.959 | 0.985 | 0.850 | 0.919 | 0.972 |
| Cohere Rerank 4 Pro | 0.985 | 0.935 | 0.978 | 0.995 | 0.872 | 0.956 | 0.991 |
| **Qwen3-Reranker-8B** | **0.986** | **0.941** | **0.984** | **0.996** | **0.882** | **0.968** | **0.992** |
| Qwen3-Reranker-0.6B | 0.984 | 0.940 | 0.981 | 0.995 | 0.881 | 0.962 | 0.990 |

On comparison questions JEV is significantly behind Qwen 8B (Both@2 −3.2 points, p < 0.001)
and borderline behind Cohere (−2.2 points, p ≈ 0.03). JEV's overall lead comes entirely from
bridge questions, which are 80% of the dev set.

JEV scores all of a question's paragraphs within one request (one state, one question per
paragraph), so it can use the other paragraphs as context; Cohere and Qwen score each
(query, paragraph) pair independently. This is how each API is designed to be used, and likely
explains JEV's lead on bridge questions.

Full tables and significance tests: [`results/summary_n300.md`](results/summary_n300.md),
[`results/significance_n300.md`](results/significance_n300.md),
[`results/hotpotqa/summary_n7405.md`](results/hotpotqa/summary_n7405.md),
[`results/hotpotqa/significance_n7405.md`](results/hotpotqa/significance_n7405.md).

## Setup

```bash
uv sync
cp .env.example .env   # fill in TYPESAFE_API_KEY, COHERE_API_KEY, DEEPINFRA_API_KEY (.env is gitignored)
uv run python -m bench.ping jev@scifact-v1,jev@hotpotqa-v1,cohere,qwen,qwen8b   # validate keys
```

## Run

```bash
# SciFact
uv run python -m bench.retrieve                        # build Chroma index + top-100 candidates (one-time)
uv run python -m bench.run --limit 10                  # subset
uv run python -m bench.run                             # jev@scifact-v1, cohere, qwen, qwen8b
uv run python -m bench.significance

# HotpotQA distractor
uv run python -m bench.hotpot --full --limit 10        # subset
bash scripts/run_hotpot_full.sh                        # all 7,405 questions + significance
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
(commit `b5c0602`); `results/hotpotqa/summary_n500.md` and `significance_n500.md` are kept
from that run.

## Method notes

- Document text for every reranker is `title + "\n" + text`.
- **JEV:** query + up to 30 docs per call, one `noul` question per doc. Scores come back rounded
  to 2 decimals (~12–20 distinct values per query).
- **Ties** in any reranker's scores are broken by the first stage (Chroma rank for SciFact, BM25
  for HotpotQA), not doc id. Worst case (every tie broken against gold) moves JEV's HotpotQA
  Both@2 from 0.871 to 0.867.
- **Costs** are list prices: JEV $42 per 1B input tokens, Cohere Rerank 4 Pro $2.50 per 1K
  searches (third-party listing), Qwen on DeepInfra $0.01 (0.6B) / $0.05 (8B) per 1M tokens.
- **Cohere** defaults assume a production key. For a trial key (~10 calls/min) set
  `COHERE_MIN_INTERVAL_S=6.5` and `COHERE_CONCURRENCY=1` in `.env`.
