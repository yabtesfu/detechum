"""Turn a calibrated P(AI) interval into the verdict a writer sees.

See docs/design/architecture.md §3 (abstain / verdict) and docs/evaluation/plan.md (M1, M3).
The threshold `tau` is chosen on the calibration split so realized FPR ≤ 1% in every stratum;
this function never chooses thresholds, it only applies them.
"""

from dataclasses import dataclass
from enum import Enum


class Verdict(Enum):
    LIKELY_AI = "Likely AI generated"
    LIKELY_HUMAN = "Likely human written"
    CANT_TELL = "Can't tell reliably"
    NO_VERDICT = "No verdict (outside calibrated conditions)"


@dataclass(frozen=True)
class ScoredDocument:
    p_ai: float            # calibrated point estimate, 0..1
    p_low: float           # 5th percentile of the bootstrap interval
    p_high: float          # 95th percentile of the bootstrap interval
    n_words: int
    stratum_calibrated: bool   # do we have calibration data for this language/domain/writer group?


MIN_WORDS_FOR_VERDICT = 150  # provisional; set from length stratified curves (plan.md §1)


def decide_verdict(doc: ScoredDocument, tau: float) -> Verdict:
    """Return the verdict for one document, given the stratum's decision threshold `tau`.

    Policy (strict): a label is only given when the WHOLE uncertainty interval sits on one
    side of `tau`. If the interval straddles `tau`, we say so instead of letting the point
    estimate decide, because that is how innocent writers get accused on a coin toss.
    """
    if not (0.0 <= doc.p_low <= doc.p_ai <= doc.p_high <= 1.0):
        raise ValueError(f"inconsistent interval: {doc.p_low=} {doc.p_ai=} {doc.p_high=}")
    if not 0.0 < tau < 1.0:
        raise ValueError(f"tau must be in (0, 1), got {tau}")

    # Outside calibrated conditions we have no measured error rate, so no label at all.
    if doc.n_words < MIN_WORDS_FOR_VERDICT or not doc.stratum_calibrated:
        return Verdict.NO_VERDICT
    if doc.p_low >= tau:
        return Verdict.LIKELY_AI
    if doc.p_high < tau:
        return Verdict.LIKELY_HUMAN
    return Verdict.CANT_TELL
