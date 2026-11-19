"""Command line entry point: `detechum score FILE`.

Runs normalize, score, calibrate and verdict on one text and prints the result with the reasons
behind it, including the sentences that raise the score most (architecture §5).
"""

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

from detechum.calibration import INTERVAL_LEVEL, Calibrator
from detechum.conformal import ConformalLayer, ConformalResult, min_calibration_texts
from detechum.explain import MIN_CONTRIBUTION, sentence_contributions, split_sentences
from detechum.models import GPTTRACE, ModelVerificationError, verify_model
from detechum.normalize import normalize
from detechum.verdict import MIN_WORDS_FOR_VERDICT, Verdict, decide_verdict

CAVEAT = ("These are statistical signals, not proof of authorship. Human writers, especially those writing "
          "in a second language, can trigger them.")
AI_EDITED_NOTE = ("The text shows signs that an AI had a hand in it. A person may have written it and an AI edited "
                  "it, or an AI may have written all of it. This tool cannot tell those two cases apart.")
MAX_SENTENCES_SHOWN = 5
# Wording follows results/attribution_pilot_v1: the top ranked sentence was the planted AI sentence in
# 27 of 50 essays, and opening sentences ranked first more often than chance.
SENTENCE_CAVEAT = ("This shows what moves the scorer's number, not which sentences are AI written. In a pilot "
                   "test the top ranked sentence was the planted AI sentence about half the time, and "
                   "opening sentences ranked high more often than chance.")


def _sentence_effects(text: str, scorer, raw_score: float, calibrator: Calibrator | None) -> dict:
    contributions = sentence_contributions(text, scorer, raw_score)
    strongest = sorted((c for c in contributions if c.contribution >= MIN_CONTRIBUTION),
                       key=lambda c: c.contribution, reverse=True)[:MAX_SENTENCES_SHOWN]
    return {
        "count": len(split_sentences(text)), "analysed": len(contributions), "min_contribution": MIN_CONTRIBUTION,
        "strongest": [{"index": c.index, "text": c.text, "contribution": c.contribution,
                       "score_without": c.score_without,
                       "p_ai_without": calibrator.predict(c.score_without)[0] if calibrator else None}
                      for c in strongest],
    }


def _conformal_reasons(conformal: ConformalResult, interval_verdict: Verdict, verdict: Verdict) -> list[str]:
    """Say what the comparison with the length band found and, if it withheld a label, why."""
    c = conformal
    band = f"{c.min_words} or more words" if c.max_words is None else f"{c.min_words} to {c.max_words - 1} words"
    reasons = [f"Among calibration texts of {band}, {c.human_at_or_above} of {c.n_human} human texts score this "
               f"high or higher and {c.ai_at_or_below} of {c.n_ai} AI texts score this low or lower."]
    if verdict is interval_verdict:
        return reasons
    need_human, need_ai = min_calibration_texts(c.alpha_human), min_calibration_texts(c.alpha_ai)
    if verdict is Verdict.NO_VERDICT:
        return reasons + [f"A label for a text of this length needs at least {need_human} human or {need_ai} AI "
                          "calibration texts, so no verdict is given."]
    if interval_verdict is Verdict.LIKELY_AI and c.human_in_set:
        target = f"at the {c.alpha_human * 100:g}% error target, so the text is not labelled as AI."
        blocked = (f"That does not rule out a human writer {target}" if c.can_exclude_human else
                   f"At least {need_human} human calibration texts of this length are needed before a text may be "
                   f"labelled as AI {target}")
    elif interval_verdict is Verdict.LIKELY_HUMAN and c.ai_in_set:
        target = f"at the {c.alpha_ai * 100:g}% error target, so the text is not labelled as human written."
        blocked = (f"That does not rule out an AI {target}" if c.can_exclude_ai else
                   f"At least {need_ai} AI calibration texts of this length are needed before a text may be "
                   f"labelled as human written {target}")
    else:
        blocked = ("The score is higher than nearly all human calibration texts of this length and lower than "
                   "nearly all AI ones. It resembles neither group, so no label is given.")
    return reasons + [blocked]


def analyse(text: str, scorer, calibration: dict | None, explain: bool = True, model: dict | None = None) -> dict:
    """Score one text and return every value the report shows.

    `scorer` needs `name`, `score(list[str])` and `is_truncated(str)`. `calibration` is the content
    of a calibration file or None, in which case no verdict is given. A calibration file with a
    "conformal" entry also applies the conformal abstention layer. With `explain`, each sentence
    is removed in turn and the rest scored again, which costs one scorer pass per sentence. `model` is
    the record of the pinned model behind `scorer`, passed only by a caller that has verified its
    files; the report then names the model and says the files were verified.

    Raises ValueError if the text has no words or the calibration was fitted for another scorer.
    """
    cleaned, found = normalize(text)
    n_words = len(cleaned.split())
    if n_words == 0:
        raise ValueError("the text has no words")
    if calibration is not None and calibration["scorer"] != scorer.name:
        raise ValueError(f"calibration {calibration['name']!r} was fitted for {calibration['scorer']!r}, "
                         f"not for {scorer.name!r}")

    result = {
        "n_words": n_words, "scorer": scorer.name, "model": model, "raw_score": float(scorer.score([cleaned])[0]),
        "normalization": found.summary(), "evasion_suspected": found.evasion_suspected,
        "calibration": None, "p_ai": None, "interval": None, "tau": None, "conformal": None,
        "verdict": Verdict.NO_VERDICT.value, "reasons": [], "sentences": None,
    }
    reasons = result["reasons"]
    if scorer.is_truncated(cleaned):
        reasons.append("The text is longer than the scorer's input limit, so only its beginning was scored. "
                       "Removing a sentence pulls later text into the scored part, so sentence effects are "
                       "less reliable for this text.")
    calibrator = Calibrator.from_dict(calibration["calibrator"]) if calibration else None
    if explain:
        result["sentences"] = _sentence_effects(cleaned, scorer, result["raw_score"], calibrator)

    if calibration is None:
        reasons.append("No calibration file was given, so the raw score cannot be turned into a probability.")
        return result

    doc = calibrator.scored_document(result["raw_score"], n_words)
    tau = calibration["tau"]
    result.update(
        calibration={"name": calibration["name"], "description": calibration["description"],
                     "n_human": calibrator.n_human, "n_ai": calibrator.n_ai},
        p_ai=doc.p_ai, interval=[doc.p_low, doc.p_high], tau=tau)
    if tau is None:
        reasons.append("This calibration has no threshold that meets its false positive target.")
        return result

    if n_words < MIN_WORDS_FOR_VERDICT:
        reasons.append(f"The text has {n_words} words. Texts under {MIN_WORDS_FOR_VERDICT} words get no verdict.")
        return result
    layer = ConformalLayer.from_dict(calibration["conformal"]) if calibration.get("conformal") else None
    conformal = layer.assess(result["raw_score"], n_words) if layer else None
    if layer and conformal is None:
        result["verdict"] = decide_verdict(replace(doc, stratum_calibrated=False), tau).value
        reasons.append(f"The calibration has no length band for a text of {n_words} words, so no verdict is given.")
        return result

    interval_verdict, verdict = decide_verdict(doc, tau), decide_verdict(doc, tau, conformal)
    result.update(verdict=verdict.value, conformal=conformal.to_dict() if conformal else None)
    low, high = f"{doc.p_low:.2f}", f"{doc.p_high:.2f}"
    if interval_verdict is Verdict.LIKELY_AI:
        reasons.append(f"The whole interval ({low} to {high}) is at or above the threshold {tau:.2f}.")
    elif interval_verdict is Verdict.LIKELY_HUMAN:
        reasons.append(f"The whole interval ({low} to {high}) is below the threshold {tau:.2f}.")
    else:
        reasons.append(f"The interval ({low} to {high}) contains the threshold {tau:.2f}.")
    if conformal:
        reasons += _conformal_reasons(conformal, interval_verdict, verdict)
    if verdict is Verdict.LIKELY_AI:
        reasons.append(AI_EDITED_NOTE)
    return result


def render_text(result: dict) -> str:
    def row(label: str, value: str) -> str:
        return f"{label} {'.' * (27 - len(label))} {value}"

    lines = [f"Document: {result['n_words']} words", ""]
    if result["p_ai"] is None:
        lines.append(row("P(AI generated)", "not available"))
    else:
        low, high = result["interval"]
        lines.append(row("P(AI generated)", f"{result['p_ai']:.2f}   "
                                            f"({round(INTERVAL_LEVEL * 100)}% interval {low:.2f} to {high:.2f})"))
    lines.append(row("Verdict", result["verdict"]))
    lines.append(row("Raw score", f"{result['raw_score']:.3f}   ({result['scorer']})"))
    if result["model"]:
        model = result["model"]
        lines.append(row("Model", f"{model['repo']} at revision {model['revision'][:12]}, files verified by SHA 256"))
    if result["calibration"]:
        cal = result["calibration"]
        lines.append(row("Calibration", f"{cal['name']}, fitted on {cal['n_human']} human and {cal['n_ai']} AI texts"))
        lines.append(f"  {cal['description']}")
    lines += ["", "Why"] + [f" * {reason}" for reason in result["reasons"]]
    lines += _render_sentences(result["sentences"])
    if result["normalization"]:
        lines += ["", "Found in the input"] + [f" * {item}" for item in result["normalization"]]
    return "\n".join(lines + ["", CAVEAT])


def _render_sentences(sentences: dict | None) -> list[str]:
    if sentences is None:
        return []
    lines = ["", "Sentences that raise the score most (each removed in turn, the rest scored again)"]
    if sentences["analysed"] == 0:
        return lines + [" The text has fewer than two sentences, so sentence effects cannot be measured."]
    if not sentences["strongest"]:
        return lines + [f" No single sentence changes the raw score by {sentences['min_contribution']:g} or more. "
                        "The score rests on the text as a whole."]
    for s in sentences["strongest"]:
        quote = s["text"] if len(s["text"]) <= 70 else s["text"][:67].rstrip() + "..."
        without = f"raw score {s['score_without']:.2f}"
        if s["p_ai_without"] is not None:
            without += f", P(AI) {s['p_ai_without']:.2f}"
        lines += [f" S{s['index']:<3} +{s['contribution']:.2f}  \"{quote}\"", f"      Without it: {without}"]
    if sentences["analysed"] < sentences["count"]:
        lines.append(f" Only the first {sentences['analysed']} of {sentences['count']} sentences were analysed.")
    return lines + [f" {SENTENCE_CAVEAT}"]


def _load_scorer(models: Path, device: str | None):
    """Return the GPTTrace scorer and the record of its model, after verifying the model files.

    The files are verified before anything from the folder is loaded, because loading the scorer
    executes the folder's `normalize.py`.
    """
    try:
        snapshot = verify_model(GPTTRACE, models)
    except ModelVerificationError as exc:
        raise SystemExit(f"{exc}\nNo score was produced. Run eval/fetch_models.py to restore the pinned files, "
                         "or pass --models with the folder that holds them.")
    try:
        import torch
        from detechum.scorers.gpttrace import GPTTraceScorer
    except ImportError as exc:
        raise SystemExit(f"scoring needs the model dependencies: pip install 'detechum[models]' ({exc})")
    device = device or ("mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
    return GPTTraceScorer(snapshot, device, typography=False), GPTTRACE.record()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="detechum")
    score = parser.add_subparsers(dest="command", required=True).add_parser(
        "score", help="estimate P(AI) for one text file")
    score.add_argument("file", help="path of a UTF 8 text file, or - for standard input")
    score.add_argument("--calibration", type=Path, help="calibration file; without it no verdict is given")
    score.add_argument("--models", type=Path, default=Path("data/external/models"))
    score.add_argument("--device", help="torch device; chosen automatically when omitted")
    score.add_argument("--json", action="store_true", help="print the full result as JSON")
    score.add_argument("--no-explain", action="store_true", help="skip the sentence analysis, which is slower")
    args = parser.parse_args(argv)

    text = sys.stdin.read() if args.file == "-" else Path(args.file).read_text(encoding="utf-8")
    calibration = json.loads(args.calibration.read_text()) if args.calibration else None
    scorer, model = _load_scorer(args.models, args.device)
    try:
        result = analyse(text, scorer, calibration, explain=not args.no_explain, model=model)
    except ValueError as exc:
        raise SystemExit(str(exc))
    print(json.dumps(result, indent=1) if args.json else render_text(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
