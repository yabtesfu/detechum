#!/bin/sh
# Test the second signal of plan §10 in one unattended run: score the calib split with Desklib, apply the
# rule written before its scores were seen, then rerun the rehearsal with the combined score. Test texts are
# not scored. Every step can be stopped and started again. It prints "done" at the end.
set -e
cd "$(dirname "$0")"
caffeinate -i ../.venv/bin/python score_corpora.py --v2 --scorer desklib --splits calib --data ../data/external \
    --manifests manifests_v2 --models ../data/external/models --out ../results/eval_v2
../.venv/bin/python second_signal.py
../.venv/bin/python run_v2.py --rehearsal --scores ../results/second_signal_v1/scores_combined.jsonl \
    --out ../results/second_signal_v1/rehearsal
../.venv/bin/python report_v2.py ../results/second_signal_v1/rehearsal
echo done
