"""Write records.jsonl for the Claude essays of eval_plan_v2 (plan §10).

The essays were written on 20 Nov 2026 by six Claude Code subagents, two for each model alias below, each
from a list of 50 tasks drawn by `essay_tasks.tasks` with the seed given here. Each subagent saved one
essay per task as <id>.txt in data/external/generated/claude. This script rebuilds the task lists from the
seeds and writes one record per essay that exists.

Known limits of this way of generating: decoding settings cannot be set, the subagents run with the
system prompt of Claude Code, and none of the 300 essays contains an em dash, which suggests that the
session's writing style rules reached the subagents.

Usage: cd eval && ../.venv/bin/python record_claude_essays.py
"""

import argparse
import json
from pathlib import Path

from essay_tasks import tasks

WRITTEN = "2026-11-20"
# (agent number, model alias given to the subagent, model id of that alias on the day)
AGENTS = [(0, "opus", "claude-opus-5-5"), (1, "opus", "claude-opus-5-5"), (2, "sonnet", "claude-sonnet-5-5"),
          (3, "sonnet", "claude-sonnet-5-5"), (4, "haiku", "claude-haiku-5-5"), (5, "haiku", "claude-haiku-5-5")]
SEED_BASE = 20261120
PER_AGENT = 50


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", type=Path, default=Path("../data/external/generated/claude"))
    args = ap.parse_args()
    rows, missing = [], []
    for k, alias, model in AGENTS:
        for t in tasks(PER_AGENT, SEED_BASE + k, f"claude-{alias}-{k}-"):
            if not (args.dir / f"{t['id']}.txt").exists():
                missing.append(t["id"])
                continue
            rows.append(t | {"generator": model, "model_alias": alias, "seed": SEED_BASE + k,
                             "written_by": "Claude Code subagent", "decoding": None, "written_at": WRITTEN})
    (args.dir / "records.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    print(f"{len(rows)} records written, {len(missing)} essays missing")


if __name__ == "__main__":
    main()
