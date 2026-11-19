"""Nonnative test of the top 1 token rate before it is used in explanations (architecture §5 and §8).

The explanation template compares a text's top 1 token rate with "the human median". That comparison
misleads a nonnative writer if nonnative human text has a higher rate than native human text of the
same length. This run measures the gap on the Liang et al. 2023 groups.

Decision rule, fixed before the run. The threshold is the rate exceeded by 1% of native essays.
* fail: the 95% interval of the share of TOEFL essays above the threshold lies entirely above the
  interval of the length matched native control.
* undecided: anything else. The admission test of architecture §2.4 needs at least 183 nonnative
  texts, so 91 essays cannot show a pass.

Essays stay in data/external/. Only SHA 256 hashes and numbers are written to the output folder.

Usage: python eval/explanation_pilot.py --liang data/external/liang --out results/explanation_pilot_v1
"""

import argparse
import json
import platform
from pathlib import Path

import numpy as np
import torch
import transformers
from scipy.stats import mannwhitneyu

from bias_experiment import CONTROL, MODELS, TARGET_FPR, load_groups, sha256, verify_models
from detechum.scorers.token_stats import TokenStatsScorer
from detechum.stats import flag_stats, threshold_for_fpr

SCORER_NAME = "token_stats_qwen2.5_1.5b"
NONNATIVE = "TOEFL_real_91"


def score_all(groups: dict, model_dir: Path, out: Path, device: str) -> list[dict]:
    cache_file = out / "scores.jsonl"
    rows = [json.loads(line) for line in cache_file.read_text().splitlines()] if cache_file.exists() else []
    done = {(r["group"], r["index"]) for r in rows}
    scorer = None
    with cache_file.open("a") as fh:
        for name, group in groups.items():
            todo = [i for i in range(len(group["texts"])) if (name, i) not in done]
            if not todo:
                continue
            scorer = scorer or TokenStatsScorer(model_dir, device, SCORER_NAME)
            print(f"{SCORER_NAME}: {name} ({len(todo)} texts)", flush=True)
            for i, stats in zip(todo, scorer.stats([group["texts"][i] for i in todo])):
                text = group["texts"][i]
                row = {"scorer": SCORER_NAME, "group": name, "index": i, "sha256": sha256(text),
                       "n_words": len(text.split()), "n_predicted_tokens": len(stats.top1),
                       "top1_rate": stats.top1_rate, "mean_surprisal": float(np.mean(stats.surprisal))}
                fh.write(json.dumps(row) + "\n")
                rows.append(row)
    return rows


def auroc(higher: list[float], lower: list[float]) -> float:
    """Probability that a value drawn from `higher` exceeds one drawn from `lower`."""
    return float(mannwhitneyu(higher, lower).statistic / (len(higher) * len(lower)))


def summarize(groups: dict, rows: list[dict]) -> dict:
    rates = {name: [r["top1_rate"] for r in rows if r["group"] == name] for name in groups}
    roles = {name: g["role"] for name, g in groups.items()}
    native = [v for name, vals in rates.items() if roles[name] == "human_native" for v in vals]
    human = [v for name, vals in rates.items() if roles[name].startswith("human") and name != CONTROL for v in vals]
    ai = [v for name, vals in rates.items() if roles[name] == "ai" for v in vals]
    threshold = threshold_for_fpr(native, TARGET_FPR)
    per_group = {
        name: {"role": roles[name], "n": len(vals), "median_top1_rate": float(np.median(vals)),
               "quartiles": [float(np.quantile(vals, 0.25)), float(np.quantile(vals, 0.75))],
               "above_threshold": flag_stats(vals, threshold)}
        for name, vals in rates.items()
    }
    nonnative, control = per_group[NONNATIVE]["above_threshold"], per_group[CONTROL]["above_threshold"]
    return {
        "threshold_native_1pct": threshold,
        "native_median_top1_rate": float(np.median(native)),
        "auroc_ai_vs_all_human": auroc(ai, human),
        "auroc_nonnative_vs_length_matched_native": auroc(rates[NONNATIVE], rates[CONTROL]),
        "outcome": "fail" if nonnative["ci95"][0] > control["ci95"][1] else "undecided",
        "groups": per_group,
    }


def render_report(result: dict) -> str:
    env, s = result["environment"], result["results"]
    lines = [
        "# Nonnative test of the top 1 token rate (explanation_pilot_v1)", "",
        f"Data: Liang et al. 2023 repository at commit `{env['liang_commit']}`. Language model: "
        f"`{env['model']['repo']}` at revision `{env['model']['revision']}`, bfloat16, first 512 tokens of each text.",
        f"Python {env['python']}, torch {env['torch']}, transformers {env['transformers']}, {env['machine']}.", "",
        "The top 1 token rate is the share of tokens that were the language model's single most likely next token.", "",
        f"* Outcome under the rule fixed before the run: **{s['outcome']}**",
        f"* Threshold, the rate exceeded by 1% of native essays: {s['threshold_native_1pct']:.3f}",
        f"* Median rate of native essays: {s['native_median_top1_rate']:.3f}",
        f"* Probability that a TOEFL essay has a higher rate than a native essay of the same length: "
        f"{s['auroc_nonnative_vs_length_matched_native']:.3f} (0.5 means no difference)",
        f"* AUROC of the rate alone, AI groups against all human groups: {s['auroc_ai_vs_all_human']:.3f}", "",
        "| Group | Role | n | Median rate | Quartiles | Above the threshold (95% interval) |", "|---|---|---|---|---|---|",
    ]
    for name, g in s["groups"].items():
        a = g["above_threshold"]
        lines.append(f"| {name} | {g['role']} | {g['n']} | {g['median_top1_rate']:.3f} | "
                     f"{g['quartiles'][0]:.3f} to {g['quartiles'][1]:.3f} | {a['flagged']}/{a['n']} = "
                     f"{a['rate'] * 100:.1f}% ({a['ci95'][0] * 100:.1f} to {a['ci95'][1] * 100:.1f}) |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--liang", type=Path, required=True)
    ap.add_argument("--models", type=Path, default=Path("data/external/models"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--device", default="mps" if torch.backends.mps.is_available() else "cpu")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    groups = load_groups(args.liang)
    model_dir = verify_models(args.models, keys=("qwen_base",))["qwen_base"]
    rows = score_all(groups, model_dir, args.out, args.device)
    liang_commit = (args.liang / ".git" / "HEAD").read_text().strip()
    if liang_commit.startswith("ref: "):
        liang_commit = (args.liang / ".git" / liang_commit[5:]).read_text().strip()
    result = {
        "environment": {"python": platform.python_version(), "torch": torch.__version__,
                        "transformers": transformers.__version__, "machine": platform.machine(),
                        "liang_commit": liang_commit, "target_fpr": TARGET_FPR,
                        "model": MODELS["qwen_base"].record()},
        "results": summarize(groups, rows),
    }
    (args.out / "metrics.json").write_text(json.dumps(result, indent=1) + "\n")
    (args.out / "report.md").write_text(render_report(result))
    print(f"wrote {args.out}/metrics.json and report.md")


if __name__ == "__main__":
    main()
