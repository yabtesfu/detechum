"""Turn a calibrated P(AI) interval into the verdict a writer sees.

See docs/design/architecture.md §3 (abstain / verdict) and docs/evaluation/plan.md (M1, M3).
The threshold `tau` is chosen on the calibration split so realized FPR ≤ 1% in every stratum;
this function never chooses thresholds, it only applies them.
"""

from dataclasses import dataclass
from enum import Enum

from detechum.conformal import ConformalResult


class Verdict(Enum):
    # Covers human text that an AI edited: the pilot scorer flags most of it and cannot separate it
    # from text an AI wrote (architecture §8).
    LIKELY_AI = "Likely AI written or AI edited"
    LIKELY_HUMAN = "Likely human written"
    CANT_TELL = "Can't tell reliably"
    NO_VERDICT = "No verdict (outside calibrated conditions)"


@dataclass(frozen=True)
class ScoredDocument:
    p_ai: float            # calibrated point estimate, 0..1
    p_low: float           # lower bound of the 90% interval (detechum.calibration)
    p_high: float          # upper bound of the 90% interval
    n_words: int
    stratum_calibrated: bool   # calibration data exists for this language, domain and writer group


# Fixed by the project owner on 2026-11-19 (architecture §8), not derived from measured error rates.
MIN_WORDS_FOR_VERDICT = 150


def decide_verdict(doc: ScoredDocument, tau: float, conformal: ConformalResult | None = None) -> Verdict:
    """Return the verdict for one document, given the stratum's decision threshold `tau`.

    A label is returned only when the whole interval [p_low, p_high] lies on one side of
    `tau`; an interval that straddles `tau` yields CANT_TELL. The point estimate never
    decides a label on its own, so a borderline score cannot produce an accusation.

    With `conformal`, a label also needs the conformal prediction set to hold that class alone.
    The conformal layer can turn a label into CANT_TELL or NO_VERDICT and can never create one.

    Raises ValueError if the interval is inconsistent or `tau` is outside (0, 1).
    """
    if not (0.0 <= doc.p_low <= doc.p_ai <= doc.p_high <= 1.0):
        raise ValueError(f"inconsistent interval: {doc.p_low=} {doc.p_ai=} {doc.p_high=}")
    if not 0.0 < tau < 1.0:
        raise ValueError(f"tau must be in (0, 1), got {tau}")

    # Outside calibrated conditions we have no measured error rate, so no label at all.
    if doc.n_words < MIN_WORDS_FOR_VERDICT or not doc.stratum_calibrated:
        return Verdict.NO_VERDICT
    # A length band whose calibration texts are too few to rule out either class cannot give a label
    # for any score, which is a property of the band and not of this text.
    if conformal is not None and not (conformal.can_exclude_human or conformal.can_exclude_ai):
        return Verdict.NO_VERDICT
    if doc.p_low >= tau:
        only_ai = conformal is None or (conformal.ai_in_set and not conformal.human_in_set)
        return Verdict.LIKELY_AI if only_ai else Verdict.CANT_TELL
    if doc.p_high < tau:
        only_human = conformal is None or (conformal.human_in_set and not conformal.ai_in_set)
        return Verdict.LIKELY_HUMAN if only_human else Verdict.CANT_TELL
    return Verdict.CANT_TELL
