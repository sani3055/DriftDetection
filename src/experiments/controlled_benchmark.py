"""Controlled semantic perturbations built from real training-window samples."""

from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np
import pandas as pd

from src.drift.diagnosis import apply_coupled_diagnosis, apply_diagnosis, tune_coupled_thresholds, tune_thresholds
from src.drift.drift_monitor import compute_drift_coupling, compute_feature_drift, compute_shap_drift
from src.explain.shap_explainer import explain_matrix


CATEGORY_COLUMNS = {
    "eventName": 0,
    "eventSource": 1,
    "awsRegion": 2,
    "userIdentitytype": 3,
    "errorCode": 4,
}


def _set_fraction(matrix: np.ndarray, column: int, value: float, fraction: float, rng: np.random.Generator) -> np.ndarray:
    count = max(1, int(len(matrix) * fraction))
    indices = rng.choice(len(matrix), size=count, replace=False)
    matrix[indices, column] = value
    return indices


def perturb_sample(
    base: np.ndarray,
    scenario: str,
    category_maps: dict[str, dict[str, int]],
    intensity: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Apply semantic scenario changes without using scenario labels in the model."""
    current = np.array(base, dtype=np.float64, copy=True)
    lookup = lambda column, value: float(category_maps[column].get(value, -1))
    if scenario == "stable":
        return current
    if scenario == "benign_region":
        _set_fraction(current, CATEGORY_COLUMNS["awsRegion"], lookup("awsRegion", "ap-southeast-1"), intensity, rng)
    elif scenario == "benign_identity":
        _set_fraction(current, CATEGORY_COLUMNS["userIdentitytype"], lookup("userIdentitytype", "AWSService"), intensity, rng)
    elif scenario == "benign_service":
        _set_fraction(current, CATEGORY_COLUMNS["eventSource"], lookup("eventSource", "lambda.amazonaws.com"), intensity, rng)
    elif scenario == "security_privilege":
        _set_fraction(current, CATEGORY_COLUMNS["eventName"], lookup("eventName", "AttachUserPolicy"), intensity, rng)
        _set_fraction(current, CATEGORY_COLUMNS["userIdentitytype"], lookup("userIdentitytype", "Root"), intensity / 2, rng)
    elif scenario == "security_defense":
        _set_fraction(current, CATEGORY_COLUMNS["eventName"], lookup("eventName", "DeleteTrail"), intensity, rng)
        _set_fraction(current, CATEGORY_COLUMNS["eventSource"], lookup("eventSource", "cloudtrail.amazonaws.com"), intensity / 2, rng)
    elif scenario == "security_credential":
        _set_fraction(current, CATEGORY_COLUMNS["eventName"], lookup("eventName", "AssumeRole"), intensity, rng)
        _set_fraction(current, CATEGORY_COLUMNS["awsRegion"], lookup("awsRegion", "ap-southeast-1"), intensity / 2, rng)
    else:
        raise ValueError(f"Unknown scenario: {scenario}")
    return current


def perturb_sample_with_mask(
    base: np.ndarray,
    scenario: str,
    category_maps: dict[str, dict[str, int]],
    intensity: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Return a perturbation and the rows changed by the controlled scenario."""
    current = np.array(base, dtype=np.float64, copy=True)
    changed = np.zeros(len(current), dtype=bool)
    lookup = lambda column, value: float(category_maps[column].get(value, -1))
    operations = {
        "benign_region": [("awsRegion", "ap-southeast-1", intensity)],
        "benign_identity": [("userIdentitytype", "AWSService", intensity)],
        "benign_service": [("eventSource", "lambda.amazonaws.com", intensity)],
        "security_privilege": [("eventName", "AttachUserPolicy", intensity), ("userIdentitytype", "Root", intensity / 2)],
        "security_defense": [("eventName", "DeleteTrail", intensity), ("eventSource", "cloudtrail.amazonaws.com", intensity / 2)],
        "security_credential": [("eventName", "AssumeRole", intensity), ("awsRegion", "ap-southeast-1", intensity / 2)],
    }
    if scenario == "stable":
        return current, changed
    if scenario not in operations:
        raise ValueError(f"Unknown scenario: {scenario}")
    for column_name, value_name, fraction in operations[scenario]:
        indices = _set_fraction(current, CATEGORY_COLUMNS[column_name], lookup(column_name, value_name), fraction, rng)
        changed[indices] = True
    return current, changed


def _distributions(matrix: np.ndarray) -> dict[str, dict[str, int]]:
    result = {}
    for name, column in CATEGORY_COLUMNS.items():
        result[name] = {str(int(key)): int(value) for key, value in Counter(matrix[:, column].astype(int)).items()}
    return result


def scenario_signals(
    model: Any,
    category_maps: dict[str, dict[str, int]],
    base: np.ndarray,
    scenario: str,
    seed: int,
    intensity: float,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    current = perturb_sample(base, scenario, category_maps, intensity, rng)
    reference_distributions = _distributions(base)
    current_distributions = _distributions(current)
    feature_names = list(model.feature_names_in_) if hasattr(model, "feature_names_in_") else None
    # The model artifact uses the stable seven-column contract.
    model_feature_names = ("eventName", "eventSource", "awsRegion", "userIdentitytype", "errorCode", "requestParametersinstanceType", "isRoot")
    ref_frame = pd.DataFrame([{ "window_id": "reference", "event_count": len(base), "high_risk_event_rate": 0.0 }])
    cur_frame = pd.DataFrame([{ "window_id": "scenario", "event_count": len(current), "high_risk_event_rate": 0.0 }])
    feature_frame = pd.concat([ref_frame, cur_frame], ignore_index=True)
    distribution_frame = {
        "reference": reference_distributions,
        "scenario": current_distributions,
    }
    feature_drift = compute_feature_drift(
        feature_frame,
        distribution_frame,
        ["reference"],
        scalar_features=["event_count", "high_risk_event_rate"],
    )
    reference_shap, _ = explain_matrix(model, base, model_feature_names)
    current_shap, _ = explain_matrix(model, current, model_feature_names)
    reference_shap["window_id"] = "reference"
    current_shap["window_id"] = "scenario"
    shap_frame = pd.concat([reference_shap, current_shap], ignore_index=True)
    shap_drift = compute_shap_drift(shap_frame, ["reference"], model_feature_names, top_k=3)
    coupling = compute_drift_coupling(feature_drift, shap_drift)
    feature_row = feature_drift[feature_drift["window_id"] == "scenario"].iloc[0]
    shap_row = shap_drift[shap_drift["window_id"] == "scenario"].iloc[0]
    return {
        "scenario": scenario,
        "seed": seed,
        "feature_drift_score": float(feature_row["feature_drift_score"]),
        "shap_drift_score": float(shap_row["shap_drift_score"]),
        "mean_psi": float(feature_row["mean_psi"]),
        "mean_wasserstein": float(shap_row["mean_wasserstein"]),
        "top_k_jaccard": float(shap_row["top_k_jaccard"]),
        "feature_attribution_coupling": float(coupling.loc[coupling["window_id"] == "scenario", "feature_attribution_coupling"].iloc[0]),
    }


def run_benchmark(
    model: Any,
    category_maps: dict[str, dict[str, int]],
    base: np.ndarray,
    scenarios: list[str],
    validation_seeds: list[int],
    test_seeds: list[int],
    intensity: float,
) -> tuple[pd.DataFrame, dict[str, float], pd.DataFrame]:
    rows = []
    for split, seeds in [("validation", validation_seeds), ("test", test_seeds)]:
        for seed in seeds:
            for scenario in scenarios:
                row = scenario_signals(model, category_maps, base, scenario, seed, intensity)
                row["split"] = split
                row["ground_truth"] = scenario
                rows.append(row)
    frame = pd.DataFrame(rows)
    validation = frame[frame["split"] == "validation"]
    thresholds = tune_thresholds(validation)
    coupled_thresholds = tune_coupled_thresholds(validation)
    thresholds.update({"coupling_threshold": coupled_thresholds["coupling_threshold"], "coupled_validation_macro_f1": coupled_thresholds["validation_macro_f1"]})
    diagnosed = apply_diagnosis(frame, thresholds)
    diagnosed = apply_coupled_diagnosis(diagnosed, thresholds)
    return frame, thresholds, diagnosed
