"""JEV (TypeSafe System One) as a pointwise reranker.

Same shape as the open-source hev-rerank wrapper (Apache-2.0): query + up to 30 docs in one
state, one Noul question per doc, evaluated in parallel. The Noul is an absolute probability,
so scores from different 30-doc calls are comparable.

Prompts are versioned; select one with the reranker name "jev@<version>" (plain "jev" = generic-1).
  generic-1   hev-rerank's domain-neutral prompt (used for the first SciFact / HotpotQA-500 runs)
  scifact-v1  claim verification: supporting OR refuting evidence counts
  hotpotqa-v1 multi-hop: answer facts, comparison facts, and intermediate (bridge) entities count
"""
from concurrent.futures import ThreadPoolExecutor

import httpx

from bench.rerankers.base import Reranker, api_key, post_json

URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"
MAX_DOCS = 30
# ~32k-token request budget (state + questions), with headroom. Source: the hev-rerank wrapper
# (github.com/hev/jev-rerank, same value and rationale) and Hindsight's "Adding Jev as a
# reranker" post (hindsight.vectorize.io, 2026-09-24) -- not confirmed in TypeSafe's own docs.
MAX_STATE_CHARS = 100_000
PROMPTS = {
    "generic-1": {
        "question": "Document `documents.{id}` is relevant to `query`: it contains information that answers or directly addresses it.",
        "criteria": {
            "true": "The document contains information that answers the query or directly addresses what it asks about.",
            "false": "The document is only loosely related, on a similar topic, or does not address what the query asks.",
        },
    },
    "scifact-v1": {
        "question": "Does `documents.{id}` contain evidence useful for assessing the scientific claim in `query`?",
        "criteria": {
            "true": (
                "The document reports findings that support or refute the claim, "
                "or directly bear on whether it is true. Agreement with the claim "
                "is not required."
            ),
            "false": (
                "The document only shares terminology or background topics, "
                "without evidence bearing on the claim."
            ),
        },
    },
    "hotpotqa-v1": {
        "question": (
            "Does `documents.{id}` contribute evidence needed to answer `query`, "
            "either directly or as an intermediate step?"
        ),
        "criteria": {
            "true": (
                "The document supplies an answer fact, a fact needed for a "
                "comparison, or an intermediate entity or relationship linking "
                "the question to its answer. Other documents may clarify its role, "
                "but the target document must itself supply useful evidence."
            ),
            "false": (
                "The document merely shares a topic or entity, or contributes "
                "no evidence to answering the question. Evidence found only in "
                "another document does not make the target document relevant."
            ),
        },
    },
}


class Jev(Reranker):
    name = "jev"
    concurrency = 4  # queries in flight; SciFact fans out to ~4 calls per query

    def __init__(self, prompt: str = "generic-1"):
        super().__init__()
        if prompt not in PROMPTS:
            raise SystemExit(f"unknown JEV prompt {prompt!r}; choose from {sorted(PROMPTS)}")
        self.prompt_version = prompt
        self.prompt = PROMPTS[prompt]
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
                k: {"type": "noul", "instructions": self.prompt["question"].format(id=k), "criteria": self.prompt["criteria"]}
                for k in ids
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
