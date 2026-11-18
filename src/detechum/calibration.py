"""Map a raw detector score to P(AI) with an interval (docs/design/architecture.md §3).

The map is an isotonic regression of the label on the score, so P(AI) reads as "the share of AI
texts among calibration texts scored like this one". That share depends on the mix of human and
AI texts in the calibration set, which is why a `Calibrator` records both counts.

The conformal abstention layer of §3 is not implemented here. Abstention currently comes from the
interval rule in `detechum.verdict`.
"""

import math
from dataclasses import dataclass

import numpy as np
from scipy.optimize import isotonic_regression

from detechum.stats import clopper_pearson
from detechum.verdict import ScoredDocument

INTERVAL_LEVEL = 0.90  # the report shows the 5th to 95th percentile
N_BOOTSTRAP = 1000
# A "likely" label below even odds would contradict its own wording, whatever the FPR target allows.
MIN_TAU = 0.5


@dataclass(frozen=True, eq=False)
class Calibrator:
    """Piecewise linear maps from score to P(AI) and to the bounds of its interval.

    `knots` are the distinct calibration scores in increasing order. Scores outside their range get
    the value at the nearest knot.
    """

    knots: np.ndarray
    p_ai: np.ndarray
    p_low: np.ndarray
    p_high: np.ndarray
    n_human: int
    n_ai: int

    def predict(self, score: float) -> tuple[float, float, float]:
        """Return (P(AI), lower bound, upper bound) for one raw score."""
        if not math.isfinite(score):
            raise ValueError(f"score must be finite, got {score}")
        p, lo, hi = (float(np.interp(score, self.knots, ys)) for ys in (self.p_ai, self.p_low, self.p_high))
        return p, min(lo, p), max(hi, p)

    def scored_document(self, score: float, n_words: int) -> ScoredDocument:
        p, lo, hi = self.predict(score)
        return ScoredDocument(p_ai=p, p_low=lo, p_high=hi, n_words=n_words, stratum_calibrated=True)

    def to_dict(self) -> dict:
        return {"knots": self.knots.tolist(), "p_ai": self.p_ai.tolist(), "p_low": self.p_low.tolist(),
                "p_high": self.p_high.tolist(), "n_human": self.n_human, "n_ai": self.n_ai}

    @classmethod
    def from_dict(cls, data: dict) -> "Calibrator":
        arrays = {k: np.asarray(data[k], dtype=float) for k in ("knots", "p_ai", "p_low", "p_high")}
        if len({len(a) for a in arrays.values()}) != 1 or len(arrays["knots"]) == 0:
            raise ValueError("calibrator arrays must be non empty and of equal length")
        return cls(**arrays, n_human=int(data["n_human"]), n_ai=int(data["n_ai"]))


def _isotonic(scores: np.ndarray, labels: np.ndarray):
    """Pool adjacent violators over the distinct scores.

    Returns (knots, fitted share of AI per knot, block boundaries into knots, AI count per knot,
    text count per knot).
    """
    knots, inverse, counts = np.unique(scores, return_inverse=True, return_counts=True)
    positives = np.bincount(inverse, weights=labels, minlength=len(knots))
    fit = isotonic_regression(positives / counts, weights=counts, increasing=True)
    return knots, np.clip(fit.x, 0.0, 1.0), fit.blocks, positives, counts


def fit_calibrator(scores, labels, *, seed: int, n_bootstrap: int = N_BOOTSTRAP) -> Calibrator:
    """Fit the score to P(AI) map and its interval on labelled calibration scores.

    `labels` are 1 for AI and 0 for human. The interval is the percentile range of `n_bootstrap`
    refits on resampled data, widened to the exact binomial interval of the pooled block each score
    falls in. Without the widening, a block that holds only AI texts would report an interval of
    zero width, however few texts it holds.

    Raises ValueError if the inputs are malformed or one class is missing.
    """
    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels)
    if scores.ndim != 1 or scores.shape != labels.shape:
        raise ValueError("scores and labels must be one dimensional and of equal length")
    if not np.all(np.isfinite(scores)):
        raise ValueError("scores must be finite")
    if not np.all((labels == 0) | (labels == 1)):
        raise ValueError("labels must be 0 (human) or 1 (AI)")
    labels = labels.astype(float)
    n, n_ai = len(labels), int(labels.sum())
    if n_ai == 0 or n_ai == n:
        raise ValueError("calibration needs both human and AI texts")

    knots, p_ai, blocks, positives, counts = _isotonic(scores, labels)

    rng = np.random.default_rng(seed)
    boot = np.empty((n_bootstrap, len(knots)))
    for b in range(n_bootstrap):
        idx = rng.integers(0, n, n)
        if labels[idx].min() == labels[idx].max():
            boot[b] = labels[idx][0]  # a resample with one class has a constant fit
            continue
        boot_knots, boot_p, *_ = _isotonic(scores[idx], labels[idx])
        boot[b] = np.interp(knots, boot_knots, boot_p)
    tail = (1 - INTERVAL_LEVEL) / 2
    p_low, p_high = np.quantile(boot, tail, axis=0), np.quantile(boot, 1 - tail, axis=0)

    for start, end in zip(blocks[:-1], blocks[1:]):
        exact_low, exact_high = clopper_pearson(int(positives[start:end].sum()), int(counts[start:end].sum()),
                                                alpha=1 - INTERVAL_LEVEL)
        p_low[start:end] = np.minimum(p_low[start:end], exact_low)
        p_high[start:end] = np.maximum(p_high[start:end], exact_high)

    # P(AI) is assumed to rise with the score, so a bound established at one score also holds for
    # every score on the far side of it. This keeps both bounds monotone after the widening.
    p_low = np.maximum.accumulate(np.minimum(p_low, p_ai))
    p_high = np.minimum.accumulate(np.maximum(p_high, p_ai)[::-1])[::-1]
    return Calibrator(knots=knots, p_ai=p_ai, p_low=p_low, p_high=p_high, n_human=n - n_ai, n_ai=n_ai)


def choose_tau(calibrator: Calibrator, human_scores, target_fpr: float) -> float | None:
    """Smallest decision threshold that labels at most `target_fpr` of `human_scores` as AI.

    A text is labelled AI when its lower bound is at or above tau (see `decide_verdict`). Returns
    None when no threshold below 1 meets the target; the caller must then abstain for the stratum.
    The guarantee is in sample: the realised rate on new human text can be higher.
    """
    if not 0.0 < target_fpr < 1.0:
        raise ValueError(f"target_fpr must be in (0, 1), got {target_fpr}")
    lows = np.sort([calibrator.predict(float(s))[1] for s in human_scores])[::-1]
    if len(lows) == 0:
        raise ValueError("human_scores is empty")
    allowed = int(math.floor(target_fpr * len(lows)))
    # tau must exceed the lower bound of the first human text that may not be flagged.
    tau = max(float(np.nextafter(lows[allowed], 2.0)), MIN_TAU)
    return tau if tau < 1.0 else None


def reliability_bins(p_ai, labels, n_bins: int = 15) -> list[dict]:
    """Equal mass bins of predicted P(AI) with the observed share of AI texts in each.

    Bins follow docs/evaluation/plan.md (M2). Tied predictions can be split across neighbouring bins.
    """
    p_ai, labels = np.asarray(p_ai, dtype=float), np.asarray(labels, dtype=float)
    if p_ai.shape != labels.shape or p_ai.ndim != 1 or len(p_ai) == 0:
        raise ValueError("p_ai and labels must be non empty, one dimensional and of equal length")
    order = np.argsort(p_ai, kind="stable")
    bins = []
    for idx in np.array_split(order, min(n_bins, len(order))):
        k, n = int(labels[idx].sum()), len(idx)
        lo, hi = clopper_pearson(k, n)
        bins.append({"n": n, "mean_predicted": float(p_ai[idx].mean()), "observed": k / n, "ci95": [lo, hi]})
    return bins


def expected_calibration_error(p_ai, labels, n_bins: int = 15) -> float:
    bins = reliability_bins(p_ai, labels, n_bins)
    total = sum(b["n"] for b in bins)
    return sum(b["n"] / total * abs(b["mean_predicted"] - b["observed"]) for b in bins)


def brier_score(p_ai, labels) -> float:
    p_ai, labels = np.asarray(p_ai, dtype=float), np.asarray(labels, dtype=float)
    return float(np.mean((p_ai - labels) ** 2))
