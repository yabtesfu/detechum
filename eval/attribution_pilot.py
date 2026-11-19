"""Does sentence attribution locate an AI written sentence? (architecture §5)

`detechum.explain` ranks sentences by how much the score drops when each is removed. That number is
exact about the scorer. Whether the top ranked sentence is the AI written one is an empirical
question, tested here with a known answer: one sentence from a GPT 3 essay is planted at a random
position in a native human essay, and the rank of the planted sentence is recorded.

A second measurement records how often the first sentence of the text ranks highest when it is not
the planted one, to expose an effect of position alone.

Texts are built by joining sentences with a space. An essay or a planting is used only if splitting
the joined text returns the same sentences, so that the planted sentence is one unit of the analysis.

Reading of the result, fixed before the run: the method may be described as locating AI written
sentences only if the 95% lower bound of the top rank hit rate is above the chance rate. Otherwise
the report must say that listed sentences are not evidence about which sentences are AI written.

Essays stay in data/external/. Only SHA 256 hashes and numbers are written to the output folder.

Usage: python eval/attribution_pilot.py --liang data/external/liang --out results/attribution_pilot_v1
"""

import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch

from bias_experiment import MODELS, load_groups, sha256, verify_models
from detechum.explain import MIN_CONTRIBUTION, sentence_contributions, split_sentences
from detechum.scorers.gpttrace import GPTTraceScorer
from detechum.stats import clopper_pearson

SEED = 20261118
N_ESSAYS = 50
MAX_DRAWS = 5           # attempts to find a planting that splits cleanly
MAX_WORDS = 250          # keeps every text inside the scorer's 512 token window
MIN_SENTENCES = 6
PLANT_WORDS = (12, 40)   # length range of a planted sentence
HUMAN_GROUP = "HewlettStudentEssay_real_88"
AI_GROUPS = ("CollegeEssay_gpt3_31", "CollegeEssay_gpt3PromptEng_31")


def leading_sentences(text: str) -> list[str]:
    out, words = [], 0
    for a, b in split_sentences(text):
        words += len(text[a:b].split())
        if words > MAX_WORDS:
            break
        out.append(text[a:b])
    return out


def splits_cleanly(sentences: list[str]) -> bool:
    text = " ".join(sentences)
    return [text[a:b] for a, b in split_sentences(text)] == sentences


def plant(sentences: list[str], pool: list[str], rng: random.Random) -> tuple[int, list[str]] | None:
    for _ in range(MAX_DRAWS):
        position = rng.randrange(len(sentences) + 1)
        planted = sentences[:position] + [rng.choice(pool)] + sentences[position:]
        if splits_cleanly(planted):
            return position, planted
    return None


def rank_of(contributions, index: int) -> int:
    """Rank of the sentence at `index` by contribution, 1 for the largest. Ties take the worst rank."""
    target = next(c.contribution for c in contributions if c.index == index)
    return sum(c.contribution >= target for c in contributions)


def rate(k: int, n: int) -> dict:
    lo, hi = clopper_pearson(k, n)
    return {"k": k, "n": n, "rate": k / n, "ci95": [lo, hi]}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--liang", type=Path, required=True)
    ap.add_argument("--models", type=Path, default=Path("data/external/models"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--device", default="mps" if torch.backends.mps.is_available() else "cpu")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    groups = load_groups(args.liang)
    rng = random.Random(SEED)
    pool = [text[a:b] for g in AI_GROUPS for text in groups[g]["texts"] for a, b in split_sentences(text)
            if PLANT_WORDS[0] <= len(text[a:b].split()) <= PLANT_WORDS[1]]
    candidates = [s for s in map(leading_sentences, groups[HUMAN_GROUP]["texts"])
                  if len(s) >= MIN_SENTENCES and splits_cleanly(s)]
    rng.shuffle(candidates)
    cases = [(sentences, planting) for sentences in candidates if (planting := plant(sentences, pool, rng))][:N_ESSAYS]

    scorer = GPTTraceScorer(verify_models(args.models, keys=("gpttrace",))["gpttrace"], args.device, typography=False)
    rows = []
    for n, (sentences, (position, planted_sentences)) in enumerate(cases, start=1):
        original, planted = " ".join(sentences), " ".join(planted_sentences)
        original_score, planted_score = scorer.score([original, planted])
        contributions = sentence_contributions(planted, scorer, planted_score)
        rows.append({
            "sha256": sha256(original), "n_sentences": len(contributions), "plant_index": position + 1,
            "original_score": original_score, "planted_score": planted_score,
            "plant_contribution": contributions[position].contribution,
            "plant_rank": rank_of(contributions, position + 1),
            "first_sentence_rank": rank_of(contributions, 1),
            "first_sentence_contribution": contributions[0].contribution,
        })
        print(f"{n}/{len(cases)}", flush=True)

    n = len(rows)
    human_first = [r for r in rows if r["plant_index"] != 1]
    metrics = {
        "seed": SEED, "scorer": scorer.name, "min_contribution": MIN_CONTRIBUTION,
        "model": dict(zip(("repo", "revision"), MODELS["gpttrace"][:2])),
        "planted": {
            "ranked_first": rate(sum(r["plant_rank"] == 1 for r in rows), n),
            "ranked_in_top_3": rate(sum(r["plant_rank"] <= 3 for r in rows), n),
            "chance_ranked_first": float(np.mean([1 / r["n_sentences"] for r in rows])),
            "chance_ranked_in_top_3": float(np.mean([min(1.0, 3 / r["n_sentences"]) for r in rows])),
            "contribution_at_least_min": rate(sum(r["plant_contribution"] >= MIN_CONTRIBUTION for r in rows), n),
            "median_contribution": float(np.median([r["plant_contribution"] for r in rows])),
            "median_score_change_from_planting": float(np.median([r["planted_score"] - r["original_score"] for r in rows])),
        },
        "human_first_sentence": {
            "ranked_first": rate(sum(r["first_sentence_rank"] == 1 for r in human_first), len(human_first)),
            "chance": float(np.mean([1 / r["n_sentences"] for r in human_first])),
            "median_contribution": float(np.median([r["first_sentence_contribution"] for r in human_first])),
        },
    }
    p, u = metrics["planted"], metrics["human_first_sentence"]
    locates = p["ranked_first"]["ci95"][0] > p["chance_ranked_first"]
    metrics["locates_planted_sentence"] = locates

    def show(r: dict) -> str:
        return f"{r['k']}/{r['n']} = {r['rate'] * 100:.1f}% ({r['ci95'][0] * 100:.1f} to {r['ci95'][1] * 100:.1f})"

    report = [
        "# Sentence attribution pilot (attribution_pilot_v1)", "",
        f"Scorer: `{scorer.name}`. {n} native human essays (first {MAX_WORDS} words at most), each with one GPT 3 "
        f"sentence planted at a random position. Seed `{SEED}`. Intervals are 95% Clopper Pearson.", "",
        f"**Result under the reading fixed before the run: the method "
        f"{'locates' if locates else 'does not reliably locate'} the planted sentence.**", "",
        "| Measure | Observed | Chance |", "|---|---|---|",
        f"| Planted sentence ranked first | {show(p['ranked_first'])} | {p['chance_ranked_first'] * 100:.1f}% |",
        f"| Planted sentence in the top 3 | {show(p['ranked_in_top_3'])} | {p['chance_ranked_in_top_3'] * 100:.1f}% |",
        f"| Planted sentence raises the score by {MIN_CONTRIBUTION:g} or more | {show(p['contribution_at_least_min'])} | |",
        f"| Human first sentence ranked first, when the planted sentence is elsewhere | {show(u['ranked_first'])} | "
        f"{u['chance'] * 100:.1f}% |", "",
        f"* Median contribution of the planted sentence: {p['median_contribution']:.2f}",
        f"* Median change of the document score from planting: {p['median_score_change_from_planting']:.2f}",
        f"* Median contribution of a human first sentence: {u['median_contribution']:.2f}", "",
    ]
    (args.out / "rows.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (args.out / "metrics.json").write_text(json.dumps(metrics, indent=1) + "\n")
    (args.out / "report.md").write_text("\n".join(report))
    print(f"wrote {args.out}/report.md, metrics.json and rows.jsonl")


if __name__ == "__main__":
    main()
