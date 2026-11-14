"""Nonnative writer false positive experiment (first measurement for docs/evaluation/plan.md, M1 and M3).

Data: Liang et al. 2023 (github.com/Weixin-Liang/ChatGPT-Detector-Bias). The repository has no licence,
so essays stay in data/external/ and only SHA 256 hashes and scores are written to results/.

Usage:
    eval/fetch_models.sh
    .venv/bin/python eval/bias_experiment.py --liang data/external/liang \
        --models data/external/models --out results/bias_v1
"""

import argparse
import hashlib
import json
import platform
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch
import transformers
from scipy.stats import beta, mannwhitneyu

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from detechum.scorers.binoculars import BinocularsScorer  # noqa: E402
from detechum.scorers.gpttrace import GPTTraceScorer  # noqa: E402

# key: (hub repo, pinned revision, local folder written by eval/fetch_models.sh, weights file, published SHA 256)
MODELS = {
    "gpttrace": ("nakas/gpttrace-v8s-1b", "ac748e32ca8c90bb8858fadc427757728e27b063", "gpttrace-v8s-1b",
                 "model/model.safetensors", "379b154cadb0fd6a226badd2f745705f49c19461ef150ee6b97fec92e82ba538"),
    "qwen_base": ("Qwen/Qwen2.5-1.5B", "8faed761d45a263340a0528343f099c05c9a4323", "qwen2.5-1.5b",
                  "model.safetensors", "a961db72e75d52b18e6b0c9d379e51a26973b233385e0e127fdda7d648aec796"),
    "qwen_instruct": ("Qwen/Qwen2.5-1.5B-Instruct", "989aa7980e4cf806f80c7fef2b1adb7bc71aa306",
                      "qwen2.5-1.5b-instruct", "model.safetensors",
                      "dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee"),
}

# (folder, role). "ai_edited" groups are human essays rewritten by GPT 4; they are neither human nor
# AI for FPR or TPR purposes and are reported on their own.
GROUPS = [
    ("Human_Data/TOEFL_real_91", "human_nonnative"),
    ("Human_Data/HewlettStudentEssay_real_88", "human_native"),
    ("Human_Data/CollegeEssay_real_70", "human_native"),
    ("Human_Data/CS224N_real_145", "human_unknown"),
    ("Human_Data/TOEFL_gpt4polished_91", "ai_edited"),
    ("Human_Data/HewlettStudentEssay_GPTsimplify_88", "ai_edited"),
    ("GPT_Data/CollegeEssay_gpt3_31", "ai"),
    ("GPT_Data/CollegeEssay_gpt3PromptEng_31", "ai"),
    ("GPT_Data/CS224N_gpt3_145", "ai"),
    ("GPT_Data/CS224N_gpt3PromptEng_145", "ai"),
]
CONTROL = "control/Hewlett_truncated_to_TOEFL_lengths"
SEED = 20261114
TARGET_FPR = 0.01
GPTTRACE_VENDOR_THRESHOLD = 9.3  # model card: "a logit of 9.3 flags 1% of human texts"


def load_groups(liang_root: Path) -> dict[str, dict]:
    base = liang_root / "Data_and_Results"
    groups = {}
    for folder, role in GROUPS:
        docs = [d["document"] for d in json.loads((base / folder / "data.json").read_text())]
        groups[Path(folder).name] = {"role": role, "texts": docs}
    # Length matched native control: separates "nonnative" from "short". Each TOEFL essay is paired
    # with a native essay cut to the same word count.
    toefl = groups["TOEFL_real_91"]["texts"]
    native = list(groups["HewlettStudentEssay_real_88"]["texts"])
    random.Random(SEED).shuffle(native)
    control = [" ".join(native[i % len(native)].split()[:len(t.split())]) for i, t in enumerate(toefl)]
    groups[CONTROL] = {"role": "human_native_length_matched", "texts": control}
    return groups


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return lo, hi


def flag_stats(scores: list[float], threshold: float) -> dict:
    k = int(sum(s > threshold for s in scores))
    n = len(scores)
    lo, hi = clopper_pearson(k, n)
    return {"flagged": k, "n": n, "rate": k / n, "ci95": [lo, hi]}


def native_threshold(scores: list[float]) -> float:
    # Smallest threshold that flags at most TARGET_FPR of the native calibration texts (flag means score > t).
    return float(np.quantile(np.asarray(scores), 1 - TARGET_FPR, method="higher"))


def verify_models(models_root: Path) -> dict[str, Path]:
    paths = {}
    for key, (repo, _rev, folder, weights, expected) in MODELS.items():
        digest = hashlib.sha256()
        with (models_root / folder / weights).open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 24), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected:
            raise SystemExit(f"{repo}: {weights} does not match the published SHA 256; rerun eval/fetch_models.sh")
        paths[key] = models_root / folder
    return paths


def build_scorers(paths: dict[str, Path], device: str):
    yield lambda: GPTTraceScorer(paths["gpttrace"], device, typography=False)
    yield lambda: GPTTraceScorer(paths["gpttrace"], device, typography=True)
    yield lambda: BinocularsScorer(paths["qwen_base"], paths["qwen_instruct"], device,
                                   name="binoculars_style_qwen2.5_1.5b_pair_unvalidated")


def score_all(groups: dict, paths: dict[str, Path], out: Path, device: str) -> dict:
    cache_file = out / "scores.jsonl"
    cached = {}
    if cache_file.exists():
        for line in cache_file.read_text().splitlines():
            r = json.loads(line)
            cached[(r["scorer"], r["group"], r["index"])] = r["ai_score"]
    with cache_file.open("a") as fh:
        for make in build_scorers(paths, device):
            scorer = make()
            for gname, g in groups.items():
                todo = [i for i in range(len(g["texts"])) if (scorer.name, gname, i) not in cached]
                if not todo:
                    continue
                print(f"{scorer.name}: {gname} ({len(todo)} texts)", flush=True)
                values = scorer.score([g["texts"][i] for i in todo])
                for i, v in zip(todo, values):
                    text = g["texts"][i]
                    row = {"scorer": scorer.name, "group": gname, "index": i, "sha256": sha256(text),
                           "n_words": len(text.split()), "ai_score": v}
                    fh.write(json.dumps(row) + "\n")
                    cached[(scorer.name, gname, i)] = v
            del scorer
            if device == "mps":
                torch.mps.empty_cache()
    return cached


def summarize(groups: dict, cached: dict) -> dict:
    scorer_names = sorted({k[0] for k in cached})
    report = {}
    for s in scorer_names:
        by_group = {g: [cached[(s, g, i)] for i in range(len(groups[g]["texts"]))] for g in groups}
        native = [v for g, vals in by_group.items() if groups[g]["role"] == "human_native" for v in vals]
        thresholds = {"native_calibrated_1pct": native_threshold(native)}
        if s.startswith("gpttrace"):
            thresholds["vendor_9.3"] = GPTTRACE_VENDOR_THRESHOLD
            thresholds["raw_0"] = 0.0
        # The length matched control reuses native essays, so it is left out to avoid counting them twice.
        human = [v for g, vals in by_group.items()
                 if groups[g]["role"] in {"human_native", "human_nonnative", "human_unknown"} for v in vals]
        ai = [v for g, vals in by_group.items() if groups[g]["role"] == "ai" for v in vals]
        auroc = float(mannwhitneyu(ai, human).statistic / (len(ai) * len(human)))
        report[s] = {
            "auroc_ai_vs_all_human": auroc,
            "thresholds": thresholds,
            "groups": {
                g: {
                    "role": groups[g]["role"],
                    "median_words": int(np.median([len(t.split()) for t in groups[g]["texts"]])),
                    "median_ai_score": float(np.median(vals)),
                    "at_threshold": {name: flag_stats(vals, t) for name, t in thresholds.items()},
                }
                for g, vals in by_group.items()
            },
        }
    return report


def environment(liang_root: Path) -> dict:
    liang_commit = subprocess.run(["git", "-C", str(liang_root), "rev-parse", "HEAD"],
                                  capture_output=True, text=True).stdout.strip()
    return {"python": platform.python_version(), "torch": torch.__version__,
            "transformers": transformers.__version__, "machine": platform.machine(),
            "liang_commit": liang_commit,
            "models": {k: {"repo": m[0], "revision": m[1], "weights_sha256": m[4]} for k, m in MODELS.items()},
            "seed": SEED, "target_fpr": TARGET_FPR}


def render_report(result: dict) -> str:
    env = result["environment"]
    lines = [
        "# Nonnative writer false positive experiment (bias_v1)",
        "",
        f"Data: Liang et al. 2023 repository at commit `{env['liang_commit']}`. "
        f"Python {env['python']}, torch {env['torch']}, transformers {env['transformers']}, {env['machine']}.",
        "Flag rates are shown with 95% Clopper Pearson intervals. A text is flagged when its score is above the threshold.",
        "",
    ]
    for scorer, r in result["results"].items():
        lines += [f"## {scorer}", "", f"AUROC, AI groups against all human groups: {r['auroc_ai_vs_all_human']:.3f}", ""]
        names = list(r["thresholds"])
        lines.append("| Group | Role | Median words | " + " | ".join(f"Flagged at {n} ({r['thresholds'][n]:.3f})" for n in names) + " |")
        lines.append("|---|---|---|" + "---|" * len(names))
        for g, gr in r["groups"].items():
            cells = []
            for n in names:
                s = gr["at_threshold"][n]
                lo, hi = s["ci95"]
                cells.append(f"{s['flagged']}/{s['n']} = {100 * s['rate']:.1f}% ({100 * lo:.1f} to {100 * hi:.1f})")
            lines.append(f"| {g} | {gr['role']} | {gr['median_words']} | " + " | ".join(cells) + " |")
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--liang", type=Path, required=True)
    ap.add_argument("--models", type=Path, default=Path("data/external/models"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--device", default="mps" if torch.backends.mps.is_available() else "cpu")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    groups = load_groups(args.liang)
    paths = verify_models(args.models)
    cached = score_all(groups, paths, args.out, args.device)
    result = {"environment": environment(args.liang), "results": summarize(groups, cached)}
    (args.out / "metrics.json").write_text(json.dumps(result, indent=2))
    (args.out / "report.md").write_text(render_report(result))
    print(f"wrote {args.out / 'metrics.json'} and report.md")


if __name__ == "__main__":
    main()
