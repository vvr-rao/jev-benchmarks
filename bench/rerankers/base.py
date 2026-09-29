import os
import random
import time

import httpx
from dotenv import load_dotenv

load_dotenv()


def api_key(name: str) -> str:
    key = os.environ.get(name, "").strip()
    if not key:
        raise SystemExit(f"{name} is not set — add it to .env (see .env.example)")
    return key


def post_json(client: httpx.Client, url: str, payload: dict, retries: int = 8) -> tuple[dict, float, int]:
    """POST with exponential backoff on 429/5xx/timeouts. Never logs headers (they carry the key).

    Returns (json, seconds taken by the successful attempt, number of retries). The timing
    excludes backoff sleeps, so rate limiting doesn't inflate reported latency.
    """
    for attempt in range(retries):
        try:
            t = time.perf_counter()
            r = client.post(url, json=payload)
            if r.status_code == 429 or r.status_code >= 500:
                raise httpx.HTTPStatusError(f"{r.status_code}", request=r.request, response=r)
            if r.status_code >= 400:
                raise SystemExit(f"{url} -> HTTP {r.status_code}: {r.text[:500]}")
            return r.json(), time.perf_counter() - t, attempt
        except (httpx.HTTPStatusError, httpx.TransportError) as e:
            if attempt == retries - 1:
                raise
            wait = min(60, 2**attempt) + random.random()
            print(f"  retry {attempt + 1} after {e.__class__.__name__} {e}; sleeping {wait:.0f}s", flush=True)
            time.sleep(wait)
    raise AssertionError("unreachable")


class Reranker:
    """Subclasses implement score(query, docs) -> (scores, api_seconds, retries).

    scores: one float per doc, same order. api_seconds: time spent in successful API calls
    (wall time for concurrent calls), excluding client-side pacing and retry backoff.
    """

    name: str
    concurrency: int = 4

    def __init__(self):
        self.usage: dict[str, float] = {}

    def add_usage(self, **kw):
        for k, v in kw.items():
            self.usage[k] = self.usage.get(k, 0) + (v or 0)

    def score(self, query: str, docs: list[str]) -> tuple[list[float], float, int]:
        raise NotImplementedError
