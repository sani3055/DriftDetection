"""Uncertainty estimates and paired effect sizes for experiment summaries."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon


def bootstrap_mean_ci(
    values: Iterable[float],
    seed: int = 42,
    n_bootstrap: int = 2000,
    confidence: float = 0.95,
) -> tuple[float, float, float]:
    """Return mean and percentile bootstrap CI, retaining deterministic seeds."""
    array = np.asarray(list(values), dtype=float)
    array = array[np.isfinite(array)]
    if len(array) == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    draws = rng.choice(array, size=(n_bootstrap, len(array)), replace=True).mean(axis=1)
    alpha = (1.0 - confidence) / 2.0
    return float(array.mean()), float(np.quantile(draws, alpha)), float(np.quantile(draws, 1.0 - alpha))


def paired_effect(
    left: Iterable[float],
    right: Iterable[float],
    seed: int = 42,
    n_bootstrap: int = 2000,
) -> dict[str, float | int | None]:
    """Summarize paired differences with bootstrap CI, standardized effect, and Wilcoxon p."""
    left_array = np.asarray(list(left), dtype=float)
    right_array = np.asarray(list(right), dtype=float)
    mask = np.isfinite(left_array) & np.isfinite(right_array)
    differences = left_array[mask] - right_array[mask]
    if len(differences) == 0:
        return {"n": 0, "mean_difference": None, "ci_low": None, "ci_high": None,
                "standardized_effect": None, "wilcoxon_statistic": None, "p_value": None}
    mean_difference, ci_low, ci_high = bootstrap_mean_ci(
        differences, seed=seed, n_bootstrap=n_bootstrap
    )
    standard_deviation = float(np.std(differences, ddof=1)) if len(differences) > 1 else 0.0
    standardized = mean_difference / standard_deviation if standard_deviation > 0 else 0.0
    if len(differences) < 2 or np.allclose(differences, 0.0):
        statistic, p_value = None, None
    else:
        test = wilcoxon(differences, zero_method="wilcox", alternative="two-sided")
        statistic, p_value = float(test.statistic), float(test.pvalue)
    return {
        "n": int(len(differences)),
        "mean_difference": float(mean_difference),
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
        "standardized_effect": float(standardized),
        "wilcoxon_statistic": statistic,
        "p_value": p_value,
    }


def benjamini_hochberg(p_values: Iterable[float | None]) -> list[float | None]:
    """Return Benjamini-Hochberg adjusted p-values in original row order."""
    values = list(p_values)
    valid = [(index, float(value)) for index, value in enumerate(values) if value is not None and np.isfinite(value)]
    adjusted: list[float | None] = [None] * len(values)
    if not valid:
        return adjusted
    ordered = sorted(valid, key=lambda item: item[1])
    running = 1.0
    total = len(ordered)
    for rank in range(total, 0, -1):
        index, value = ordered[rank - 1]
        running = min(running, value * total / rank)
        adjusted[index] = float(min(1.0, running))
    return adjusted


def adaptation_inference(results: pd.DataFrame, left: str = "dual_signal", right: str = "static") -> pd.DataFrame:
    """Compute paired uncertainty and effect sizes for the adaptation comparison."""
    rows = []
    for metric in ["f1", "false_positive_rate", "unnecessary_adaptation", "triggered"]:
        pivot = results.pivot_table(index=["scenario", "seed"], columns="policy", values=metric, aggfunc="mean")
        if left not in pivot or right not in pivot:
            continue
        paired = pivot[[left, right]].dropna()
        summary = paired_effect(paired[left], paired[right], seed=42 + len(rows))
        rows.append({"metric": metric, "left": left, "right": right, **summary})
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame["q_value_bh"] = benjamini_hochberg(frame["p_value"].tolist())
    return frame
