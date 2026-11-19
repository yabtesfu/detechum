"""Conformal abstention: can a label be given at a stated error rate? (docs/design/architecture.md §3)

Split conformal prediction, conditional on the class and on a length band. A new text is compared
with the calibration texts of its own band, one class at a time:

* "human" leaves the prediction set when human calibration texts rarely score this high;
* "AI" leaves the prediction set when AI calibration texts rarely score this low.

A label is given only when exactly one class remains (see `detechum.verdict.decide_verdict`).

Guarantee: if a new text is exchangeable with the calibration texts of its class and band, its true
class is missing from the set with probability at most the alpha of that class. The probability is
over the draw of the calibration texts and of the new text together. Nothing is promised for a text
that differs from the calibration texts in a way other than length, such as another language or
genre, and the layer does not detect such a text.

A class can leave the set only if the band holds enough calibration texts of that class (99 for an
alpha of 0.01, see `min_calibration_texts`). A thin band therefore gives no label, in place of a
label whose error rate nothing supports.

Writer group and domain are not conditioned on, because they are unknown for a new text.
"""

import math
from dataclasses import dataclass

import numpy as np


def min_calibration_texts(alpha: float) -> int:
    """Smallest number of calibration texts of a class with which that class can leave the set."""
    n = max(0, math.floor(1 / alpha) - 2)
    while 1 / (n + 1) > alpha:
        n += 1
    return n


@dataclass(frozen=True)
class ConformalResult:
    """The comparison of one text with the calibration texts of its length band."""

    min_words: int
    max_words: int | None    # exclusive; None for the open ended last band
    n_human: int
    n_ai: int
    human_at_or_above: int   # human calibration texts that score at least as high as the text
    ai_at_or_below: int      # AI calibration texts that score at least as low
    alpha_human: float
    alpha_ai: float

    @property
    def p_human(self) -> float:
        return (self.human_at_or_above + 1) / (self.n_human + 1)

    @property
    def p_ai(self) -> float:
        return (self.ai_at_or_below + 1) / (self.n_ai + 1)

    @property
    def human_in_set(self) -> bool:
        return self.p_human > self.alpha_human

    @property
    def ai_in_set(self) -> bool:
        return self.p_ai > self.alpha_ai

    @property
    def can_exclude_human(self) -> bool:
        """False when the band has too few human texts for any score to rule out a human writer."""
        return self.n_human >= min_calibration_texts(self.alpha_human)

    @property
    def can_exclude_ai(self) -> bool:
        return self.n_ai >= min_calibration_texts(self.alpha_ai)

    def to_dict(self) -> dict:
        return {"band_words": [self.min_words, self.max_words], "n_human": self.n_human, "n_ai": self.n_ai,
                "human_at_or_above": self.human_at_or_above, "ai_at_or_below": self.ai_at_or_below,
                "alpha_human": self.alpha_human, "alpha_ai": self.alpha_ai,
                "p_human": self.p_human, "p_ai": self.p_ai,
                "human_in_set": self.human_in_set, "ai_in_set": self.ai_in_set}


@dataclass(frozen=True, eq=False)
class ConformalLayer:
    """Calibration scores per class and length band, with the error rate tolerated for each class.

    Band i covers texts of `edges[i]` words up to, and not including, `edges[i + 1]`. The last band
    has no upper limit. `alpha_human` bounds the share of human texts for which "human" is ruled
    out, which is the share that can be labelled as AI. `alpha_ai` is the same for AI texts.
    """

    edges: tuple[int, ...]
    human_scores: tuple[np.ndarray, ...]   # one sorted array per band
    ai_scores: tuple[np.ndarray, ...]
    alpha_human: float
    alpha_ai: float

    def assess(self, score: float, n_words: int) -> ConformalResult | None:
        """Compare one text with its band. Returns None for a text shorter than the first band."""
        if not math.isfinite(score):
            raise ValueError(f"score must be finite, got {score}")
        band = int(np.searchsorted(self.edges, n_words, side="right")) - 1
        if band < 0:
            return None
        human, ai = self.human_scores[band], self.ai_scores[band]
        return ConformalResult(
            min_words=self.edges[band], max_words=self.edges[band + 1] if band + 1 < len(self.edges) else None,
            n_human=len(human), n_ai=len(ai),
            # Ties count as "at least as extreme", which can only keep a class in the set.
            human_at_or_above=len(human) - int(np.searchsorted(human, score, side="left")),
            ai_at_or_below=int(np.searchsorted(ai, score, side="right")),
            alpha_human=self.alpha_human, alpha_ai=self.alpha_ai)

    def to_dict(self) -> dict:
        return {"edges": list(self.edges), "alpha_human": self.alpha_human, "alpha_ai": self.alpha_ai,
                "human_scores": [s.tolist() for s in self.human_scores],
                "ai_scores": [s.tolist() for s in self.ai_scores]}

    @classmethod
    def from_dict(cls, data: dict) -> "ConformalLayer":
        layer = cls(edges=tuple(int(e) for e in data["edges"]),
                    human_scores=tuple(np.sort(np.asarray(s, dtype=float)) for s in data["human_scores"]),
                    ai_scores=tuple(np.sort(np.asarray(s, dtype=float)) for s in data["ai_scores"]),
                    alpha_human=float(data["alpha_human"]), alpha_ai=float(data["alpha_ai"]))
        _validate(layer)
        return layer


def _validate(layer: ConformalLayer) -> None:
    edges = layer.edges
    if not edges or any(a >= b for a, b in zip(edges, edges[1:])) or edges[0] < 0:
        raise ValueError(f"band edges must be non negative and strictly increasing, got {edges}")
    if not len(layer.human_scores) == len(layer.ai_scores) == len(edges):
        raise ValueError("each band needs one array of human scores and one of AI scores")
    for name, alpha in (("alpha_human", layer.alpha_human), ("alpha_ai", layer.alpha_ai)):
        if not 0.0 < alpha < 1.0:
            raise ValueError(f"{name} must be in (0, 1), got {alpha}")
    if not all(np.all(np.isfinite(s)) for s in (*layer.human_scores, *layer.ai_scores)):
        raise ValueError("calibration scores must be finite")


def fit_conformal(scores, labels, n_words, *, edges, alpha_human: float, alpha_ai: float) -> ConformalLayer:
    """Sort labelled calibration scores into length bands.

    `labels` are 1 for AI and 0 for human. Texts shorter than `edges[0]` are left out. The texts must
    not have been used to fit the scorer, or the guarantee does not hold.

    Raises ValueError if the inputs are malformed.
    """
    scores, labels, n_words = np.asarray(scores, dtype=float), np.asarray(labels), np.asarray(n_words)
    if scores.ndim != 1 or not scores.shape == labels.shape == n_words.shape:
        raise ValueError("scores, labels and n_words must be one dimensional and of equal length")
    if not np.all((labels == 0) | (labels == 1)):
        raise ValueError("labels must be 0 (human) or 1 (AI)")
    edges = tuple(int(e) for e in edges)
    band = np.searchsorted(edges, n_words, side="right") - 1
    layer = ConformalLayer(
        edges=edges,
        human_scores=tuple(np.sort(scores[(band == i) & (labels == 0)]) for i in range(len(edges))),
        ai_scores=tuple(np.sort(scores[(band == i) & (labels == 1)]) for i in range(len(edges))),
        alpha_human=alpha_human, alpha_ai=alpha_ai)
    _validate(layer)
    return layer
