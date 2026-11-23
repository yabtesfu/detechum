"""Write the split manifests of eval_plan_v2 (docs/evaluation/plan.md §10).

Rules, in this order:

* A text of eval_v1 keeps its split, read from eval/manifests.
* A text flagged "seen_before_freeze" goes to calib.
* An essay written on an ELLIPSE prompt goes to the split of that prompt's ELLIPSE essays, so that the
  human and AI essays on one topic are never in different splits.
* Every other new group goes whole to calib or test, balanced within its source as in eval_v1.

Human texts of the new sources are all kept. AI texts of the new sources are sampled with a fixed seed,
at most `CAP[source]` per cell of source, label, generator, variant and attack flag, so that scoring fits
into one night. No text is written to the manifests.

Usage: cd eval && ../.venv/bin/python build_manifests_v2.py
"""

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from build_manifests import SPLITS, assign_splits, sha256
from corpora import load_all_v2
from detechum.normalize import normalize

SEED = 20261121
CAP = {"gede": 120, "ghostbuster": 100, "dactyl": 60, "claude_essays": None, "qwen_essays": None}


def cell(r: dict) -> tuple:
    return r["source"], r["label"], r["generator"], r.get("variant"), "attacked" in r["flags"]


def sample(records: list[dict]) -> list[dict]:
    cells = defaultdict(list)
    for r in records:
        cells[cell(r)].append(r)
    kept = []
    for key in sorted(cells, key=str):
        members = sorted(cells[key], key=lambda r: r["sha256"])
        cap = CAP[key[0]]
        if key[1] != "human" and cap is not None and len(members) > cap:
            members = random.Random(f"{SEED}/{key}").sample(members, cap)
        kept += members
    return kept


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", type=Path, default=Path("../data/external"))
    ap.add_argument("--v1", type=Path, default=Path("manifests"))
    ap.add_argument("--out", type=Path, default=Path("manifests_v2"))
    args = ap.parse_args()

    v1 = {json.loads(line)["sha256"]: json.loads(line)["split"]
          for split in SPLITS for line in (args.v1 / f"{split}.jsonl").read_text().splitlines()}
    seen, old, new, duplicates = set(), [], [], 0
    for r in load_all_v2(args.data):
        digest = sha256(r["text"])
        if digest in seen:
            duplicates += 1
            continue
        seen.add(digest)
        row = {"sha256": digest, "length_words": len(normalize(r["text"])[0].split()),
               **{k: v for k, v in r.items() if k != "text"}}
        if r["source"] in CAP:
            new.append(row)
        elif digest in v1:
            old.append(row | {"split": v1[digest]})
    prompt_split = {r["topic"]: r["split"] for r in old if r["source"] == "ellipse"}

    new = sample(new)
    rest = []
    for r in new:
        if "seen_before_freeze" in r["flags"]:
            r["split"] = "calib"
        elif r.get("topic") in prompt_split:
            r["split"] = prompt_split[r["topic"]]
        else:
            rest.append(r)
    assign_splits(rest)

    records = old + new
    args.out.mkdir(parents=True, exist_ok=True)
    for split in SPLITS:
        rows = [r for r in records if r["split"] == split]
        (args.out / f"{split}.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
        print(f"{split}: {len(rows)} texts", dict(sorted(Counter((r["source"], r["label"]) for r in rows).items())))
    print(f"{len(new)} new texts after sampling, {duplicates} repeated texts left out")
    groups = defaultdict(set)
    for r in records:
        groups[r["group_key"]].add(r["split"])
    print("groups in both splits:", sum(len(s) > 1 for s in groups.values()))


if __name__ == "__main__":
    main()
