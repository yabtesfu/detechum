"""Write the split manifests of the evaluation (docs/evaluation/plan.md §1).

One row per text with its SHA 256 and metadata. No text is written. A text is identified by the
SHA 256 of its UTF 8 bytes as stored in the corpus.

Splits:

* Texts used in the pilots go to calib, because their labels and scores have been seen.
* Every other group (a prompt, a topic or a document, see eval/corpora.py) goes whole to calib or
  to test. Within a source, groups are shuffled with a fixed seed and each is given to the split
  that holds fewer texts of that source so far.
* A text that occurs more than once is kept once, with the first record that holds it.

There is no train split: no scorer is trained here. The scorer's own training data is described
by its model card and marked in `flags` where a source overlaps it.

Usage: python eval/build_manifests.py [--data data/external] [--out eval/manifests]
"""

import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from corpora import load_all
from detechum.normalize import normalize

SEED = 20261119
SPLITS = ("calib", "test")


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def assign_splits(records: list[dict]) -> None:
    by_source = defaultdict(lambda: defaultdict(list))
    for r in records:
        by_source[r["source"]][r["group_key"]].append(r)
    for source in sorted(by_source):
        groups = by_source[source]
        keys = sorted(groups)
        random.Random(f"{SEED}/{source}").shuffle(keys)
        size = Counter()
        for key in keys:
            members = groups[key]
            split = "calib" if any("pilot" in r["flags"] for r in members) else min(SPLITS, key=lambda s: size[s])
            size[split] += len(members)
            for r in members:
                r["split"] = split


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", type=Path, default=Path("data/external"))
    ap.add_argument("--out", type=Path, default=Path("eval/manifests"))
    args = ap.parse_args()

    seen, records, duplicates = set(), [], 0
    for r in load_all(args.data):
        digest = sha256(r["text"])
        if digest in seen:
            duplicates += 1
            continue
        seen.add(digest)
        # The length is counted as the command counts it: on the normalized text.
        records.append({"sha256": digest, "length_words": len(normalize(r["text"])[0].split()),
                        **{k: v for k, v in r.items() if k != "text"}})
    assign_splits(records)

    args.out.mkdir(parents=True, exist_ok=True)
    for split in SPLITS:
        rows = [r for r in records if r["split"] == split]
        (args.out / f"{split}.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
        print(f"{split}: {len(rows)} texts", dict(Counter((r['source'], r['label']) for r in rows)))
    print(f"{duplicates} repeated texts left out")


if __name__ == "__main__":
    main()
