#!/bin/sh
# Prepare the scores of eval_plan_v2 in one unattended run (docs/evaluation/plan.md §10):
# write the Qwen essays (the main batch, then the short one), build the v2 manifests, then score every
# text that has no score yet.
# The 12,318 scores of eval_v1 are reused: same scorer, same revision, same normalization.
# Every step can be stopped and started again; finished work is kept. It prints "done" at the end.
set -e
cd "$(dirname "$0")"
caffeinate -i ../.venv/bin/python generate_qwen_essays.py
caffeinate -i ../.venv/bin/python generate_qwen_essays.py --short
../.venv/bin/python build_manifests_v2.py
mkdir -p ../results/eval_v2
[ -f ../results/eval_v2/scores.jsonl ] || cp ../results/eval_v1/scores.jsonl ../results/eval_v2/scores.jsonl
caffeinate -i ../.venv/bin/python score_corpora.py --v2 --data ../data/external --manifests manifests_v2 \
    --models ../data/external/models --out ../results/eval_v2
