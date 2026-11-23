"""Evaluation run of the frozen plan (docs/evaluation/plan.md at the tag eval_plan_v1).

The calibration map, the thresholds and the conformal layer are fitted on the calib split. Every
reported number is computed on the test split, with the definitions of plan §2 and the values of
eval/config/thresholds.yaml.

Choices fixed before the first run on test:

* Fitting uses the calib texts labelled human or AI. Left out of fitting and of the human error
  rates, and reported on their own: human texts whose source is in the scorer's training data
  (flag "source_in_scorer_training") and human texts that an AI edited.
* M1 and M3 apply a threshold on the raw score, chosen on the calib human texts for the target
  rate. A text is flagged when its score is above the threshold.
* A stratum is reported when it holds at least one text. Whether it supports a claim follows the
  sample size rules of the plan and is stated per stratum.
* M3 needs native and nonnative human texts on test. Without one of them the gate is reported as
  not evaluable, not as passed.
* M4 and the sentence level part of M2 are not computed: the corpora hold no attacked text and the
  command gives no sentence level probability.

Usage:
    python eval/run.py --rehearsal   # calib only: half of its groups stand in for test
    python eval/run.py               # the run on test, which refuses to start a second time
"""

import argparse
import datetime
import hashlib
import json
import random
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

from calibration_pilot import reliability_svg
from detechum.calibration import (brier_score, choose_tau, expected_calibration_error, fit_calibrator,
                                  reliability_bins)
from detechum.conformal import fit_conformal, min_calibration_texts
from detechum.models import GPTTRACE
from detechum.stats import clopper_pearson, threshold_for_fpr
from detechum.verdict import Verdict, decide_verdict

SEED = 20261119
PLAN_TAG = "eval_plan_v1"
SEEN = "source_in_scorer_training"


def load_thresholds(path: Path) -> dict:
    values = {}
    for line in path.read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            key, _, value = line.partition(":")
            values[key.strip()] = json.loads(value)
    return values


def load_rows(manifest: Path, scores: dict) -> list[dict]:
    rows = [json.loads(line) for line in manifest.read_text().splitlines()]
    missing = [r["sha256"] for r in rows if r["sha256"] not in scores]
    if missing:
        raise SystemExit(f"{len(missing)} texts of {manifest} have no score; run eval/score_corpora.py first")
    return [r | scores[r["sha256"]] for r in rows]


def rehearsal_split(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split calib by group into a fitting half and a half that stands in for test."""
    keys = sorted({r["group_key"] for r in rows})
    random.Random(f"{SEED}/rehearsal").shuffle(keys)
    held_out = set(keys[::2])
    return [r for r in rows if r["group_key"] not in held_out], [r for r in rows if r["group_key"] in held_out]


def rate(k: int, n: int) -> dict:
    if n == 0:
        return {"k": 0, "n": 0, "rate": None, "ci95": None}
    return {"k": k, "n": n, "rate": k / n, "ci95": list(clopper_pearson(k, n))}


def band_names(edges: list[int]) -> list[str]:
    names = [f"under {edges[0]}"]
    names += [f"{a} to {b - 1}" for a, b in zip(edges, edges[1:])]
    return names + [f"{edges[-1]} or more"]


def band_of(n_words: int, edges: list[int]) -> str:
    return band_names(edges)[int(np.searchsorted(edges, n_words, side="right"))]


def auroc(human_scores, ai_scores) -> float | None:
    if len(human_scores) == 0 or len(ai_scores) == 0:
        return None
    ranks = rankdata(np.concatenate([human_scores, ai_scores]))
    n_h, n_a = len(human_scores), len(ai_scores)
    return float((ranks[n_h:].sum() - n_a * (n_a + 1) / 2) / (n_h * n_a))


def strata(rows: list[dict], edges: list[int]) -> dict[str, dict[str, list[dict]]]:
    """Group rows by each stratum dimension of plan §1 that applies to their class."""
    out = defaultdict(lambda: defaultdict(list))
    for r in rows:
        out["length"][band_of(r["length_words"], edges)].append(r)
        out["domain"][r["domain"]].append(r)
        out["source"][r["source"]].append(r)
        if r["label"] == "human":
            out["writer_group"][r["author_group"]].append(r)
        else:
            out["generator"][r["generator"]].append(r)
    # Length bands follow their word counts; the other dimensions are alphabetical.
    order = {name: i for i, name in enumerate(band_names(edges))}
    return {dim: dict(sorted(groups.items(), key=lambda kv: (order.get(kv[0], 0), kv[0]) if dim == "length"
                             else (0, kv[0])))
            for dim, groups in out.items()}


def flag_rate(rows: list[dict], threshold: float) -> dict:
    return rate(sum(r["ai_score"] > threshold for r in rows), len(rows))


def verdict_table(rows: list[dict]) -> dict:
    """Verdict counts and the two wrong label rates for rows of one class mix."""
    out = {}
    for label, wrong in (("human", Verdict.LIKELY_AI), ("ai", Verdict.LIKELY_HUMAN)):
        items = [r for r in rows if r["label"] == label]
        counts = Counter(r["verdict"] for r in items)
        ruled_out = [r for r in items if r["own_class_ruled_out"] is not None]
        out[label] = {"n": len(items), "verdicts": {v.name: counts[v.name] for v in Verdict},
                      "wrong_label": rate(counts[wrong.name], len(items)),
                      "no_label": rate(counts[Verdict.CANT_TELL.name] + counts[Verdict.NO_VERDICT.name], len(items)),
                      "own_class_ruled_out": rate(sum(r["own_class_ruled_out"] for r in ruled_out), len(ruled_out))}
    return out


def evaluate(fit_rows: list[dict], eval_rows: list[dict], t: dict) -> tuple[dict, dict, list[dict]]:
    """Fit on `fit_rows`, measure on `eval_rows`. Returns (metrics, calibration file content, bins)."""
    edges = t["length_strata_edges_words"]
    target = t["m1_target_fpr"]

    def usable(rows):
        return [r for r in rows if r["label"] in ("human", "ai") and SEEN not in r["flags"]]

    fit, test = usable(fit_rows), usable(eval_rows)
    fit_scores = np.array([r["ai_score"] for r in fit])
    fit_labels = np.array([int(r["label"] == "ai") for r in fit])
    fit_human = fit_scores[fit_labels == 0]

    calibrator = fit_calibrator(fit_scores, fit_labels, seed=SEED, n_bootstrap=t["bootstrap_resamples"])
    tau = choose_tau(calibrator, fit_human, target)
    layer = fit_conformal(fit_scores, fit_labels, [r["length_words"] for r in fit],
                          edges=t["conformal_band_edges_words"], alpha_human=t["conformal_alpha_human"],
                          alpha_ai=t["conformal_alpha_ai"])
    score_thresholds = {str(fpr): threshold_for_fpr(fit_human, fpr) for fpr in (target, *t["secondary_target_fprs"])}
    threshold = score_thresholds[str(target)]

    for r in eval_rows:
        doc = calibrator.scored_document(r["ai_score"], r["length_words"])
        found = layer.assess(r["ai_score"], r["length_words"])
        r["p_ai"], r["p_low"], r["p_high"] = doc.p_ai, doc.p_low, doc.p_high
        r["flagged"] = bool(r["ai_score"] > threshold)
        r["verdict"] = (Verdict.NO_VERDICT if tau is None else decide_verdict(doc, tau, found)).name
        r["own_class_ruled_out"] = None if found is None or r["label"] not in ("human", "ai") else (
            not (found.ai_in_set if r["label"] == "ai" else found.human_in_set))

    human = [r for r in test if r["label"] == "human"]
    ai = [r for r in test if r["label"] == "ai"]
    human_strata, ai_strata = strata(human, edges), strata(ai, edges)
    min_claim = t["m1_min_human_texts_for_claim"]

    m1 = {
        "score_threshold": threshold, "target_fpr": target,
        "overall": {"tpr": flag_rate(ai, threshold), "realized_fpr": flag_rate(human, threshold),
                    "supports_claim": len(human) >= min_claim},
        "human_strata": {dim: {name: flag_rate(items, threshold) | {"supports_claim": len(items) >= min_claim}
                               for name, items in groups.items()}
                         for dim, groups in human_strata.items()},
        "ai_strata": {dim: {name: flag_rate(items, threshold) for name, items in groups.items()}
                      for dim, groups in ai_strata.items()},
    }
    secondary = {
        "auroc": auroc([r["ai_score"] for r in human], [r["ai_score"] for r in ai]),
        "at_other_target_fprs": {fpr: {"score_threshold": s, "tpr": flag_rate(ai, s), "realized_fpr": flag_rate(human, s)}
                                 for fpr, s in score_thresholds.items() if fpr != str(target)},
    }

    def calibration_of(rows):
        if not rows:
            return None
        p, y = [r["p_ai"] for r in rows], [int(r["label"] == "ai") for r in rows]
        return {"n": len(rows), "n_ai": sum(y), "ece": expected_calibration_error(p, y, t["m2_ece_bins"]),
                "brier": brier_score(p, y)}

    m2_overall = calibration_of(test)
    bins = reliability_bins([r["p_ai"] for r in test], [int(r["label"] == "ai") for r in test], t["m2_ece_bins"])
    m2_strata = {}
    for dim, groups in strata(test, edges).items():
        m2_strata[dim] = {}
        for name, items in groups.items():
            c = calibration_of(items)
            judged = c["n"] >= t["m2_min_texts_per_stratum"]
            m2_strata[dim][name] = c | {"target_applies": judged,
                                        "meets_target": c["ece"] <= t["m2_ece_max_per_stratum"] if judged else None}
    m2 = {"overall": m2_overall | {"meets_target": m2_overall["ece"] <= t["m2_ece_max_overall"]},
          "strata": m2_strata, "reliability_bins": bins,
          "sentence_level": "not computed: the command gives no sentence level probability"}

    nonnative = flag_rate(human_strata["writer_group"].get("nonnative", []), threshold)
    native = flag_rate(human_strata["writer_group"].get("native", []), threshold)
    # The ratio is undefined without native texts or with no flagged native text.
    ratio = nonnative["rate"] / native["rate"] if nonnative["n"] and native["k"] else None
    bound_ok = None if nonnative["n"] == 0 else nonnative["ci95"][1] <= t["m3_nonnative_fpr_upper_bound_max"]
    ratio_ok = None if ratio is None else ratio <= t["m3_nonnative_to_native_fpr_ratio_max"]
    # One failed condition fails the gate. Passing needs both, so a missing one leaves it open.
    gate = "failed" if False in (bound_ok, ratio_ok) else "passed" if bound_ok and ratio_ok else "not evaluable"
    m3 = {"nonnative_fpr": nonnative, "native_fpr": native, "ratio": ratio,
          "nonnative_upper_bound_ok": bound_ok, "ratio_ok": ratio_ok, "gate": gate}

    minimum = t["min_words_for_verdict"]
    long_enough = [r for r in test if r["length_words"] >= minimum]
    verdicts = {"all_lengths": verdict_table(test), "at_least_minimum_length": verdict_table(long_enough),
                "by_band": {name: verdict_table(items) for name, items in strata(long_enough, edges)["length"].items()}}

    need_human, need_ai = min_calibration_texts(layer.alpha_human), min_calibration_texts(layer.alpha_ai)
    bands = [{"band": band_of(layer.edges[i], edges),
              "n_human": len(layer.human_scores[i]), "n_ai": len(layer.ai_scores[i]),
              "can_label_ai": len(layer.human_scores[i]) >= need_human,
              "can_label_human": len(layer.ai_scores[i]) >= need_ai} for i in range(len(layer.edges))]

    seen_human = [r for r in eval_rows if r["label"] == "human" and SEEN in r["flags"]]
    edited = [r for r in eval_rows if r["label"] == "ai_edited"]

    def on_their_own(rows):
        counts = Counter(r["verdict"] for r in rows if r["length_words"] >= minimum)
        return {"n": len(rows), "flagged_at_m1_threshold": flag_rate(rows, threshold),
                "n_at_least_minimum_length": sum(counts.values()),
                "verdicts": {v.name: counts[v.name] for v in Verdict}}

    metrics = {
        "fit": {"n_human": calibrator.n_human, "n_ai": calibrator.n_ai, "tau": tau,
                "score_thresholds": score_thresholds, "bands": bands,
                "by_source": {f"{s}/{l}": n for (s, l), n in sorted(Counter((r["source"], r["label"]) for r in fit).items())}},
        "test_counts": {"human": len(human), "ai": len(ai),
                        "by_source": {f"{s}/{l}": n for (s, l), n in sorted(Counter((r["source"], r["label"]) for r in test).items())}},
        "m1": m1, "secondary": secondary, "m2": m2, "m3": m3,
        "m4": "not run: the corpora hold no attacked or paraphrased text",
        "verdicts": verdicts,
        "reported_on_their_own": {"human_with_source_in_scorer_training": on_their_own(seen_human),
                                  "ai_edited": on_their_own(edited)},
    }
    calibration = {
        "name": "calibration_eval_v1", "scorer": fit[0]["scorer"], "tau": tau, "target_fpr": target,
        "description": "Fitted on the calib split of eval_plan_v1: student essays by English learners, 2026 chat "
                       "model text in eight domains and the 2023 pilot texts. See results/eval_v1/report.md.",
        "calibrator": calibrator.to_dict(), "conformal": layer.to_dict(),
    }
    return metrics, calibration, bins


def git_commit() -> str:
    out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=Path(__file__).parent)
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], capture_output=True, text=True,
                           cwd=Path(__file__).parent).stdout.strip()
    return out.stdout.strip() + (" with uncommitted changes" if dirty else "")


def main():
    root = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--manifests", type=Path, default=root / "manifests")
    ap.add_argument("--scores", type=Path, default=root.parent / "results" / "eval_v1" / "scores.jsonl")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--rehearsal", action="store_true", help="use calib only; half of its groups stand in for test")
    args = ap.parse_args()
    out = args.out or root.parent / "results" / ("eval_v1_rehearsal" if args.rehearsal else "eval_v1")
    if not args.rehearsal and (out / "metrics.json").exists():
        raise SystemExit(f"{out}/metrics.json exists: the run on test was already made. A second run needs a new "
                         "results folder and a written reason in the plan.")

    thresholds = load_thresholds(root / "config" / "thresholds.yaml")
    scores = {}
    for line in args.scores.read_text().splitlines():
        row = json.loads(line)
        scores[row["sha256"]] = {k: row[k] for k in ("scorer", "ai_score", "truncated")}
    calib = load_rows(args.manifests / "calib.jsonl", scores)
    fit_rows, eval_rows = rehearsal_split(calib) if args.rehearsal else (calib, load_rows(args.manifests / "test.jsonl", scores))

    metrics, calibration, bins = evaluate(fit_rows, eval_rows, thresholds)
    metrics = {"plan_tag": PLAN_TAG, "mode": "rehearsal on calib" if args.rehearsal else "test",
               "scorer": calibration["scorer"], "model": GPTTRACE.record(), "seed": SEED, "thresholds": thresholds,
               "inputs": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in
                          (("calib_manifest", args.manifests / "calib.jsonl"),
                           ("test_manifest", args.manifests / "test.jsonl"), ("scores", args.scores))},
               **metrics}

    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=1) + "\n")
    (out / "reliability.svg").write_text(reliability_svg(bins))
    keep = ("sha256", "ai_score", "truncated", "p_ai", "p_low", "p_high", "flagged", "verdict")
    (out / "predictions.jsonl").write_text("".join(json.dumps({k: r[k] for k in keep}) + "\n" for r in eval_rows))
    if not args.rehearsal:
        (out / "calibration.json").write_text(json.dumps(calibration) + "\n")
        with (out / "run_log.jsonl").open("a") as fh:
            fh.write(json.dumps({"when": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                                 "commit": git_commit(), "mode": metrics["mode"]}) + "\n")
    print(f"wrote {out}/metrics.json")


if __name__ == "__main__":
    main()
