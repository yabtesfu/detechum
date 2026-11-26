"""Evaluation run of eval_plan_v2 (docs/evaluation/plan.md §10).

Uses the functions of eval/run.py unchanged, so that the definitions of eval_v1 carry over, and adds what
§10 asks for:

* Two fits on calib: one on all texts, one on student essays only (the "student_essay" entry of the
  calibration file, used by `detechum score --kind student_essay`). Each is measured on the matching
  texts of test.
* M4: texts flagged "attacked" are left out of fitting and of M1, and their true positive rate at the M1
  threshold is compared with that of the unattacked AI texts of the same source.
* New strata of AI texts: generator family, kind of essay and voice.
* M3 under the rule of §2 and under the rule proposed in §10, which compares upper bounds. Only the rule
  adopted at the tag decides the gate; the other is shown for comparison.
* Human texts that an AI edited, per source and way of editing.

Choices fixed before the first run on test, in addition to those of eval/run.py:

* Attacked texts are never used for fitting, so that M4 measures a calibration that has not seen the
  attack.
* The student essay fit uses the calib texts of the domain "student_essay" and nothing else.
* The bootstrap and rehearsal seed is that of eval/run.py.

Usage:
    python eval/run_v2.py --rehearsal   # calib only: half of its groups stand in for test
    python eval/run_v2.py               # the run on test: needs the tag eval_plan_v2, refuses a second run
"""

import argparse
import datetime
import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from calibration_pilot import reliability_svg
from detechum.models import GPTTRACE
from run import SEED, SEEN, evaluate, flag_rate, git_commit, load_rows, load_thresholds, rehearsal_split, verdict_table

PLAN_TAG = "eval_plan_v2"
KIND = "student_essay"
ATTACKED = "ai_attacked"  # label given to attacked AI texts, so that evaluate() leaves them out of fitting and M1
# M3 rule adopted at the tag: "section_2" (ratio of the rates) or "upper_bounds" (proposed in §10).
M3_RULE = "section_2"
GENERATED = {"claude_essays", "qwen_essays"}  # essays written from eval/essay_tasks.py; variant is "kind/voice"
FAMILIES = (("claude", "claude"), ("chatgpt", "gpt"), ("gpt", "gpt"), ("gemini", "gemini"), ("llama", "llama"),
            ("qwen", "qwen"), ("mistral", "mistral"), ("deepseek", "deepseek"))


def family(generator: str) -> str:
    g = generator.lower()
    return next((name for key, name in FAMILIES if key in g), "other")


def kind_and_voice(r: dict) -> tuple[str | None, str | None]:
    if r["source"] in GENERATED:
        kind, voice = r["variant"].split("/")
        return kind, voice
    if r["source"] == "dactyl":
        return None, r["variant"]
    return None, None


def usable(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r["label"] in ("human", "ai") and SEEN not in r["flags"]]


def long_enough(rows: list[dict], t: dict) -> list[dict]:
    return [r for r in rows if r["length_words"] >= t["min_words_for_verdict"]]


def new_ai_strata(eval_rows: list[dict], threshold: float, t: dict) -> dict:
    """Flag rate at the M1 threshold and verdicts of the AI texts by family, kind of essay and voice."""
    groups = defaultdict(lambda: defaultdict(list))
    for r in usable(eval_rows):
        if r["label"] != "ai":
            continue
        groups["generator_family"][family(r["generator"])].append(r)
        kind, voice = kind_and_voice(r)
        if kind:
            groups["essay_kind"][kind].append(r)
        if voice:
            groups["voice"][voice].append(r)
    return {dim: {name: {"flagged": flag_rate(items, threshold),
                         "verdicts": verdict_table(long_enough(items, t))["ai"]}
                  for name, items in sorted(by_name.items())}
            for dim, by_name in groups.items()}


def m3_upper_bounds(m3: dict, t: dict) -> dict:
    """The rule proposed in §10: the upper bound of the nonnative rate is at most the ratio limit times the
    upper bound of the native rate, next to the bound on the nonnative rate of §2."""
    nonnative, native = m3["nonnative_fpr"], m3["native_fpr"]
    limit = t["m3_nonnative_to_native_fpr_ratio_max"]
    ok = None if not (nonnative["n"] and native["n"]) else nonnative["ci95"][1] <= limit * native["ci95"][1]
    bound_ok = m3["nonnative_upper_bound_ok"]
    gate = "failed" if False in (bound_ok, ok) else "passed" if bound_ok and ok else "not evaluable"
    return {"nonnative_upper": nonnative["ci95"] and nonnative["ci95"][1],
            "native_upper": native["ci95"] and native["ci95"][1], "limit": limit, "upper_bounds_ok": ok,
            "gate": gate}


def difference(base: dict, attacked: dict) -> dict:
    """Drop from `base` to `attacked` in absolute points, with Newcombe's square and add interval built
    from the two Clopper Pearson intervals."""
    if not (base["n"] and attacked["n"]):
        return {"drop": None, "ci95": None}
    d = base["rate"] - attacked["rate"]
    (bl, bu), (al, au) = base["ci95"], attacked["ci95"]
    low = d - math.hypot(base["rate"] - bl, au - attacked["rate"])
    high = d + math.hypot(bu - base["rate"], attacked["rate"] - al)
    return {"drop": d, "ci95": [low, high]}


def m4(eval_rows: list[dict], threshold: float, t: dict) -> dict:
    """True positive rate at the M1 threshold per attack, against the unattacked AI texts of its source."""
    attacked = defaultdict(list)
    for r in eval_rows:
        if r["label"] == ATTACKED:
            attacked[(r["source"], r.get("variant") or r["generator"])].append(r)
    out = {}
    for (source, attack), rows in sorted(attacked.items()):
        base_rows = [r for r in usable(eval_rows) if r["label"] == "ai" and r["source"] == source]
        base, hit = flag_rate(base_rows, threshold), flag_rate(rows, threshold)
        counts = Counter(r["verdict"] for r in long_enough(rows, t))
        out[f"{source}/{attack}"] = {"baseline_tpr": base, "attacked_tpr": hit, "difference": difference(base, hit),
                                     "verdicts_at_least_minimum_length": dict(counts)}
    return out


def ai_edited(eval_rows: list[dict], threshold: float, t: dict) -> dict:
    groups = defaultdict(list)
    for r in eval_rows:
        if r["label"] == "ai_edited":
            groups[f"{r['source']}/{r.get('variant') or r['generator']}"].append(r)
    return {name: {"flagged_at_m1_threshold": flag_rate(rows, threshold),
                   "verdicts_at_least_minimum_length": dict(Counter(r["verdict"] for r in long_enough(rows, t)))}
            for name, rows in sorted(groups.items())}


def run(fit_rows: list[dict], eval_rows: list[dict], t: dict) -> tuple[dict, dict, list]:
    """evaluate() of eval/run.py plus the additions of §10, on the rows given."""
    metrics, calibration, bins = evaluate(fit_rows, eval_rows, t)
    threshold = metrics["m1"]["score_threshold"]
    metrics["m1"]["new_ai_strata"] = new_ai_strata(eval_rows, threshold, t)
    metrics["m3"]["upper_bounds_rule"] = m3_upper_bounds(metrics["m3"], t)
    metrics["m3"]["rule_adopted"] = M3_RULE
    metrics["m3"]["gate_adopted"] = (metrics["m3"]["gate"] if M3_RULE == "section_2"
                                     else metrics["m3"]["upper_bounds_rule"]["gate"])
    metrics["m4"] = m4(eval_rows, threshold, t)
    metrics["reported_on_their_own"]["ai_edited_by_source"] = ai_edited(eval_rows, threshold, t)
    return metrics, calibration, bins


def tag_exists(tag: str) -> bool:
    out = subprocess.run(["git", "tag", "-l", tag], capture_output=True, text=True, cwd=Path(__file__).parent)
    return out.stdout.strip() == tag


def main():
    root = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--manifests", type=Path, default=root / "manifests_v2")
    ap.add_argument("--scores", type=Path, default=root.parent / "results" / "eval_v2" / "scores.jsonl")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--rehearsal", action="store_true", help="use calib only; half of its groups stand in for test")
    args = ap.parse_args()
    out = args.out or root.parent / "results" / ("eval_v2_rehearsal" if args.rehearsal else "eval_v2")
    if not args.rehearsal:
        if (out / "metrics.json").exists():
            raise SystemExit(f"{out}/metrics.json exists: the run on test was already made. A second run needs a "
                             "new results folder and a written reason in the plan.")
        if not tag_exists(PLAN_TAG):
            raise SystemExit(f"the tag {PLAN_TAG} does not exist: freeze the plan before the run on test")

    t = load_thresholds(root / "config" / "thresholds.yaml")
    scores = {}
    for line in args.scores.read_text().splitlines():
        row = json.loads(line)
        scores[row["sha256"]] = {k: row[k] for k in ("scorer", "ai_score", "truncated")}
    calib = load_rows(args.manifests / "calib.jsonl", scores)
    fit_rows, eval_rows = (rehearsal_split(calib) if args.rehearsal
                           else (calib, load_rows(args.manifests / "test.jsonl", scores)))
    for r in fit_rows + eval_rows:
        if "attacked" in r["flags"]:
            r["label"] = ATTACKED

    all_metrics, calibration, bins = run(fit_rows, eval_rows, t)
    kind_eval = [dict(r) for r in eval_rows if r["domain"] == KIND]
    kind_metrics, kind_calibration, kind_bins = run([r for r in fit_rows if r["domain"] == KIND], kind_eval, t)

    name = "calibration_eval_v2" + ("_rehearsal" if args.rehearsal else "")
    calibration |= {"name": name, "description": (
        "Fitted on the calib split of eval_plan_v2: the texts of eval_v1, AI written student essays of current "
        "models and the human essays of GEDE and Ghostbuster. See results/eval_v2/report.md.")}
    kind_calibration = {k: v for k, v in kind_calibration.items() if k != "scorer"} | {
        "name": f"{name}/{KIND}", "description": (
            "Fitted only on the student essays of the calib split of eval_plan_v2. Use it only for texts that are "
            "student essays; the tool does not check this.")}
    calibration["kinds"] = {KIND: kind_calibration}

    metrics = {"plan_tag": PLAN_TAG, "mode": "rehearsal on calib" if args.rehearsal else "test",
               "scorer": calibration["scorer"], "model": GPTTRACE.record(), "seed": SEED, "thresholds": t,
               "inputs": {label: hashlib.sha256(path.read_bytes()).hexdigest() for label, path in
                          (("calib_manifest", args.manifests / "calib.jsonl"),
                           ("test_manifest", args.manifests / "test.jsonl"), ("scores", args.scores))},
               "all_texts": all_metrics, KIND: kind_metrics}

    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=1) + "\n")
    (out / "reliability.svg").write_text(reliability_svg(bins))
    (out / f"reliability_{KIND}.svg").write_text(reliability_svg(kind_bins))
    keep = ("sha256", "ai_score", "truncated", "p_ai", "p_low", "p_high", "flagged", "verdict")
    (out / "predictions.jsonl").write_text("".join(json.dumps({k: r[k] for k in keep}) + "\n" for r in eval_rows))
    (out / f"predictions_{KIND}.jsonl").write_text(
        "".join(json.dumps({k: r[k] for k in keep}) + "\n" for r in kind_eval))
    (out / "calibration.json").write_text(json.dumps(calibration) + "\n")
    if not args.rehearsal:
        with (out / "run_log.jsonl").open("a") as fh:
            fh.write(json.dumps({"when": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                                 "commit": git_commit(), "mode": metrics["mode"]}) + "\n")
    print(f"wrote {out}/metrics.json")


if __name__ == "__main__":
    main()
