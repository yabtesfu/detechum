"""Command line entry point: `detechum score FILE`.

Runs normalize, score, calibrate and verdict on one text and prints the result with the reasons
behind it, including the sentences that raise the score most (architecture §5).
"""

import argparse
import json
import sys
from pathlib import Path

from detechum.calibration import INTERVAL_LEVEL, Calibrator
from detechum.explain import MIN_CONTRIBUTION, sentence_contributions, split_sentences
from detechum.normalize import normalize
from detechum.verdict import MIN_WORDS_FOR_VERDICT, Verdict, decide_verdict

GPTTRACE_FOLDER = "gpttrace-v8s-1b"
CAVEAT = ("These are statistical signals, not proof of authorship. Human writers, especially those writing "
          "in a second language, can trigger them.")
AI_EDITED_NOTE = "This label does not separate AI written text from human text that an AI edited."
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


def analyse(text: str, scorer, calibration: dict | None, explain: bool = True) -> dict:
    """Score one text and return every value the report shows.

    `scorer` needs `name`, `score(list[str])` and `is_truncated(str)`. `calibration` is the content
    of a calibration file or None, in which case no verdict is given. With `explain`, each sentence
    is removed in turn and the rest scored again, which costs one scorer pass per sentence.

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
        "n_words": n_words, "scorer": scorer.name, "raw_score": float(scorer.score([cleaned])[0]),
        "normalization": found.summary(), "evasion_suspected": found.evasion_suspected,
        "calibration": None, "p_ai": None, "interval": None, "tau": None,
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

    verdict = decide_verdict(doc, tau)
    result["verdict"] = verdict.value
    low, high = f"{doc.p_low:.2f}", f"{doc.p_high:.2f}"
    if verdict is Verdict.NO_VERDICT:
        reasons.append(f"The text has {n_words} words. Texts under {MIN_WORDS_FOR_VERDICT} words get no verdict.")
    elif verdict is Verdict.LIKELY_AI:
        reasons += [f"The whole interval ({low} to {high}) is at or above the threshold {tau:.2f}.", AI_EDITED_NOTE]
    elif verdict is Verdict.LIKELY_HUMAN:
        reasons.append(f"The whole interval ({low} to {high}) is below the threshold {tau:.2f}.")
    else:
        reasons.append(f"The interval ({low} to {high}) contains the threshold {tau:.2f}.")
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
    try:
        import torch
        from detechum.scorers.gpttrace import GPTTraceScorer
    except ImportError as exc:
        raise SystemExit(f"scoring needs the model dependencies: pip install 'detechum[models]' ({exc})")
    snapshot = models / GPTTRACE_FOLDER
    if not snapshot.is_dir():
        raise SystemExit(f"model folder {snapshot} not found; run eval/fetch_models.py or pass --models")
    device = device or ("mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
    return GPTTraceScorer(snapshot, device, typography=False)


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
    try:
        result = analyse(text, _load_scorer(args.models, args.device), calibration, explain=not args.no_explain)
    except ValueError as exc:
        raise SystemExit(str(exc))
    print(json.dumps(result, indent=1) if args.json else render_text(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
