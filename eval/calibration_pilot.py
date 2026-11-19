"""Pilot of the calibration layer on the bias_v1 scores (docs/evaluation/plan.md §8).

Fits the score to P(AI) map and the conformal abstention layer on the labelled Liang groups and
reports held out results from five fold cross validation. The groups are not a split of the
evaluation plan, the AI text is from 2023 and the folds share one domain mix, so the output shows
that the layers work and nothing about release quality.

Version 2 adds the conformal layer (`detechum.conformal`). The calibration map, its seed and its
metrics are those of version 1, whose outputs stay in results/calibration_pilot_v1.

Two layers are evaluated. "banded" uses the length bands of the evaluation plan and is the one
written to calibration.json. "single_band" pools all texts of 150 words or more and shows what the
bands cost on a corpus this small. It is written to calibration_single_band.json.

Reading of the conformal result, fixed before the run: a layer fails the pilot if, for either
class, the 95% Clopper Pearson interval of the held out share of texts whose own class was ruled
out lies entirely above the alpha of that class. A band with too few calibration texts rules
nothing out, so it cannot fail this way; the report lists which labels each band can give.

Usage: python eval/calibration_pilot.py [--scores results/bias_v1/scores.jsonl] [--out results/calibration_pilot_v2]
"""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from detechum.calibration import (INTERVAL_LEVEL, brier_score, choose_tau, expected_calibration_error,
                                  fit_calibrator, reliability_bins)
from detechum.conformal import fit_conformal, min_calibration_texts
from detechum.stats import clopper_pearson
from detechum.verdict import MIN_WORDS_FOR_VERDICT, Verdict, decide_verdict

SEED = 20261118
FOLDS = 5
TARGET_FPR = 0.01
ALPHA_HUMAN = TARGET_FPR   # share of human texts for which "human" may be ruled out
ALPHA_AI = 0.05            # share of AI texts for which "AI" may be ruled out
# Lower word limits of the length bands. "banded" follows docs/evaluation/plan.md §1 from the minimum up.
LAYERS = {"banded": (MIN_WORDS_FOR_VERDICT, 250, 500), "single_band": (MIN_WORDS_FOR_VERDICT,)}
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


def fit_layers(rows: list[dict]) -> dict:
    return {name: fit_conformal([r["ai_score"] for r in rows], [r["label"] for r in rows],
                                [r["n_words"] for r in rows], edges=edges,
                                alpha_human=ALPHA_HUMAN, alpha_ai=ALPHA_AI)
            for name, edges in LAYERS.items()}


def apply(calibrator, tau, layers: dict, row: dict) -> None:
    doc = calibrator.scored_document(row["ai_score"], row["n_words"])
    row["p_ai"], row["p_low"], row["p_high"] = doc.p_ai, doc.p_low, doc.p_high
    row["verdict_interval"] = Verdict.NO_VERDICT.name if tau is None else decide_verdict(doc, tau).name
    row["low_at_or_above_tau"] = tau is not None and doc.p_low >= tau
    for name, layer in layers.items():
        found = layer.assess(row["ai_score"], row["n_words"])
        # A text under the first band is under the minimum length and gets no verdict from any rule.
        row[f"verdict_{name}"] = (row["verdict_interval"] if found is None or tau is None
                                  else decide_verdict(doc, tau, found).name)
        row[f"own_class_ruled_out_{name}"] = None if found is None or "label" not in row else (
            not (found.ai_in_set if row["label"] else found.human_in_set))


def group_table(rows: list[dict], rule: str) -> list[dict]:
    by_group = defaultdict(list)
    for r in rows:
        by_group[r["group"]].append(r)
    table = []
    for group, items in by_group.items():
        long_enough = [r for r in items if r["n_words"] >= MIN_WORDS_FOR_VERDICT]
        verdicts = Counter(r[f"verdict_{rule}"] for r in long_enough)
        table.append({
            "group": group, "role": items[0]["role"], "n": len(items),
            "median_p_ai": float(np.median([r["p_ai"] for r in items])), "long_enough": len(long_enough),
            "likely_ai": verdicts[Verdict.LIKELY_AI.name], "likely_human": verdicts[Verdict.LIKELY_HUMAN.name],
            "cant_tell": verdicts[Verdict.CANT_TELL.name], "no_verdict": verdicts[Verdict.NO_VERDICT.name],
            "low_at_or_above_tau_any_length": sum(r["low_at_or_above_tau"] for r in items),
        })
    return table


def rate(k: int, n: int) -> dict:
    return {"k": k, "n": n, "ci95": list(clopper_pearson(k, n))}


def held_out_summary(rows: list[dict], rule: str) -> dict:
    """Error and label counts of one verdict rule on held out texts of the minimum length or more."""
    eligible = [r for r in rows if r["n_words"] >= MIN_WORDS_FOR_VERDICT]
    summary = {}
    for label, name, wrong in ((0, "human", Verdict.LIKELY_AI), (1, "ai", Verdict.LIKELY_HUMAN)):
        items = [r for r in eligible if r["label"] == label]
        verdicts = Counter(r[f"verdict_{rule}"] for r in items)
        summary[name] = {"wrong_label": rate(verdicts[wrong.name], len(items)),
                         "verdicts": {v.name: verdicts[v.name] for v in Verdict}}
        if rule != "interval":
            summary[name]["own_class_ruled_out"] = rate(
                sum(r[f"own_class_ruled_out_{rule}"] for r in items), len(items))
    return summary


def band_table(layer) -> list[dict]:
    need_human, need_ai = min_calibration_texts(layer.alpha_human), min_calibration_texts(layer.alpha_ai)
    return [{"min_words": edge, "max_words": layer.edges[i + 1] if i + 1 < len(layer.edges) else None,
             "n_human": len(layer.human_scores[i]), "n_ai": len(layer.ai_scores[i]),
             "can_label_ai": len(layer.human_scores[i]) >= need_human,
             "can_label_human": len(layer.ai_scores[i]) >= need_ai}
            for i, edge in enumerate(layer.edges)]


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

    def show(r: dict) -> str:
        if r["n"] == 0:
            return "0/0"
        return f"{r['k']}/{r['n']} ({r['ci95'][0] * 100:.1f}% to {r['ci95'][1] * 100:.1f}%)"

    def group_rows(table):
        return [f"| {t['group']} | {t['role']} | {t['n']} | {t['median_p_ai']:.3f} | {t['long_enough']} | "
                f"{t['likely_ai']} | {t['likely_human']} | {t['cant_tell']} | {t['no_verdict']} | "
                f"{t['low_at_or_above_tau_any_length']} |" for t in table]

    def band_name(b: dict) -> str:
        return f"{b['min_words']} or more" if b["max_words"] is None else f"{b['min_words']} to {b['max_words'] - 1}"

    group_header = [
        f"| Group | Role | n | Median P(AI) | Texts of {MIN_WORDS_FOR_VERDICT}+ words | Likely AI | Likely human | "
        "Can't tell | No verdict | Lower bound at or above tau, any length |", "|---|---|---|---|---|---|---|---|---|---|"]
    interval = cv["rules"]["interval"]
    lines = [
        "# Calibration pilot (calibration_pilot_v2)", "",
        f"Scorer: `{metrics['scorer']}`. Input: `{metrics['scores_file']}` (SHA 256 `{metrics['scores_sha256']}`).",
        f"Fitted on {metrics['n_human']} human and {metrics['n_ai']} AI texts, so P(AI) assumes that mix.",
        f"The interval is the {round(INTERVAL_LEVEL * 100)}% range. Seed `{metrics['seed']}`.", "",
        "This is a pilot on 2023 data from one source. It checks that the calibration and abstention layers work. "
        "It is not evidence about release quality.", "",
        f"## Calibration map, held out ({FOLDS} fold cross validation)", "",
        f"* ECE (15 equal mass bins): {cv['ece']:.4f}",
        f"* Brier score: {cv['brier']:.4f}",
        f"* Decision threshold tau per fold: {', '.join('none' if t is None else f'{t:.3f}' for t in cv['tau_per_fold'])}",
        "", "![Reliability diagram](reliability.svg)", "",
        "| Bin | n | Mean predicted P(AI) | Observed share of AI | 95% interval |", "|---|---|---|---|---|",
    ]
    lines += [f"| {i} | {b['n']} | {b['mean_predicted']:.3f} | {b['observed']:.3f} | "
              f"{b['ci95'][0]:.3f} to {b['ci95'][1]:.3f} |" for i, b in enumerate(cv["reliability_bins"], start=1)]

    lines += [
        "", "## Conformal abstention layer, held out", "",
        f"\"Human\" may be ruled out for at most {ALPHA_HUMAN * 100:g}% of human texts and \"AI\" for at most "
        f"{ALPHA_AI * 100:g}% of AI texts. A class can be ruled out only in a band with at least "
        f"{min_calibration_texts(ALPHA_HUMAN)} human or {min_calibration_texts(ALPHA_AI)} AI calibration texts. "
        f"All counts are for held out texts of {MIN_WORDS_FOR_VERDICT} words or more, with 95% Clopper Pearson "
        "intervals.", "",
        f"**Result under the reading fixed before the run: the banded layer "
        f"{'fails' if cv['layer_fails']['banded'] else 'does not fail'} and the single band layer "
        f"{'fails' if cv['layer_fails']['single_band'] else 'does not fail'}.**", "",
        "| Rule | Human texts labelled Likely AI | Human texts with \"human\" ruled out | AI texts labelled Likely human | "
        "AI texts with \"AI\" ruled out |", "|---|---|---|---|---|",
        f"| Interval rule alone | {show(interval['human']['wrong_label'])} | | {show(interval['ai']['wrong_label'])} | |",
    ]
    for name, title in (("banded", "With the banded layer"), ("single_band", "With the single band layer")):
        r = cv["rules"][name]
        lines.append(f"| {title} | {show(r['human']['wrong_label'])} | {show(r['human']['own_class_ruled_out'])} | "
                     f"{show(r['ai']['wrong_label'])} | {show(r['ai']['own_class_ruled_out'])} |")
    lines += ["", "| Rule | Class | Likely AI | Likely human | Can't tell | No verdict |", "|---|---|---|---|---|---|"]
    for name, title in (("interval", "Interval rule alone"), ("banded", "With the banded layer"),
                        ("single_band", "With the single band layer")):
        for cls in ("human", "ai"):
            v = cv["rules"][name][cls]["verdicts"]
            lines.append(f"| {title} | {cls} | {v['LIKELY_AI']} | {v['LIKELY_HUMAN']} | {v['CANT_TELL']} | "
                         f"{v['NO_VERDICT']} |")

    lines += ["", "## Bands of the final banded layer", "",
              "The final layer is fitted on all labelled texts and written to `calibration.json`. The single band "
              "layer is written to `calibration_single_band.json`.", "",
              "| Words | Human texts | AI texts | Can label as AI | Can label as human |", "|---|---|---|---|---|"]
    lines += [f"| {band_name(b)} | {b['n_human']} | {b['n_ai']} | {'yes' if b['can_label_ai'] else 'no'} | "
              f"{'yes' if b['can_label_human'] else 'no'} |" for b in final["bands"]]
    lines += ["", "## Verdicts per group, held out, with the banded layer", "",
              "Shorter texts receive no verdict and are not counted in the verdict columns. The last column counts "
              "texts whose lower bound reaches tau when length is ignored.", "",
              *group_header, *group_rows(cv["groups"]), "",
              "## AI edited human text, scored with the final calibrator and the final banded layer", "",
              f"The final calibrator is fitted on all labelled texts. Its tau is "
              f"{'none' if final['tau'] is None else format(final['tau'], '.3f')}.", "",
              *group_header, *group_rows(final["ai_edited_groups"]), ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scores", type=Path, default=Path("results/bias_v1/scores.jsonl"))
    parser.add_argument("--out", type=Path, default=Path("results/calibration_pilot_v2"))
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
        layers = fit_layers(train)
        for r in labelled:
            if r["fold"] == fold:
                apply(calibrator, tau, layers, r)

    p_ai, labels = [r["p_ai"] for r in labelled], [r["label"] for r in labelled]
    bins = reliability_bins(p_ai, labels)
    rules = {rule: held_out_summary(labelled, rule) for rule in ("interval", *LAYERS)}
    layer_fails = {name: (rules[name]["human"]["own_class_ruled_out"]["ci95"][0] > ALPHA_HUMAN
                          or rules[name]["ai"]["own_class_ruled_out"]["ci95"][0] > ALPHA_AI) for name in LAYERS}

    final = fit_calibrator([r["ai_score"] for r in labelled], labels, seed=SEED)
    final_tau = choose_tau(final, [r["ai_score"] for r in labelled if r["label"] == 0], TARGET_FPR)
    final_layers = fit_layers(labelled)
    edited = [dict(r) for r in rows if r["role"] == "ai_edited"]
    for r in edited:
        apply(final, final_tau, final_layers, r)

    metrics = {
        "scorer": args.scorer, "scores_file": args.scores.as_posix(),
        "scores_sha256": hashlib.sha256(args.scores.read_bytes()).hexdigest(),
        "seed": SEED, "target_fpr": TARGET_FPR, "alpha_human": ALPHA_HUMAN, "alpha_ai": ALPHA_AI,
        "layers": {name: list(edges) for name, edges in LAYERS.items()},
        "n_human": final.n_human, "n_ai": final.n_ai,
        "cross_validation": {
            "folds": FOLDS, "ece": expected_calibration_error(p_ai, labels), "brier": brier_score(p_ai, labels),
            "tau_per_fold": taus, "reliability_bins": bins, "rules": rules, "layer_fails": layer_fails,
            "groups": group_table(labelled, "banded"),
        },
        "final_calibrator": {"tau": final_tau, "bands": band_table(final_layers["banded"]),
                             "ai_edited_groups": group_table(edited, "banded")},
    }
    calibration = {
        "name": "calibration_pilot_v2", "scorer": args.scorer, "tau": final_tau, "target_fpr": TARGET_FPR,
        "description": "Pilot: Liang et al. 2023 student essays and CS224N abstracts, AI text from GPT 3 (2023). "
                       "Not validated for release.",
        "calibrator": final.to_dict(), "conformal": final_layers["banded"].to_dict(),
    }
    single_band = calibration | {"name": "calibration_pilot_v2_single_band",
                                 "conformal": final_layers["single_band"].to_dict()}

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "metrics.json").write_text(json.dumps(metrics, indent=1) + "\n")
    (args.out / "calibration.json").write_text(json.dumps(calibration) + "\n")
    (args.out / "calibration_single_band.json").write_text(json.dumps(single_band) + "\n")
    (args.out / "reliability.svg").write_text(reliability_svg(bins))
    (args.out / "report.md").write_text(render_report(metrics))
    print(f"wrote {args.out}/report.md, metrics.json, reliability.svg and two calibration files")


if __name__ == "__main__":
    main()
