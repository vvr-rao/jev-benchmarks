## BEIR SciFact test — 300 queries, rerank depth 100

| system | nDCG@10 | nDCG@100 | Recall@1 | Recall@3 | Recall@5 | Recall@10 | Recall@20 | Recall@100 | p50 API latency/query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| chroma (no rerank) | 0.6417 | 0.6734 | 0.4790 | 0.6570 | 0.7346 | 0.7800 | 0.8340 | 0.9217 | — |
| jev | 0.7927 | 0.8006 | 0.6726 | 0.7952 | 0.8318 | 0.8892 | 0.9050 | 0.9217 | 0.42s (n=300) |
| cohere | 0.7857 | 0.7934 | 0.6508 | 0.8093 | 0.8629 | 0.8899 | 0.9050 | 0.9217 | 1.13s (n=3) |
| qwen | 0.7509 | 0.7652 | 0.6126 | 0.7499 | 0.8065 | 0.8620 | 0.9000 | 0.9217 | 1.84s (n=300) |
| qwen8b | 0.7797 | 0.7905 | 0.6499 | 0.7965 | 0.8298 | 0.8766 | 0.9022 | 0.9217 | 5.53s (n=300) |

Recall@100 is identical for all systems: rerankers reorder the same Chroma top-100.
Ties in reranker scores are broken by Chroma rank.

### Sanity checks

| reranker | score min | score max | distinct scores / query (median) | top-1 doc relevant |
|---|---:|---:|---:|---:|
| jev | 0.0100 | 0.9900 | 12 | 211/300 |
| cohere | 0.0423 | 0.9902 | 54 | 204/300 |
| qwen | 0.0000 | 0.9999 | 100 | 193/300 |
| qwen8b | 0.0000 | 0.9999 | 100 | 205/300 |
