## BEIR SciFact test — 10 queries, rerank depth 100

| system | nDCG@10 | nDCG@100 | Recall@1 | Recall@3 | Recall@5 | Recall@10 | Recall@20 | Recall@100 | p50 API latency/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| chroma (no rerank) | 0.5640 | 0.5880 | 0.3000 | 0.6500 | 0.7500 | 0.8000 | 0.9000 | 0.9000 | — |
| jev | 0.5931 | 0.6438 | 0.5000 | 0.6000 | 0.7000 | 0.7000 | 0.8000 | 0.9000 | 0.60s (n=10) |
| cohere | 0.5801 | 0.6309 | 0.5000 | 0.6000 | 0.6000 | 0.7000 | 0.8000 | 0.9000 | — |
| qwen | 0.5649 | 0.6289 | 0.5000 | 0.5000 | 0.6000 | 0.6500 | 0.8000 | 0.9000 | 2.11s (n=10) |
| qwen8b | 0.6172 | 0.6537 | 0.5000 | 0.6000 | 0.6000 | 0.7500 | 0.8000 | 0.9000 | 17.51s (n=10) |

Recall@100 is identical for all systems: rerankers reorder the same Chroma top-100.
Ties in reranker scores are broken by Chroma rank.

### Sanity checks

| reranker | score min | score max | distinct scores / query (median) | top-1 doc relevant |
|---|---:|---:|---:|---:|
| jev | 0.0100 | 0.9800 | 12 | 5/10 |
| cohere | 0.0832 | 0.9726 | 54 | 5/10 |
| qwen | 0.0000 | 0.9999 | 100 | 5/10 |
| qwen8b | 0.0000 | 0.9987 | 100 | 5/10 |
