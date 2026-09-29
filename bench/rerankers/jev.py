"""JEV (TypeSafe System One) as a pointwise reranker.

Same shape as the open-source hev-rerank wrapper (Apache-2.0): query + up to 30 docs in one
state, one Noul question per doc, evaluated in parallel. The Noul is an absolute probability,
so scores from different 30-doc calls are comparable. Prompt is hev-rerank's `generic-1`.
"""
from concurrent.futures import ThreadPoolExecutor

import httpx

from bench.rerankers.base import Reranker, api_key, post_json

URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"
MAX_DOCS = 30
MAX_STATE_CHARS = 100_000  # ~32k-token request budget, with headroom
QUESTION = "Document `documents.{id}` is relevant to `query`: it contains information that answers or directly addresses it."
CRITERIA = {
    "true": "The document contains information that answers the query or directly addresses what it asks about.",
    "false": "The document is only loosely related, on a similar topic, or does not address what the query asks.",
}


class Jev(Reranker):
    name = "jev"
    concurrency = 2  # queries in flight; each fans out to ~4 calls -> ~8 requests in flight

    def __init__(self):
        super().__init__()
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {api_key('TYPESAFE_API_KEY')}"}, timeout=90
        )
        self.model_version = None

    def _batches(self, docs):
        batch, chars = [], 0
        for i, d in enumerate(docs):
            if batch and (len(batch) >= MAX_DOCS or chars + len(d) > MAX_STATE_CHARS):
                yield batch
                batch, chars = [], 0
            batch.append(i)
            chars += len(d)
        if batch:
            yield batch

    def _score_batch(self, query, docs, idx):
        ids = {f"D{j:02d}": i for j, i in enumerate(idx)}
        payload = {
            "model": MODEL,
            "state": {"query": query, "documents": {k: docs[i] for k, i in ids.items()}},
            "questions": {
                k: {"type": "noul", "instructions": QUESTION.format(id=k), "criteria": CRITERIA} for k in ids
            },
        }
        r, secs, retries = post_json(self.client, URL, payload)
        self.model_version = r.get("model", self.model_version)
        u = r.get("usage", {})
        self.add_usage(calls=1, input_tokens=u.get("input_tokens"), output_tokens=u.get("output_tokens"))
        return [(i, float(r["answers"][k]["noul"])) for k, i in ids.items()], secs, retries

    def score(self, query, docs):
        batches = list(self._batches(docs))
        with ThreadPoolExecutor(len(batches)) as ex:
                parts = list(ex.map(lambda b: self._score_batch(query, docs, b), batches))
        scores = [0.0] * len(docs)
        for part, _, _ in parts:
            for i, s in part:
                scores[i] = s
        return scores, max(p[1] for p in parts), sum(p[2] for p in parts)
