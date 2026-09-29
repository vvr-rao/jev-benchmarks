"""Download and load BEIR SciFact (test split) without the `beir` package."""
import csv
import io
import json
import zipfile
from pathlib import Path

import httpx

URL = "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/scifact.zip"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ROOT = DATA_DIR / "scifact"


def download() -> Path:
    if (ROOT / "corpus.jsonl").exists():
        return ROOT
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {URL}")
    r = httpx.get(URL, follow_redirects=True, timeout=120)
    r.raise_for_status()
    zipfile.ZipFile(io.BytesIO(r.content)).extractall(DATA_DIR)
    return ROOT


def _jsonl(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def load(split: str = "test"):
    """Returns (corpus, queries, qrels).

    corpus:  {doc_id: text}  — text is "title\\nabstract", identical for every reranker
    queries: {qid: text}     — only queries that have qrels in `split`
    qrels:   {qid: {doc_id: relevance}}
    """
    root = download()
    corpus = {}
    for d in _jsonl(root / "corpus.jsonl"):
        title = (d.get("title") or "").strip()
        corpus[str(d["_id"])] = f"{title}\n{d['text'].strip()}" if title else d["text"].strip()

    qrels: dict[str, dict[str, int]] = {}
    with open(root / "qrels" / f"{split}.tsv") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)  # header
        for qid, did, score in reader:
            qrels.setdefault(qid, {})[did] = int(score)

    queries = {str(q["_id"]): q["text"] for q in _jsonl(root / "queries.jsonl") if str(q["_id"]) in qrels}
    return corpus, queries, qrels
