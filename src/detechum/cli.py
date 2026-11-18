"""Command line entry point: `detechum score FILE`.

Runs normalize, score, calibrate and verdict on one text and prints the result with the reasons
behind it. Sentence level reasons (architecture §5) are not produced yet.
"""

import argparse
import json
import sys
from pathlib import Path

from detechum.calibration import INTERVAL_LEVEL, Calibrator
from detechum.normalize import normalize
from detechum.verdict import MIN_WORDS_FOR_VERDICT, Verdict, decide_verdict

GPTTRACE_FOLDER = "gpttrace-v8s-1b"
CAVEAT = ("These are statistical signals, not proof of authorship. Human writers, especially those writing "
          "in a second language, can trigger them.")
AI_EDITED_NOTE = "This label does not separate AI written text from human text that an AI edited."


def analyse(text: str, scorer, calibration: dict | None) -> dict:
    """Score one text and return every value the report shows.

    `scorer` needs `name`, `score(list[str])` and `is_truncated(str)`. `calibration` is the content
    of a calibration file or None, in which case no verdict is given.

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
        "verdict": Verdict.NO_VERDICT.value, "reasons": [],
    }
    reasons = result["reasons"]
    if scorer.is_truncated(cleaned):
        reasons.append("The text is longer than the scorer's input limit, so only its beginning was scored.")

    if calibration is None:
        reasons.append("No calibration file was given, so the raw score cannot be turned into a probability.")
        return result

    calibrator = Calibrator.from_dict(calibration["calibrator"])
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
    if result["normalization"]:
        lines += ["", "Found in the input"] + [f" * {item}" for item in result["normalization"]]
    return "\n".join(lines + ["", CAVEAT])


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
    args = parser.parse_args(argv)

    text = sys.stdin.read() if args.file == "-" else Path(args.file).read_text(encoding="utf-8")
    calibration = json.loads(args.calibration.read_text()) if args.calibration else None
    try:
        result = analyse(text, _load_scorer(args.models, args.device), calibration)
    except ValueError as exc:
        raise SystemExit(str(exc))
    print(json.dumps(result, indent=1) if args.json else render_text(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
