"""Interpretable dual-signal drift diagnosis and validation-only threshold tuning."""

from __future__ import annotations

from itertools import product
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score


def diagnose(feature_score: float, shap_score: float, feature_threshold: float, shap_threshold: float) -> str:
    feature_high = feature_score >= feature_threshold
    shap_high = shap_score >= shap_threshold
    if not feature_high and not shap_high:
        return "stable"
    if feature_high and not shap_high:
        return "benign_drift"
    if feature_high and shap_high:
        return "security_relevant_drift"
    return "review_required"


def _labels(frame: pd.DataFrame) -> list[str]:
    return frame["ground_truth"].replace({"benign_region": "benign_drift", "benign_identity": "benign_drift", "benign_service": "benign_drift", "security_privilege": "security_relevant_drift", "security_defense": "security_relevant_drift", "security_credential": "security_relevant_drift", "stable": "stable"}).tolist()


def tune_thresholds(validation: pd.DataFrame) -> dict[str, float]:
    """Tune both thresholds on validation scenarios only."""
    feature_candidates = np.unique(np.quantile(validation["feature_drift_score"], [0.2, 0.35, 0.5, 0.65, 0.8, 0.9]))
    shap_candidates = np.unique(np.quantile(validation["shap_drift_score"], [0.2, 0.35, 0.5, 0.65, 0.8, 0.9]))
    truth = _labels(validation)
    best = None
    for feature_threshold, shap_threshold in product(feature_candidates, shap_candidates):
        predictions = [
            diagnose(f, s, float(feature_threshold), float(shap_threshold))
            for f, s in zip(validation["feature_drift_score"], validation["shap_drift_score"])
        ]
        score = f1_score(truth, predictions, labels=["stable", "benign_drift", "security_relevant_drift"], average="macro", zero_division=0)
        candidate = (float(score), float(feature_threshold), float(shap_threshold))
        if best is None or candidate > best:
            best = candidate
    assert best is not None
    return {
        "feature_threshold": best[1],
        "shap_threshold": best[2],
        "validation_macro_f1": best[0],
    }


def apply_diagnosis(frame: pd.DataFrame, thresholds: dict[str, float]) -> pd.DataFrame:
    result = frame.copy()
    result["diagnosis"] = [
        diagnose(f, s, thresholds["feature_threshold"], thresholds["shap_threshold"])
        for f, s in zip(result["feature_drift_score"], result["shap_drift_score"])
    ]
    return result

