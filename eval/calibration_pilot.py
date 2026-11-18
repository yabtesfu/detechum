"""Pilot of the calibration layer on the bias_v1 scores (docs/evaluation/plan.md §8).

Fits the score to P(AI) map on the labelled Liang groups and reports held out calibration error from
five fold cross validation. The groups are not a split of the evaluation plan, the AI text is from
2023 and the folds share one domain mix, so the output shows that the layer works and nothing about
release quality.

Usage: python eval/calibration_pilot.py [--scores results/bias_v1/scores.jsonl] [--out results/calibration_pilot_v1]
"""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from detechum.calibration import (INTERVAL_LEVEL, brier_score, choose_tau, expected_calibration_error,
                                  fit_calibrator, reliability_bins)
from detechum.stats import clopper_pearson
from detechum.verdict import MIN_WORDS_FOR_VERDICT, Verdict, decide_verdict

SEED = 20261118
FOLDS = 5
TARGET_FPR = 0.01
SCORER = "gpttrace_v8s_1b_typography_off"
HUMAN_ROLES = {"human_native", "human_nonnative", "human_unknown"}
# "ai_edited" texts have no agreed label and the length matched control repeats essays of a human
# group, so neither takes part in fitting or in the calibration metrics.
LABELLED_ROLES = HUMAN_ROLES | {"ai"}


def load(scores_path: Path, scorer: str) -> list[dict]:
    roles = {g: v["role"] for g, v in
             json.loads((scores_path.parent / "metrics.json").read_text())["results"][scorer]["groups"].items()}
    rows = [json.loads(line) for line in scores_path.read_text().splitlines()]
    rows = [r | {"role": roles[r["group"]]} for r in rows if r["scorer"] == scorer]
    if not rows:
        raise SystemExit(f"no scores for {scorer} in {scores_path}")
    return rows


def assign_folds(rows: list[dict], rng: np.random.Generator) -> None:
    by_group = defaultdict(list)
    for r in rows:
        by_group[r["group"]].append(r)
    for group in sorted(by_group):
        for position, i in enumerate(rng.permutation(len(by_group[group]))):
            by_group[group][i]["fold"] = position % FOLDS


def apply(calibrator, tau, row: dict) -> None:
    doc = calibrator.scored_document(row["ai_score"], row["n_words"])
    row["p_ai"], row["p_low"], row["p_high"] = doc.p_ai, doc.p_low, doc.p_high
    row["verdict"] = Verdict.NO_VERDICT.name if tau is None else decide_verdict(doc, tau).name
    row["low_at_or_above_tau"] = tau is not None and doc.p_low >= tau


def group_table(rows: list[dict]) -> list[dict]:
    by_group = defaultdict(list)
    for r in rows:
        by_group[r["group"]].append(r)
    table = []
    for group, items in by_group.items():
        verdicts = Counter(r["verdict"] for r in items)
        table.append({
            "group": group, "role": items[0]["role"], "n": len(items),
            "median_p_ai": float(np.median([r["p_ai"] for r in items])),
            "long_enough": sum(r["n_words"] >= MIN_WORDS_FOR_VERDICT for r in items),
            "likely_ai": verdicts[Verdict.LIKELY_AI.name], "likely_human": verdicts[Verdict.LIKELY_HUMAN.name],
            "cant_tell": verdicts[Verdict.CANT_TELL.name],
            "low_at_or_above_tau_any_length": sum(r["low_at_or_above_tau"] for r in items),
        })
    return table


def reliability_svg(bins: list[dict]) -> str:
    size, pad = 320, 48
    x = lambda v: pad + v * size
    y = lambda v: pad + (1 - v) * size
    largest = max(b["n"] for b in bins)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size + 2 * pad} {size + 2 * pad}" '
             'font-family="sans-serif" font-size="11">',
             '<rect width="100%" height="100%" fill="#ffffff"/>',
             f'<rect x="{pad}" y="{pad}" width="{size}" height="{size}" fill="none" stroke="#444"/>',
             f'<line x1="{x(0)}" y1="{y(0)}" x2="{x(1)}" y2="{y(1)}" stroke="#999" stroke-dasharray="4 4"/>']
    for tick in (0, 0.25, 0.5, 0.75, 1):
        parts.append(f'<text x="{x(tick)}" y="{y(0) + 16}" text-anchor="middle" fill="#222">{tick:g}</text>')
        parts.append(f'<text x="{x(0) - 8}" y="{y(tick) + 4}" text-anchor="end" fill="#222">{tick:g}</text>')
    for b in bins:
        cx = x(b["mean_predicted"])
        parts.append(f'<line x1="{cx:.1f}" y1="{y(b["ci95"][0]):.1f}" x2="{cx:.1f}" y2="{y(b["ci95"][1]):.1f}" '
                     'stroke="#1f5fa8"/>')
        parts.append(f'<circle cx="{cx:.1f}" cy="{y(b["observed"]):.1f}" r="{2 + 4 * (b["n"] / largest) ** 0.5:.1f}" '
                     'fill="#1f5fa8" fill-opacity="0.6"/>')
    parts.append(f'<text x="{x(0.5)}" y="{y(0) + 36}" text-anchor="middle" fill="#222">Predicted P(AI)</text>')
    parts.append(f'<text transform="translate(14 {y(0.5)}) rotate(-90)" text-anchor="middle" fill="#222">'
                 'Observed share of AI texts</text>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def render_report(metrics: dict) -> str:
    cv, final = metrics["cross_validation"], metrics["final_calibrator"]

    def rows(table):
        return [f"| {t['group']} | {t['role']} | {t['n']} | {t['median_p_ai']:.3f} | {t['long_enough']} | "
                f"{t['likely_ai']} | {t['likely_human']} | {t['cant_tell']} | {t['low_at_or_above_tau_any_length']} |"
                for t in table]

    header = [f"| Group | Role | n | Median P(AI) | Texts of {MIN_WORDS_FOR_VERDICT}+ words | Likely AI | Likely human | "
              "Can't tell | Lower bound at or above tau, any length |", "|---|---|---|---|---|---|---|---|---|"]
    fp = cv["human_false_positives"]
    lines = [
        "# Calibration pilot (calibration_pilot_v1)", "",
        f"Scorer: `{metrics['scorer']}`. Input: `{metrics['scores_file']}` (SHA 256 `{metrics['scores_sha256']}`).",
        f"Fitted on {metrics['n_human']} human and {metrics['n_ai']} AI texts, so P(AI) assumes that mix.",
        f"The interval is the {round(INTERVAL_LEVEL * 100)}% range. Seed `{metrics['seed']}`.", "",
        "This is a pilot on 2023 data from one source. It checks that the calibration layer works. "
        "It is not evidence about release quality.", "",
        f"## Held out results ({FOLDS} fold cross validation)", "",
        f"* ECE (15 equal mass bins): {cv['ece']:.4f}",
        f"* Brier score: {cv['brier']:.4f}",
        f"* Decision threshold tau per fold: {', '.join('none' if t is None else f'{t:.3f}' for t in cv['tau_per_fold'])}",
        f"* Human texts of {MIN_WORDS_FOR_VERDICT}+ words labelled Likely AI: {fp['flagged']}/{fp['n']} "
        f"(95% interval {fp['ci95'][0] * 100:.1f}% to {fp['ci95'][1] * 100:.1f}%)", "",
        "![Reliability diagram](reliability.svg)", "",
        "| Bin | n | Mean predicted P(AI) | Observed share of AI | 95% interval |", "|---|---|---|---|---|",
    ]
    lines += [f"| {i} | {b['n']} | {b['mean_predicted']:.3f} | {b['observed']:.3f} | "
              f"{b['ci95'][0]:.3f} to {b['ci95'][1]:.3f} |" for i, b in enumerate(cv["reliability_bins"], start=1)]
    lines += ["", "Verdicts apply the length rule, so shorter texts receive no verdict. The last column counts "
              "texts whose lower bound reaches tau when length is ignored.", "", *header, *rows(cv["groups"]), "",
              "## AI edited human text, scored with the final calibrator", "",
              f"The final calibrator is fitted on all labelled texts. Its tau is "
              f"{'none' if final['tau'] is None else format(final['tau'], '.3f')}.", "",
              *header, *rows(final["ai_edited_groups"]), ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scores", type=Path, default=Path("results/bias_v1/scores.jsonl"))
    parser.add_argument("--out", type=Path, default=Path("results/calibration_pilot_v1"))
    parser.add_argument("--scorer", default=SCORER)
    args = parser.parse_args()

    rows = load(args.scores, args.scorer)
    labelled = [r for r in rows if r["role"] in LABELLED_ROLES]
    for r in labelled:
        r["label"] = int(r["role"] == "ai")
    assign_folds(labelled, np.random.default_rng(SEED))

    taus = []
    for fold in range(FOLDS):
        train = [r for r in labelled if r["fold"] != fold]
        calibrator = fit_calibrator([r["ai_score"] for r in train], [r["label"] for r in train], seed=SEED + fold)
        tau = choose_tau(calibrator, [r["ai_score"] for r in train if r["label"] == 0], TARGET_FPR)
        taus.append(tau)
        for r in labelled:
            if r["fold"] == fold:
                apply(calibrator, tau, r)

    p_ai, labels = [r["p_ai"] for r in labelled], [r["label"] for r in labelled]
    eligible_humans = [r for r in labelled if r["label"] == 0 and r["n_words"] >= MIN_WORDS_FOR_VERDICT]
    flagged = sum(r["verdict"] == Verdict.LIKELY_AI.name for r in eligible_humans)
    bins = reliability_bins(p_ai, labels)

    final = fit_calibrator([r["ai_score"] for r in labelled], labels, seed=SEED)
    final_tau = choose_tau(final, [r["ai_score"] for r in labelled if r["label"] == 0], TARGET_FPR)
    edited = [dict(r) for r in rows if r["role"] == "ai_edited"]
    for r in edited:
        apply(final, final_tau, r)

    metrics = {
        "scorer": args.scorer, "scores_file": args.scores.as_posix(),
        "scores_sha256": hashlib.sha256(args.scores.read_bytes()).hexdigest(),
        "seed": SEED, "target_fpr": TARGET_FPR, "n_human": final.n_human, "n_ai": final.n_ai,
        "cross_validation": {
            "folds": FOLDS, "ece": expected_calibration_error(p_ai, labels), "brier": brier_score(p_ai, labels),
            "tau_per_fold": taus, "reliability_bins": bins, "groups": group_table(labelled),
            "human_false_positives": {"flagged": flagged, "n": len(eligible_humans),
                                      "ci95": list(clopper_pearson(flagged, len(eligible_humans)))},
        },
        "final_calibrator": {"tau": final_tau, "ai_edited_groups": group_table(edited)},
    }
    calibration = {
        "name": "calibration_pilot_v1", "scorer": args.scorer, "tau": final_tau, "target_fpr": TARGET_FPR,
        "description": "Pilot: Liang et al. 2023 student essays and CS224N abstracts, AI text from GPT 3 (2023). "
                       "Not validated for release.",
        "calibrator": final.to_dict(),
    }

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "metrics.json").write_text(json.dumps(metrics, indent=1) + "\n")
    (args.out / "calibration.json").write_text(json.dumps(calibration) + "\n")
    (args.out / "reliability.svg").write_text(reliability_svg(bins))
    (args.out / "report.md").write_text(render_report(metrics))
    print(f"wrote {args.out}/report.md, metrics.json, calibration.json and reliability.svg")


if __name__ == "__main__":
    main()
