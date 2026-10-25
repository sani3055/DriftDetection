"""Adaptation decisions and protected retraining for controlled experiments."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest


POLICIES = ("static", "periodic", "feature_only", "shap_only", "dual_signal")


def should_adapt(
    policy: str,
    feature_score: float,
    shap_score: float,
    diagnosis: str,
    feature_threshold: float,
    shap_threshold: float,
    sequence_index: int,
    periodic_interval: int,
) -> bool:
    if policy not in POLICIES:
        raise ValueError(f"Unknown adaptation policy: {policy}")
    if policy == "static":
        return False
    if policy == "periodic":
        return sequence_index % periodic_interval == 0
    if policy == "feature_only":
        return feature_score >= feature_threshold
    if policy == "shap_only":
        return shap_score >= shap_threshold
    return diagnosis == "security_relevant_drift"


def protected_retrain(
    baseline_model: IsolationForest,
    replay_matrix: np.ndarray,
    current_matrix: np.ndarray,
    random_state: int,
    n_estimators: int = 50,
    contamination: float = 0.05,
    n_jobs: int = 1,
    minimum_normal_candidates: int = 10,
) -> tuple[IsolationForest, int]:
    """Retrain on replay plus baseline-model normal candidates only."""
    current_predictions = baseline_model.predict(current_matrix)
    normal_candidates = current_matrix[current_predictions == 1]
    if len(normal_candidates) < minimum_normal_candidates:
        return baseline_model, int(len(normal_candidates))
    training_matrix = np.vstack([replay_matrix, normal_candidates])
    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
        n_jobs=n_jobs,
    )
    model.fit(training_matrix)
    return model, int(len(normal_candidates))

