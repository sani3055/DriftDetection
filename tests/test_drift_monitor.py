from __future__ import annotations

import pandas as pd

from src.drift.drift_monitor import compute_feature_drift, compute_shap_drift, psi_from_counts


def test_psi_is_zero_for_identical_distributions() -> None:
    assert psi_from_counts({"a": 10, "b": 5}, {"a": 10, "b": 5}) < 1e-10


def test_feature_drift_detects_changed_category() -> None:
    features = pd.DataFrame([
        {"window_id": "2020-01", "event_count": 10, "error_rate": 0.1},
        {"window_id": "2020-02", "event_count": 20, "error_rate": 0.2},
    ])
    distributions = {
        "2020-01": {key: {"a": 10} for key in ["eventName", "eventSource", "awsRegion", "userIdentitytype", "errorCode"]},
        "2020-02": {key: {"b": 20} for key in ["eventName", "eventSource", "awsRegion", "userIdentitytype", "errorCode"]},
    }
    result = compute_feature_drift(features, distributions, ["2020-01"], scalar_features=["event_count", "error_rate"])
    assert float(result.loc[result["window_id"] == "2020-02", "feature_drift_score"].iloc[0]) > 0


def test_shap_drift_outputs_rank_overlap() -> None:
    rows = []
    for month, first in [("2020-01", 1.0), ("2020-02", 2.0)]:
        for _ in range(4):
            rows.append({"window_id": month, "a": first, "b": 0.1, "c": 0.01})
    result = compute_shap_drift(pd.DataFrame(rows), ["2020-01"], ["a", "b", "c"], top_k=2)
    assert set(result["window_id"]) == {"2020-01", "2020-02"}
    assert result["top_k_jaccard"].notna().all()
    assert result["mean_absolute_attribution_displacement"].notna().all()
