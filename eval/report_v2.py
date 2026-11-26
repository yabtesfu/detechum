"""Render results/<run>/report.md from the metrics.json written by eval/run_v2.py.

Every number is read from metrics.json. The statements about what the corpora can and cannot show are fixed
text, written before the run on test. The helpers come from eval/report.py, which stays as it was run for
eval_v1.

Usage: python eval/report_v2.py results/eval_v2
"""

import argparse
import json
from pathlib import Path

from report import pct, show, table, yes_no

PARTS = (("all_texts", "All texts", "reliability.svg"),
         ("student_essay", "Student essays only (`--kind student_essay`)", "reliability_student_essay.svg"))


def verdict_rows(name: str, block: dict) -> list[list]:
    out = []
    for cls in ("human", "ai"):
        c = block[cls]
        out.append([name, cls, c["n"], c["verdicts"]["LIKELY_AI"], c["verdicts"]["LIKELY_HUMAN"],
                    c["verdicts"]["CANT_TELL"], c["verdicts"]["NO_VERDICT"], show(c["wrong_label"]),
                    show(c["own_class_ruled_out"])])
    return out


def counts(c: dict) -> str:
    return (f"{c.get('LIKELY_AI', 0)} Likely AI, {c.get('LIKELY_HUMAN', 0)} Likely human, "
            f"{c.get('CANT_TELL', 0)} Can't tell, {c.get('NO_VERDICT', 0)} no verdict")


def render_part(x: dict, title: str, svg: str, t: dict) -> list[str]:
    m1, m2, m3, fit = x["m1"], x["m2"], x["m3"], x["fit"]
    lines = [f"## {title}", "",
             f"Fitted on {fit['n_human']} human and {fit['n_ai']} AI texts, so P(AI) assumes that mix. Measured on "
             f"{x['test_counts']['human']} human and {x['test_counts']['ai']} AI texts. Threshold of M1 "
             f"`{m1['score_threshold']:.3f}`, tau `{fit['tau']:.3f}`.", ""]
    sources = sorted(set(fit["by_source"]) | set(x["test_counts"]["by_source"]))
    lines += table(["Source and class", "Fitting", "Measuring"],
                   [[s, fit["by_source"].get(s, 0), x["test_counts"]["by_source"].get(s, 0)] for s in sources])

    lines += ["### M1: true positive rate at a 1% false positive rate", "",
              f"* **True positive rate:** {show(m1['overall']['tpr'])}",
              f"* **Realized false positive rate (nominal {pct(m1['target_fpr'])}):** "
              f"{show(m1['overall']['realized_fpr'])}", ""]
    for dim, name in (("source", "source"), ("writer_group", "writer group"), ("length", "length in words")):
        if dim in m1["human_strata"]:
            lines += [f"Human texts by {name}. A claim of 1% or lower needs {t['m1_min_human_texts_for_claim']} "
                      "texts.", ""]
            lines += table([name.capitalize(), "Flagged", "Enough texts for the claim"],
                           [[k, show(r), yes_no(r["supports_claim"])] for k, r in m1["human_strata"][dim].items()])
    for dim, name in (("source", "source"), ("generator", "generator"), ("length", "length in words")):
        if dim in m1["ai_strata"]:
            lines += [f"AI texts by {name}.", ""]
            lines += table([name.capitalize(), "Flagged"], [[k, show(r)] for k, r in m1["ai_strata"][dim].items()])
    for dim, name in (("generator_family", "generator family"), ("essay_kind", "kind of essay"), ("voice", "voice")):
        if dim in m1["new_ai_strata"]:
            lines += [f"AI texts by {name}. Verdicts count texts of {t['min_words_for_verdict']} words or more.", ""]
            lines += table([name.capitalize(), "Flagged", "Labelled Likely human"],
                           [[k, show(r["flagged"]), show(r["verdicts"]["wrong_label"])]
                            for k, r in m1["new_ai_strata"][dim].items()])

    o = m2["overall"]
    lines += ["### M2: calibration of P(AI)", "",
              f"* **ECE ({t['m2_ece_bins']} equal mass bins):** {o['ece']:.4f}. Target: at most "
              f"{t['m2_ece_max_overall']}. Met: {yes_no(o['meets_target'])}.",
              f"* **Brier score:** {o['brier']:.4f}", "", f"![Reliability diagram]({svg})", ""]

    ub = m3["upper_bounds_rule"]
    lines += ["### M3: nonnative release gate", "",
              f"* Nonnative human texts flagged at the M1 threshold: {show(m3['nonnative_fpr'])}",
              f"* Native human texts flagged at the M1 threshold: {show(m3['native_fpr'])}",
              f"* Upper bound of the nonnative rate at most {pct(t['m3_nonnative_fpr_upper_bound_max'])}: "
              f"{yes_no(m3['nonnative_upper_bound_ok'])}",
              f"* Rule of §2, ratio of the rates"
              f"{'' if m3['ratio'] is None else ' is ' + format(m3['ratio'], '.2f')}, at most "
              f"{t['m3_nonnative_to_native_fpr_ratio_max']}: {yes_no(m3['ratio_ok'])}. Gate: {m3['gate']}.",
              f"* Rule proposed in §10, upper bounds ({pct(ub['nonnative_upper'])} against {ub['limit']} times "
              f"{pct(ub['native_upper'])}): {yes_no(ub['upper_bounds_ok'])}. Gate: {ub['gate']}.",
              f"* **Gate under the rule adopted at the tag ({m3['rule_adopted']}): {m3['gate_adopted']}.**", ""]

    lines += ["### M4: attacked texts", "",
              "True positive rate at the M1 threshold, against the unattacked AI texts of the same source. The "
              "drop is in absolute points, with Newcombe's interval from the two Clopper Pearson intervals.", ""]
    lines += table(["Attack", "Unattacked", "Attacked", "Drop", "Verdicts, enough words"],
                   [[k, show(r["baseline_tpr"]), show(r["attacked_tpr"]),
                     "n/a" if r["difference"]["drop"] is None else
                     f"{pct(r['difference']['drop'])} ({pct(r['difference']['ci95'][0])} to "
                     f"{pct(r['difference']['ci95'][1])})", counts(r["verdicts_at_least_minimum_length"])]
                    for k, r in x["m4"].items()] or [["none in this split", "", "", "", ""]])

    v = x["verdicts"]
    lines += ["### Verdict rules and rates", ""]
    lines += table(["Length band of the conformal layer", "Human texts in fitting", "AI texts in fitting",
                    "Can label as AI", "Can label as human"],
                   [[b["band"], b["n_human"], b["n_ai"], yes_no(b["can_label_ai"]), yes_no(b["can_label_human"])]
                    for b in fit["bands"]])
    rows = verdict_rows("all lengths", v["all_lengths"]) + verdict_rows(
        f"{t['min_words_for_verdict']} words or more", v["at_least_minimum_length"])
    for name in sorted(v["by_band"], key=lambda n: int(n.split()[0])):
        rows += verdict_rows(name, v["by_band"][name])
    lines += table(["Texts", "Class", "n", "Likely AI", "Likely human", "Can't tell", "No verdict",
                    "Wrong label", "Own class ruled out"], rows)

    lines += ["### Human texts that an AI edited", ""]
    edited = x["reported_on_their_own"]["ai_edited_by_source"]
    lines += [f"* **{k}:** flagged at the M1 threshold {show(r['flagged_at_m1_threshold'])}. Verdicts with enough "
              f"words: {counts(r['verdicts_at_least_minimum_length'])}." for k, r in edited.items()] or ["* none"]
    return lines + [""]


def render(m: dict) -> str:
    t = m["thresholds"]
    rehearsal = m["mode"] != "test"
    lines = [f"# Evaluation run of eval_plan_v2 {'(rehearsal on calib)' if rehearsal else 'on the test split'}", "",
             f"Plan: `{m['plan_tag']}`. Scorer: `{m['scorer']}` ({m['model']['repo']} at revision "
             f"`{m['model']['revision'][:12]}`). Seed `{m['seed']}`. Intervals are 95% Clopper Pearson.", ""]
    if rehearsal:
        lines += ["**This is a rehearsal.** Half of the groups of the calib split stand in for test. It checks the "
                  "harness and is not a result.", ""]
    lines += [
        "What these corpora can and cannot show:", "",
        "* **The texts of eval_v1 have been seen.** Their results were published, so the claims of this run rest on "
        "the texts added for eval_plan_v2.",
        "* **The 300 Claude essays are in fitting only.** They were scored before the plan was frozen.",
        "* **Attacked texts are DIPPER paraphrases and AI rewrites of AI essays, from GEDE.** Commercial humanizers "
        "and light human edits are not covered.",
        "* **Native human essays come from BAWE (GEDE):** students at UK universities whose first language is "
        "English. Nonnative essays are mostly those of ELLIPSE, written in US schools. The two groups also differ in "
        "age and level, so a gap between them is not due to the first language alone.",
        "* **The writers of the Ghostbuster human essays are unknown.** They come from IvyPanda and are counted in "
        "neither writer group.",
        "* **Generators fine tuned on student essays are few:** one model of DACTYL. The rate on them rests on few "
        "texts.", ""]
    for key, title, svg in PARTS:
        lines += render_part(m[key], title, svg, t)
    lines += ["## Inputs", ""] + [f"* {name}: SHA 256 `{digest}`" for name, digest in m["inputs"].items()] + [""]
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
