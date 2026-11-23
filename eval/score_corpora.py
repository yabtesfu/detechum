"""Score every text of the split manifests with the primary scorer (docs/evaluation/plan.md §4).

Texts are normalized first, as `detechum score` does, so the scores are those the command would
give. The output holds one row per text with its SHA 256 and no label, so that writing it reads no
label of the test split. An interrupted run continues from the rows already written.

Usage: python eval/score_corpora.py [--data data/external] [--manifests eval/manifests] [--out results/eval_v1]
"""

import argparse
import hashlib
import json
from pathlib import Path

import torch

from corpora import load_all, load_all_v2
from detechum.models import GPTTRACE, ModelVerificationError, verify_model
from detechum.normalize import normalize
from detechum.scorers.gpttrace import GPTTraceScorer

BATCH = 8


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", type=Path, default=Path("data/external"))
    ap.add_argument("--manifests", type=Path, default=Path("eval/manifests"))
    ap.add_argument("--models", type=Path, default=Path("data/external/models"))
    ap.add_argument("--out", type=Path, default=Path("results/eval_v1"))
    ap.add_argument("--device", default="mps" if torch.backends.mps.is_available() else "cpu")
    ap.add_argument("--v2", action="store_true", help="read the corpora of eval_plan_v2 (plan §10)")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    wanted = {json.loads(line)["sha256"] for split in ("calib", "test")
              for line in (args.manifests / f"{split}.jsonl").read_text().splitlines()}
    texts = {}
    for r in (load_all_v2 if args.v2 else load_all)(args.data):
        texts.setdefault(hashlib.sha256(r["text"].encode("utf-8")).hexdigest(), r["text"])
    missing = wanted - texts.keys()
    if missing:
        raise SystemExit(f"{len(missing)} manifest texts are not in {args.data}; rerun eval/fetch_data.py")

    scores_file = args.out / "scores.jsonl"
    done = {json.loads(line)["sha256"] for line in scores_file.read_text().splitlines()} if scores_file.exists() else set()
    todo = sorted(wanted - done)
    print(f"{len(done)} texts already scored, {len(todo)} to score", flush=True)
    if not todo:
        return
    try:
        scorer = GPTTraceScorer(verify_model(GPTTRACE, args.models), args.device, typography=False)
    except ModelVerificationError as exc:
        raise SystemExit(f"{exc}; rerun eval/fetch_models.py")
    with scores_file.open("a") as fh:
        for start in range(0, len(todo), BATCH):
            batch = todo[start:start + BATCH]
            cleaned = [normalize(texts[digest])[0] for digest in batch]
            for digest, text, value in zip(batch, cleaned, scorer.score(cleaned, batch_size=BATCH)):
                fh.write(json.dumps({"sha256": digest, "scorer": scorer.name, "ai_score": value,
                                     "truncated": scorer.is_truncated(text)}) + "\n")
            fh.flush()
            if (start // BATCH) % 25 == 0:
                print(f"{start + len(batch)}/{len(todo)}", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
