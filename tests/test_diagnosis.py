from __future__ import annotations

import pandas as pd

from src.drift.diagnosis import apply_diagnosis, diagnose, tune_thresholds


def test_dual_signal_rule() -> None:
    assert diagnose(0.1, 0.1, 0.5, 0.5) == "stable"
    assert diagnose(1.0, 0.1, 0.5, 0.5) == "benign_drift"
    assert diagnose(1.0, 1.0, 0.5, 0.5) == "security_relevant_drift"
    assert diagnose(0.1, 1.0, 0.5, 0.5) == "review_required"


def test_threshold_tuning_uses_validation_frame() -> None:
    frame = pd.DataFrame([
        {"feature_drift_score": 0.1, "shap_drift_score": 0.1, "ground_truth": "stable"},
        {"feature_drift_score": 1.0, "shap_drift_score": 0.1, "ground_truth": "benign_region"},
        {"feature_drift_score": 1.0, "shap_drift_score": 1.0, "ground_truth": "security_privilege"},
    ])
    thresholds = tune_thresholds(frame)
    result = apply_diagnosis(frame, thresholds)
    assert set(result["diagnosis"]).issubset({"stable", "benign_drift", "security_relevant_drift", "review_required"})

