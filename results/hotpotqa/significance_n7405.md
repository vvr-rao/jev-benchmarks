## Paired bootstrap: A − B (7405 queries, 10,000 resamples, seed 0)

| A | B | metric | A − B | 95% CI | p |
|---|---|---|---:|---|---:|
| jev@hotpotqa-v1 | cohere | nDCG@10 | +0.0193 | [+0.0175, +0.0211] | 0.000 * |
| jev@hotpotqa-v1 | cohere | Recall@2 | +0.0664 | [+0.0612, +0.0716] | 0.000 * |
| jev@hotpotqa-v1 | cohere | Both@2 | +0.1307 | [+0.1203, +0.1407] | 0.000 * |
| jev@hotpotqa-v1 | qwen8b | nDCG@10 | +0.0221 | [+0.0201, +0.0241] | 0.000 * |
| jev@hotpotqa-v1 | qwen8b | Recall@2 | +0.0713 | [+0.0658, +0.0768] | 0.000 * |
| jev@hotpotqa-v1 | qwen8b | Both@2 | +0.1383 | [+0.1278, +0.1487] | 0.000 * |
| jev@hotpotqa-v1 | qwen | nDCG@10 | +0.0516 | [+0.0491, +0.0543] | 0.000 * |
| jev@hotpotqa-v1 | qwen | Recall@2 | +0.1502 | [+0.1437, +0.1570] | 0.000 * |
| jev@hotpotqa-v1 | qwen | Both@2 | +0.2875 | [+0.2751, +0.2999] | 0.000 * |
| cohere | qwen8b | nDCG@10 | +0.0028 | [+0.0013, +0.0043] | 0.000 * |
| cohere | qwen8b | Recall@2 | +0.0049 | [+0.0005, +0.0094] | 0.029 * |
| cohere | qwen8b | Both@2 | +0.0076 | [-0.0008, +0.0159] | 0.085 |
| cohere | qwen | nDCG@10 | +0.0324 | [+0.0302, +0.0345] | 0.000 * |
| cohere | qwen | Recall@2 | +0.0838 | [+0.0783, +0.0895] | 0.000 * |
| cohere | qwen | Both@2 | +0.1568 | [+0.1461, +0.1680] | 0.000 * |
| qwen8b | qwen | nDCG@10 | +0.0295 | [+0.0275, +0.0315] | 0.000 * |
| qwen8b | qwen | Recall@2 | +0.0789 | [+0.0734, +0.0845] | 0.000 * |
| qwen8b | qwen | Both@2 | +0.1492 | [+0.1386, +0.1599] | 0.000 * |

\* p < 0.05 (uncorrected; 18 comparisons, so treat p ≈ 0.01–0.05 as borderline).
