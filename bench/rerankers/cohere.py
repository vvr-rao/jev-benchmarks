"""Cohere Rerank 4 Pro via the v2 REST API (one call per query, all candidates)."""
import os
import time

import httpx

from bench.rerankers.base import Reranker, api_key, post_json

URL = "https://api.cohere.com/v2/rerank"
MODEL = "rerank-v4.0-pro"
# Trial keys allow ~10 rerank calls/min; pace client-side instead of burning retries on 429s.
# Set COHERE_MIN_INTERVAL_S=0 in .env for a production key.
MIN_INTERVAL_S = float(os.environ.get("COHERE_MIN_INTERVAL_S", "6.5"))


class Cohere(Reranker):
    name = "cohere"
    concurrency = 1

    def __init__(self):
        super().__init__()
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {api_key('COHERE_API_KEY')}"}, timeout=90
        )
        self._last_call = 0.0

    def score(self, query, docs):
        wait = self._last_call + MIN_INTERVAL_S - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self._last_call = time.monotonic()
        r, secs, retries = post_json(self.client, URL, {"model": MODEL, "query": query, "documents": docs, "top_n": len(docs)}, retries=15)
        bu = r.get("meta", {}).get("billed_units", {})
        self.add_usage(calls=1, search_units=bu.get("search_units"))
        scores = [0.0] * len(docs)
        for res in r["results"]:
            scores[res["index"]] = float(res["relevance_score"])
        return scores, secs, retries
