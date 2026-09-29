"""One tiny request per API to validate keys and payload formats before a real run."""
import sys

from bench.run import get_reranker

QUERY = "Vitamin D supplementation increases bone mineral density in older adults."
DOCS = [
    "Vitamin D and bone density\nIn a randomized trial of adults over 65, vitamin D3 supplementation increased lumbar spine bone mineral density.",
    "Coffee consumption and sleep\nEvening caffeine intake delayed sleep onset in healthy volunteers.",
]

ok = True
for name in (sys.argv[1].split(",") if len(sys.argv) > 1 else ["jev", "cohere", "qwen"]):
    try:
        rr = get_reranker(name)
        s, _, _ = rr.score(QUERY, DOCS)
        verdict = "OK" if s[0] > s[1] else "WARN: relevant doc did not score higher"
        print(f"{name:7s} {verdict}  relevant={s[0]:.4f} irrelevant={s[1]:.4f}  usage={rr.usage}")
    except SystemExit as e:
        ok = False
        print(f"{name:7s} FAIL  {e}")
    except Exception as e:
        ok = False
        print(f"{name:7s} FAIL  {e.__class__.__name__}: {e}")
sys.exit(0 if ok else 1)
