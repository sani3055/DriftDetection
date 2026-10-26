from __future__ import annotations

import pandas as pd

from src.drift.diagnosis import apply_coupled_diagnosis, apply_diagnosis, diagnose, diagnose_coupled, tune_thresholds, tune_coupled_thresholds


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


def test_coupling_rule_distinguishes_aligned_and_unaligned_drift() -> None:
    assert diagnose_coupled(1.0, 1.0, 0.9, 0.5, 0.5, 0.5) == "security_relevant_drift"
    assert diagnose_coupled(1.0, 1.0, 0.1, 0.5, 0.5, 0.5) == "review_required"
    assert diagnose_coupled(0.1, 1.0, 0.1, 0.5, 0.5, 0.5) == "hidden_model_instability"


def test_coupled_threshold_tuning_and_application() -> None:
    frame = pd.DataFrame([
        {"feature_drift_score": 0.1, "shap_drift_score": 0.1, "feature_attribution_coupling": 0.1, "ground_truth": "stable"},
        {"feature_drift_score": 1.0, "shap_drift_score": 0.1, "feature_attribution_coupling": 0.2, "ground_truth": "benign_region"},
        {"feature_drift_score": 1.0, "shap_drift_score": 1.0, "feature_attribution_coupling": 0.9, "ground_truth": "security_privilege"},
    ])
    thresholds = tune_coupled_thresholds(frame)
    result = apply_coupled_diagnosis(frame, thresholds)
    assert "coupled_diagnosis" in result
