"""Test of a second signal on calib, by the rule written in plan §10 before its scores were seen.

Uses the rehearsal halves of eval/run.py: everything is fitted on one half of the calib groups and
measured on the other, on student essays only. For GPTTrace alone, Desklib alone and their combination
(a logistic regression on the two raw scores), it reports the flag rate at the threshold that flags 1% of
the human essays of the fitting half, per source, writer group and generator family, and checks the
conditions of the rule.

It also writes scores_combined.jsonl: the combined score of every calib text, from the regression fitted
on the fitting half, so that `run_v2.py --rehearsal --scores` can check the last condition. Test texts are
neither read nor scored.

Usage: cd eval && python second_signal.py
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from detechum.stats import threshold_for_fpr
from run import SEEN, auroc, load_thresholds, rate, rehearsal_split
from run_v2 import KIND, family

COMBINED = "gpttrace+desklib_logistic_rehearsal"


def logistic_fit(x: np.ndarray, y: np.ndarray, ridge: float = 1e-6, steps: int = 50) -> dict:
    """Logistic regression by Newton's method on standardized features. Returns what `logistic_score` needs."""
    mean, sd = x.mean(axis=0), x.std(axis=0)
    z = np.column_stack([np.ones(len(x)), (x - mean) / sd])
    w = np.zeros(z.shape[1])
    for _ in range(steps):
        p = 1 / (1 + np.exp(-z @ w))
        grad = z.T @ (p - y) + ridge * w
        hess = (z * (p * (1 - p))[:, None]).T @ z + ridge * np.eye(len(w))
        step = np.linalg.solve(hess, grad)
        w -= step
        if np.abs(step).max() < 1e-10:
            break
    return {"mean": mean.tolist(), "sd": sd.tolist(), "weights": w.tolist()}


def logistic_score(model: dict, x: np.ndarray) -> np.ndarray:
    """The log odds of the regression, used as a raw score."""
    z = (x - np.array(model["mean"])) / np.array(model["sd"])
    return model["weights"][0] + z @ np.array(model["weights"][1:])


def measure(fit: list[dict], held: list[dict], key: str) -> dict:
    threshold = threshold_for_fpr(np.array([r[key] for r in fit if r["label"] == "human"]), 0.01)

    def flags(rows):
        return rate(sum(r[key] > threshold for r in rows), len(rows))

    human = [r for r in held if r["label"] == "human"]
    ai = [r for r in held if r["label"] == "ai" and "attacked" not in r["flags"]]
    groups = defaultdict(lambda: defaultdict(list))
    for r in human:
        groups["human_source"][r["source"]].append(r)
        groups["writer_group"][r["author_group"]].append(r)
    for r in ai:
        groups["ai_family"][family(r["generator"])].append(r)
        groups["ai_source"][r["source"]].append(r)
    attacked = [r for r in held if "attacked" in r["flags"]]
    return {"threshold": threshold, "tpr": flags(ai), "fpr": flags(human), "attacked_tpr": flags(attacked),
            "auroc": auroc([r[key] for r in human], [r[key] for r in ai]),
            **{dim: {name: flags(rows) for name, rows in sorted(by.items())} for dim, by in groups.items()}}


def main():
    root = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--manifest", type=Path, default=root / "manifests_v2" / "calib.jsonl")
    ap.add_argument("--results", type=Path, default=root.parent / "results" / "eval_v2")
    ap.add_argument("--out", type=Path, default=root.parent / "results" / "second_signal_v1")
    args = ap.parse_args()
    t = load_thresholds(root / "config" / "thresholds.yaml")

    def scores(name):
        return {r["sha256"]: r for r in map(json.loads, (args.results / name).read_text().splitlines())}

    gpttrace, desklib = scores("scores.jsonl"), scores("scores_desklib.jsonl")
    rows = [json.loads(line) for line in args.manifest.read_text().splitlines()]
    missing = sum(r["sha256"] not in desklib for r in rows)
    if missing:
        raise SystemExit(f"{missing} calib texts have no Desklib score; run score_corpora.py --scorer desklib")
    for r in rows:
        r["gpttrace"], r["desklib"] = gpttrace[r["sha256"]]["ai_score"], desklib[r["sha256"]]["ai_score"]
    fit_all, held_all = rehearsal_split(rows)

    def essays(part, attacked=False):
        return [r for r in part if r["domain"] == KIND and SEEN not in r["flags"] and r["label"] in ("human", "ai")
                and ("attacked" in r["flags"]) == attacked]

    fit, held = essays(fit_all), essays(held_all)
    model = logistic_fit(np.array([[r["gpttrace"], r["desklib"]] for r in fit]),
                         np.array([int(r["label"] == "ai") for r in fit], dtype=float))
    for r in rows:
        r["combined"] = float(logistic_score(model, np.array([r["gpttrace"], r["desklib"]])))

    held_with_attacks = held + essays(held_all, attacked=True)
    results = {key: measure(fit, held_with_attacks, key) for key in ("gpttrace", "desklib", "combined")}
    bound = t["m3_nonnative_fpr_upper_bound_max"]

    def nonnative_ok(key):
        nn = results[key]["writer_group"].get("nonnative")
        return None if not nn or not nn["n"] else nn["ci95"][1] <= bound

    g, c = results["gpttrace"], results["combined"]
    rule = {
        "desklib_ruled_out": nonnative_ok("desklib") is False,
        "combined_tpr_higher": c["tpr"]["rate"] > g["tpr"]["rate"],
        "combined_nonnative_upper_bound_ok": nonnative_ok("combined"),
        "no_human_source_flagged_more": all(c["human_source"][s]["k"] <= g["human_source"][s]["k"]
                                            for s in g["human_source"]),
        "rehearsal_human_likely_ai": "checked with run_v2.py --rehearsal --scores scores_combined.jsonl",
    }
    out = {"rule": rule, "combiner": model, "n_fit": len(fit), "n_held": len(held_with_attacks), **results}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "metrics.json").write_text(json.dumps(out, indent=1) + "\n")
    (args.out / "scores_combined.jsonl").write_text("".join(
        json.dumps({"sha256": r["sha256"], "scorer": COMBINED, "ai_score": r["combined"],
                    "truncated": gpttrace[r["sha256"]]["truncated"] or desklib[r["sha256"]]["truncated"]}) + "\n"
        for r in rows))
    print(f"wrote {args.out}/metrics.json")


if __name__ == "__main__":
    main()
