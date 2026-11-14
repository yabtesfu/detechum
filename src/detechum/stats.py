"""Error rate statistics shared by the evaluation harness (docs/evaluation/plan.md §2)."""

import numpy as np
from scipy.stats import beta


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Exact two sided confidence interval for a binomial proportion k/n."""
    if n <= 0 or not 0 <= k <= n:
        raise ValueError(f"need 0 <= k <= n and n > 0, got k={k}, n={n}")
    lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return lo, hi


def flag_stats(scores: list[float], threshold: float) -> dict:
    """Share of scores strictly above `threshold`, with its 95% Clopper Pearson interval."""
    k = int(sum(s > threshold for s in scores))
    n = len(scores)
    lo, hi = clopper_pearson(k, n)
    return {"flagged": k, "n": n, "rate": k / n, "ci95": [lo, hi]}


def threshold_for_fpr(human_scores: list[float], target_fpr: float) -> float:
    """Smallest threshold that flags at most `target_fpr` of `human_scores` (flag means score > threshold)."""
    return float(np.quantile(np.asarray(human_scores), 1 - target_fpr, method="higher"))
