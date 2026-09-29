## Paired bootstrap: A − B (300 queries, 10,000 resamples, seed 0)

| A | B | metric | A − B | 95% CI | p |
|---|---|---|---:|---|---:|
| jev | cohere | nDCG@10 | +0.0069 | [-0.0097, +0.0238] | 0.423 |
| jev | cohere | Recall@1 | +0.0218 | [-0.0080, +0.0527] | 0.155 |
| jev | cohere | Recall@5 | -0.0311 | [-0.0611, -0.0017] | 0.036 * |
| jev | qwen8b | nDCG@10 | +0.0130 | [-0.0079, +0.0343] | 0.229 |
| jev | qwen8b | Recall@1 | +0.0227 | [-0.0130, +0.0587] | 0.219 |
| jev | qwen8b | Recall@5 | +0.0020 | [-0.0313, +0.0354] | 0.909 |
| jev | qwen | nDCG@10 | +0.0418 | [+0.0202, +0.0641] | 0.000 * |
| jev | qwen | Recall@1 | +0.0600 | [+0.0217, +0.1000] | 0.004 * |
| jev | qwen | Recall@5 | +0.0253 | [-0.0077, +0.0592] | 0.135 |
| cohere | qwen8b | nDCG@10 | +0.0060 | [-0.0089, +0.0218] | 0.439 |
| cohere | qwen8b | Recall@1 | +0.0008 | [-0.0267, +0.0283] | 0.991 |
| cohere | qwen8b | Recall@5 | +0.0331 | [+0.0086, +0.0600] | 0.008 * |
| cohere | qwen | nDCG@10 | +0.0348 | [+0.0185, +0.0519] | 0.000 * |
| cohere | qwen | Recall@1 | +0.0382 | [+0.0075, +0.0700] | 0.012 * |
| cohere | qwen | Recall@5 | +0.0564 | [+0.0325, +0.0829] | 0.000 * |
| qwen8b | qwen | nDCG@10 | +0.0288 | [+0.0117, +0.0469] | 0.000 * |
| qwen8b | qwen | Recall@1 | +0.0373 | [+0.0097, +0.0667] | 0.007 * |
| qwen8b | qwen | Recall@5 | +0.0233 | [-0.0006, +0.0488] | 0.055 |

\* p < 0.05 (uncorrected; 18 comparisons, so treat p ≈ 0.01–0.05 as borderline).
