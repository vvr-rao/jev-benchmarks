## HotpotQA distractor (dev) — 10 questions, 10 paragraphs each (2 gold)

| system | nDCG@10 | Recall@1 | Recall@2 | Recall@3 | Recall@5 | Both@2 | Both@3 | Both@5 | p50 API latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bm25 (no rerank) | 0.8055 | 0.4000 | 0.5500 | 0.6500 | 0.7000 | 0.2000 | 0.3000 | 0.4000 | — |
| jev | 0.9920 | 0.5000 | 0.9500 | 1.0000 | 1.0000 | 0.9000 | 1.0000 | 1.0000 | 0.30s |
| qwen | 0.9258 | 0.5000 | 0.7000 | 0.8500 | 0.9000 | 0.4000 | 0.7000 | 0.8000 | 0.30s |
| qwen8b | 0.9636 | 0.5000 | 0.8000 | 0.9500 | 1.0000 | 0.6000 | 0.9000 | 1.0000 | 0.61s |

### bridge questions (8)

| system | nDCG@10 | Recall@2 | Both@2 | Both@5 |
|---|---:|---:|---:|---:|
| bm25 (no rerank) | 0.8162 | 0.5625 | 0.2500 | 0.3750 |
| jev | 0.9900 | 0.9375 | 0.8750 | 1.0000 |
| qwen | 0.9073 | 0.6250 | 0.2500 | 0.7500 |
| qwen8b | 0.9545 | 0.7500 | 0.5000 | 1.0000 |

### comparison questions (2)

| system | nDCG@10 | Recall@2 | Both@2 | Both@5 |
|---|---:|---:|---:|---:|
| bm25 (no rerank) | 0.7625 | 0.5000 | 0.0000 | 0.5000 |
| jev | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| qwen | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| qwen8b | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

Both@k: both gold paragraphs in the top k. Ties in reranker scores are broken by BM25 rank.
