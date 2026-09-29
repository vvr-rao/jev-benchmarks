## Paired bootstrap: A − B (300 queries, 10,000 resamples, seed 0)

| A | B | metric | A − B | 95% CI | p |
|---|---|---|---:|---|---:|
| jev@scifact-v1 | cohere | nDCG@10 | -0.0030 | [-0.0226, +0.0170] | 0.769 |
| jev@scifact-v1 | cohere | Recall@1 | +0.0058 | [-0.0308, +0.0425] | 0.772 |
| jev@scifact-v1 | cohere | Recall@5 | -0.0251 | [-0.0562, +0.0064] | 0.115 |
| jev@scifact-v1 | qwen8b | nDCG@10 | +0.0039 | [-0.0183, +0.0266] | 0.747 |
| jev@scifact-v1 | qwen8b | Recall@1 | +0.0067 | [-0.0317, +0.0467] | 0.762 |
| jev@scifact-v1 | qwen8b | Recall@5 | +0.0080 | [-0.0246, +0.0406] | 0.632 |
| jev@scifact-v1 | qwen | nDCG@10 | +0.0331 | [+0.0080, +0.0585] | 0.009 * |
| jev@scifact-v1 | qwen | Recall@1 | +0.0440 | [+0.0007, +0.0890] | 0.049 * |
| jev@scifact-v1 | qwen | Recall@5 | +0.0313 | [-0.0024, +0.0646] | 0.066 |
| cohere | qwen8b | nDCG@10 | +0.0069 | [-0.0081, +0.0226] | 0.375 |
| cohere | qwen8b | Recall@1 | +0.0008 | [-0.0267, +0.0283] | 0.991 |
| cohere | qwen8b | Recall@5 | +0.0331 | [+0.0086, +0.0600] | 0.008 * |
| cohere | qwen | nDCG@10 | +0.0361 | [+0.0194, +0.0535] | 0.000 * |
| cohere | qwen | Recall@1 | +0.0382 | [+0.0075, +0.0700] | 0.012 * |
| cohere | qwen | Recall@5 | +0.0564 | [+0.0325, +0.0829] | 0.000 * |
| qwen8b | qwen | nDCG@10 | +0.0292 | [+0.0121, +0.0474] | 0.000 * |
| qwen8b | qwen | Recall@1 | +0.0373 | [+0.0097, +0.0667] | 0.007 * |
| qwen8b | qwen | Recall@5 | +0.0233 | [-0.0006, +0.0488] | 0.055 |

\* p < 0.05 (uncorrected; 18 comparisons, so treat p ≈ 0.01–0.05 as borderline).
