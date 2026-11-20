"""Render results/<run>/report.md from the metrics.json written by eval/run.py.

Every number in the report is read from metrics.json. The statements about what the corpora can
and cannot show are fixed text: they follow from the manifests and were written before the run on
test.

Usage: python eval/report.py results/eval_v1
"""

import argparse
import json
from pathlib import Path


def pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x * 100:.1f}%"


def show(r: dict) -> str:
    if r["n"] == 0:
        return "no texts"
    return f"{r['k']}/{r['n']} = {pct(r['rate'])} ({pct(r['ci95'][0])} to {pct(r['ci95'][1])})"


def table(header: list[str], rows: list[list]) -> list[str]:
    return ["| " + " | ".join(header) + " |", "|" + "---|" * len(header),
            *("| " + " | ".join(str(c) for c in row) + " |" for row in rows), ""]


def yes_no(value) -> str:
    return "n/a" if value is None else "yes" if value else "no"


def render(m: dict) -> str:
    t, m1, m2, m3, fit = m["thresholds"], m["m1"], m["m2"], m["m3"], m["fit"]
    rehearsal = m["mode"] != "test"
    lines = [
        f"# Evaluation run {'(rehearsal on calib)' if rehearsal else 'on the test split'}", "",
        f"Plan: `{m['plan_tag']}`. Scorer: `{m['scorer']}` ({m['model']['repo']} at revision "
        f"`{m['model']['revision'][:12]}`). Seed `{m['seed']}`. Intervals are 95% Clopper Pearson.", "",
    ]
    if rehearsal:
        lines += ["**This is a rehearsal.** Half of the groups of the calib split stand in for test. It checks the "
                  "harness and is not a result.", ""]

    lines += ["## What this run covers", ""]
    lines += table(["Part of the plan", "Status"], [
        ["M1, true positive rate at 1% false positive rate", "computed"],
        ["M2, calibration of the document probability", "computed"],
        ["M2, calibration of a sentence probability", "not computed: the command gives no sentence probability"],
        ["M3, nonnative release gate", m3["gate"]],
        ["M4, paraphrase and humanizer attacks", "not run: the corpora hold no attacked text"],
        ["Verdict rules and rates", "computed"],
        ["Revision mode metrics (§3)", "not run: revision mode does not exist"],
        ["RAID submission (§5)", "not run"],
    ])

    lines += ["## Data", "",
              f"Fitted on {fit['n_human']} human and {fit['n_ai']} AI texts, so P(AI) assumes that mix. Measured on "
              f"{m['test_counts']['human']} human and {m['test_counts']['ai']} AI texts.", ""]
    sources = sorted(set(fit["by_source"]) | set(m["test_counts"]["by_source"]))
    lines += table(["Source and class", "Fitting", "Measuring"],
                   [[s, fit["by_source"].get(s, 0), m["test_counts"]["by_source"].get(s, 0)] for s in sources])
    lines += [
        "What these corpora can and cannot show:", "",
        "* **The human and the AI texts are of different kinds.** Most human texts are school essays by English "
        "learners (ELLIPSE). Most AI texts are answers of 2026 chat models in eight other domains (MELD-eval). The "
        "false positive rate on essays and the true positive rate on chat model text are each valid for their kind "
        "of text. Any number that mixes the classes (AUROC, ECE, P(AI)) also reflects the difference in kind, which "
        "makes the classes easier to separate than authorship alone would.",
        ("* **The native human texts are pilot essays.** On test there are none, because the pilots may be used "
         "for fitting only. This rehearsal draws on calib, so here the ratio of M3 rests on those few essays."
         if rehearsal else
         "* **There is no native human text on test.** The only native essays are those of the pilots, which may "
         "be used for fitting only. The ratio of M3 cannot be computed."),
        "* **Nonnative means two things here:** school essays by English learners in the United States, and "
        "passages of research papers whose authors work in countries where English is not the main language. The "
        "second is the label of the TextSight benchmark and is an inference from the affiliation.",
        "* **No AI text is a student essay** except the 2023 GPT 3 essays of the pilots, which are in fitting only.",
        "* **The scorer's author reports results on MELD-eval and on the TextSight benchmark.** Neither is listed as "
        "training data, but both may have guided the choice of the released model.",
        "* **Human texts taken from RAID are left out of every rate above the last section.** The scorer was trained "
        "on RAID, so its scores on them say nothing about unseen human text.", ""]

    lines += ["## M1: true positive rate at a 1% false positive rate", "",
              f"The threshold `{m1['score_threshold']:.3f}` on the raw score flags {pct(m1['target_fpr'])} of the human "
              "texts used for fitting. It is applied unchanged below.", "",
              f"* **True positive rate:** {show(m1['overall']['tpr'])}",
              f"* **Realized false positive rate (nominal {pct(m1['target_fpr'])}):** "
              f"{show(m1['overall']['realized_fpr'])}", ""]
    for dim, title in (("writer_group", "writer group"), ("length", "length in words"), ("domain", "domain"),
                       ("source", "source")):
        if dim in m1["human_strata"]:
            lines += [f"Human texts by {title}. A stratum supports a claim of 1% or lower only with at least "
                      f"{t['m1_min_human_texts_for_claim']} texts.", ""]
            lines += table([title.capitalize(), "Flagged", "Enough texts for the claim"],
                           [[name, show(r), yes_no(r["supports_claim"])] for name, r in m1["human_strata"][dim].items()])
    for dim, title in (("generator", "generator"), ("length", "length in words"), ("domain", "domain")):
        if dim in m1["ai_strata"]:
            lines += [f"AI texts by {title}.", ""]
            lines += table([title.capitalize(), "Flagged"], [[name, show(r)] for name, r in m1["ai_strata"][dim].items()])

    sec = m["secondary"]
    lines += ["## Secondary metrics", "", f"* AUROC: {'n/a' if sec['auroc'] is None else format(sec['auroc'], '.4f')}"]
    for fpr, r in sec["at_other_target_fprs"].items():
        lines.append(f"* At a nominal false positive rate of {pct(float(fpr))} (threshold `{r['score_threshold']:.3f}`): "
                     f"true positive rate {show(r['tpr'])}, realized false positive rate {show(r['realized_fpr'])}")
    lines += ["* Latency: not measured.", ""]

    o = m2["overall"]
    lines += ["## M2: calibration of P(AI)", "",
              f"* **ECE ({t['m2_ece_bins']} equal mass bins):** {o['ece']:.4f}. Target: at most "
              f"{t['m2_ece_max_overall']}. Met: {yes_no(o['meets_target'])}.",
              f"* **Brier score:** {o['brier']:.4f}", "", "![Reliability diagram](reliability.svg)", ""]
    lines += table(["Bin", "n", "Mean predicted P(AI)", "Observed share of AI", "95% interval"],
                   [[i, b["n"], f"{b['mean_predicted']:.3f}", f"{b['observed']:.3f}",
                     f"{b['ci95'][0]:.3f} to {b['ci95'][1]:.3f}"] for i, b in enumerate(m2["reliability_bins"], start=1)])
    lines += [f"Per stratum. The target of {t['m2_ece_max_per_stratum']} applies to strata with at least "
              f"{t['m2_min_texts_per_stratum']} texts. A stratum with one class only measures how close P(AI) is to "
              "0 or 1 for that class.", ""]
    rows = [[dim, name, c["n"], c["n_ai"], f"{c['ece']:.4f}", f"{c['brier']:.4f}", yes_no(c["meets_target"])]
            for dim, groups in m2["strata"].items() for name, c in groups.items()]
    lines += table(["Dimension", "Stratum", "n", "AI texts", "ECE", "Brier", "Meets target"], rows)

    lines += ["## M3: nonnative release gate", "",
              f"* Nonnative human texts flagged at the M1 threshold: {show(m3['nonnative_fpr'])}",
              f"* Native human texts flagged at the M1 threshold: {show(m3['native_fpr'])}",
              f"* Upper bound of the nonnative rate at most {pct(t['m3_nonnative_fpr_upper_bound_max'])}: "
              f"{yes_no(m3['nonnative_upper_bound_ok'])}",
              f"* Ratio of the nonnative to the native rate"
              f"{'' if m3['ratio'] is None else ' is ' + format(m3['ratio'], '.2f')}, at most "
              f"{t['m3_nonnative_to_native_fpr_ratio_max']}: {yes_no(m3['ratio_ok'])}",
              f"* **Gate: {m3['gate']}.**", ""]

    v = m["verdicts"]
    lines += ["## Verdict rules and rates", "",
              f"A label needs {t['min_words_for_verdict']} words, the whole {pct(t['probability_interval_level'])} "
              f"interval on one side of tau (`{fit['tau']:.3f}`), and a conformal prediction set that holds that "
              "class alone.", ""]
    lines += table(["Length band of the conformal layer", "Human texts in fitting", "AI texts in fitting",
                    "Can label as AI", "Can label as human"],
                   [[b["band"], b["n_human"], b["n_ai"], yes_no(b["can_label_ai"]), yes_no(b["can_label_human"])]
                    for b in fit["bands"]])

    def verdict_rows(name, block):
        out = []
        for cls in ("human", "ai"):
            c = block[cls]
            out.append([name, cls, c["n"], c["verdicts"]["LIKELY_AI"], c["verdicts"]["LIKELY_HUMAN"],
                        c["verdicts"]["CANT_TELL"], c["verdicts"]["NO_VERDICT"], show(c["wrong_label"]),
                        show(c["own_class_ruled_out"])])
        return out

    rows = verdict_rows("all lengths", v["all_lengths"]) + verdict_rows(
        f"{t['min_words_for_verdict']} words or more", v["at_least_minimum_length"])
    for name in sorted(v["by_band"], key=lambda n: int(n.split()[0])):
        rows += verdict_rows(name, v["by_band"][name])
    lines += table(["Texts", "Class", "n", "Likely AI", "Likely human", "Can't tell", "No verdict",
                    "Wrong label", "Own class ruled out"], rows)
    lines += [f"The wrong label for a human text is \"Likely AI written or AI edited\", the false accusation. For "
              f"an AI text it is \"Likely human written\". The targets for ruling out the own class are "
              f"{pct(t['conformal_alpha_human'])} for human and {pct(t['conformal_alpha_ai'])} for AI texts.", ""]

    lines += ["## Reported on their own", ""]
    for key, title in (("human_with_source_in_scorer_training", "Human texts taken from RAID, on which the scorer "
                        "was trained"), ("ai_edited", "Human texts that an AI edited")):
        r = m["reported_on_their_own"][key]
        if r["n"] == 0:
            lines.append(f"* **{title}:** none in this split.")
            continue
        c = r["verdicts"]
        lines.append(f"* **{title}:** flagged at the M1 threshold {show(r['flagged_at_m1_threshold'])}. Of the "
                     f"{r['n_at_least_minimum_length']} with enough words: {c['LIKELY_AI']} Likely AI, "
                     f"{c['LIKELY_HUMAN']} Likely human, {c['CANT_TELL']} Can't tell, {c['NO_VERDICT']} no verdict.")
    lines += ["", "## Inputs", ""] + [f"* {name}: SHA 256 `{digest}`" for name, digest in m["inputs"].items()] + [""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run", type=Path, help="folder that holds metrics.json")
    args = ap.parse_args()
    metrics = json.loads((args.run / "metrics.json").read_text())
    (args.run / "report.md").write_text(render(metrics))
    print(f"wrote {args.run}/report.md")


if __name__ == "__main__":
    main()
