## HotpotQA distractor (dev) — 10 questions, up to 10 paragraphs each (2 gold)

| system | nDCG@10 | Recall@1 | Recall@2 | Recall@3 | Recall@5 | Both@2 | Both@3 | Both@5 | p50 API latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bm25 (no rerank) | 0.7938 | 0.4000 | 0.5500 | 0.6000 | 0.6500 | 0.3000 | 0.3000 | 0.4000 | — |
| jev@hotpotqa-v1 | 1.0000 | 0.5000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 16.42s |
| qwen | 0.9478 | 0.5000 | 0.8000 | 0.9000 | 0.9000 | 0.6000 | 0.8000 | 0.8000 | 8.76s |
| qwen8b | 0.9797 | 0.5000 | 0.9000 | 0.9500 | 1.0000 | 0.8000 | 0.9000 | 1.0000 | 2.13s |
| cohere | 0.9877 | 0.5000 | 0.9500 | 0.9500 | 1.0000 | 0.9000 | 0.9000 | 1.0000 | 4.03s |

### bridge questions (7)

| system | nDCG@10 | Recall@2 | Both@2 | Both@5 |
|---|---:|---:|---:|---:|
| bm25 (no rerank) | 0.8220 | 0.5714 | 0.2857 | 0.4286 |
| jev@hotpotqa-v1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| qwen | 0.9254 | 0.7143 | 0.4286 | 0.7143 |
| qwen8b | 0.9710 | 0.8571 | 0.7143 | 1.0000 |
| cohere | 0.9825 | 0.9286 | 0.8571 | 1.0000 |

### comparison questions (3)

| system | nDCG@10 | Recall@2 | Both@2 | Both@5 |
|---|---:|---:|---:|---:|
| bm25 (no rerank) | 0.7282 | 0.5000 | 0.3333 | 0.3333 |
| jev@hotpotqa-v1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| qwen | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| qwen8b | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| cohere | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

Both@k: both gold paragraphs in the top k. Ties in reranker scores are broken by BM25 rank.
jev@<version> = JEV with that prompt version (see bench/rerankers/jev.py).
