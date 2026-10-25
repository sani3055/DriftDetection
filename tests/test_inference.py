from __future__ import annotations

import pandas as pd

from src.evaluation.inference import adaptation_inference, benjamini_hochberg, bootstrap_mean_ci


def test_bootstrap_is_deterministic_and_ordered() -> None:
    values = [0.1, 0.2, 0.3, 0.4]
    first = bootstrap_mean_ci(values, seed=7, n_bootstrap=200)
    second = bootstrap_mean_ci(values, seed=7, n_bootstrap=200)
    assert first == second
    assert first[1] <= first[0] <= first[2]


def test_benjamini_hochberg_preserves_missing_values() -> None:
    adjusted = benjamini_hochberg([0.01, None, 0.04, 0.2])
    assert adjusted[1] is None
    assert adjusted[0] <= adjusted[2] <= adjusted[3]


def test_adaptation_inference_returns_effect_sizes() -> None:
    rows = []
    for seed in range(4):
        for policy, f1, fpr in [("dual_signal", 0.8, 0.1), ("static", 0.5, 0.3)]:
            rows.append({
                "scenario": "security_privilege",
                "seed": seed,
                "policy": policy,
                "f1": f1 + seed * 0.001,
                "false_positive_rate": fpr,
                "unnecessary_adaptation": 0,
                "triggered": 1,
            })
    result = adaptation_inference(pd.DataFrame(rows))
    assert set(["metric", "mean_difference", "ci_low", "ci_high", "q_value_bh"]).issubset(result.columns)
    assert float(result.loc[result["metric"] == "f1", "mean_difference"].iloc[0]) > 0
