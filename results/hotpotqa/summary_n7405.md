## HotpotQA distractor (dev) — 7405 questions, up to 10 paragraphs each (2 gold)

| system | nDCG@10 | Recall@1 | Recall@2 | Recall@3 | Recall@5 | Both@2 | Both@3 | Both@5 | p50 API latency (sequential) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bm25 (no rerank) | 0.8026 | 0.3939 | 0.5546 | 0.6272 | 0.7142 | 0.2315 | 0.3396 | 0.4718 | — |
| jev@hotpotqa-v1 | 0.9786 | 0.4850 | 0.9318 | 0.9737 | 0.9912 | 0.8713 | 0.9498 | 0.9831 | 0.31s |
| qwen | 0.9270 | 0.4695 | 0.7816 | 0.8590 | 0.9200 | 0.5838 | 0.7271 | 0.8428 | 0.31s |
| qwen8b | 0.9565 | 0.4777 | 0.8605 | 0.9275 | 0.9681 | 0.7330 | 0.8597 | 0.9380 | 0.61s |
| cohere | 0.9594 | 0.4800 | 0.8654 | 0.9320 | 0.9733 | 0.7406 | 0.8686 | 0.9484 | 0.31s |

### bridge questions (5918)

| system | nDCG@10 | Recall@2 | Both@2 | Both@5 |
|---|---:|---:|---:|---:|
| bm25 (no rerank) | 0.8025 | 0.5529 | 0.2203 | 0.4363 |
| jev@hotpotqa-v1 | 0.9792 | 0.9340 | 0.8766 | 0.9860 |
| qwen | 0.9128 | 0.7417 | 0.5091 | 0.8058 |
| qwen8b | 0.9491 | 0.8403 | 0.6955 | 0.9245 |
| cohere | 0.9530 | 0.8478 | 0.7077 | 0.9378 |

### comparison questions (1487)

| system | nDCG@10 | Recall@2 | Both@2 | Both@5 |
|---|---:|---:|---:|---:|
| bm25 (no rerank) | 0.8030 | 0.5615 | 0.2757 | 0.6133 |
| jev@hotpotqa-v1 | 0.9766 | 0.9230 | 0.8500 | 0.9718 |
| qwen | 0.9837 | 0.9401 | 0.8810 | 0.9899 |
| qwen8b | 0.9859 | 0.9408 | 0.8823 | 0.9919 |
| cohere | 0.9847 | 0.9351 | 0.8716 | 0.9906 |

Both@k: both gold paragraphs in the top k. Ties in reranker scores are broken by BM25 rank.
jev@<version> = JEV with that prompt version (see bench/rerankers/jev.py).
Latency: one request at a time on the first 50 questions (scoring itself ran 4 requests in parallel).
