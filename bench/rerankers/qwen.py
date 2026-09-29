"""Qwen3-Reranker (0.6B / 8B) via DeepInfra's hosted inference API (same open weights, hosted).

This machine (Celeron N4500, no AVX) can't run it locally in reasonable time.
"""
import httpx

from bench.rerankers.base import Reranker, api_key, post_json

URL = "https://api.deepinfra.com/v1/inference/Qwen/Qwen3-Reranker-{size}"


class Qwen(Reranker):
    name = "qwen"
    concurrency = 4

    def __init__(self, size: str = "0.6B"):
        super().__init__()
        self.url = URL.format(size=size)
        self.client = httpx.Client(
            headers={"Authorization": f"bearer {api_key('DEEPINFRA_API_KEY')}"}, timeout=120
        )

    def score(self, query, docs):
        # one (query, doc) pair per position — unambiguous regardless of broadcast semantics
        r, secs, retries = post_json(self.client, self.url, {"queries": [query] * len(docs), "documents": docs})
        scores = r["scores"]
        if len(scores) != len(docs):
            raise SystemExit(f"DeepInfra returned {len(scores)} scores for {len(docs)} docs")
        st = r.get("inference_status", {})
        self.add_usage(calls=1, input_tokens=r.get("input_tokens"), cost_usd=st.get("cost"))
        return [float(s) for s in scores], secs, retries
