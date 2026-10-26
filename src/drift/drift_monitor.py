"""Distribution and attribution drift metrics for monthly CloudTrail windows."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable, Any

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr, wasserstein_distance


def _normalized_counts(counts: dict[str, int], keys: Iterable[str], epsilon: float) -> np.ndarray:
    values = np.asarray([float(counts.get(key, 0)) for key in keys], dtype=np.float64)
    values += epsilon
    return values / values.sum()


def psi_from_counts(reference: dict[str, int], current: dict[str, int], epsilon: float = 1e-6) -> float:
    keys = sorted(set(reference) | set(current))
    ref = _normalized_counts(reference, keys, epsilon)
    cur = _normalized_counts(current, keys, epsilon)
    return float(np.sum((cur - ref) * np.log(cur / ref)))


def js_from_counts(reference: dict[str, int], current: dict[str, int], epsilon: float = 1e-6) -> float:
    keys = sorted(set(reference) | set(current))
    ref = _normalized_counts(reference, keys, epsilon)
    cur = _normalized_counts(current, keys, epsilon)
    midpoint = 0.5 * (ref + cur)
    return float(0.5 * np.sum(ref * np.log(ref / midpoint)) + 0.5 * np.sum(cur * np.log(cur / midpoint)))


def _reference_distribution(
    distributions: dict[str, dict[str, dict[str, int]]],
    months: Iterable[str],
    key: str,
) -> dict[str, int]:
    result: dict[str, int] = {}
    for month in months:
        for category, count in distributions[month][key].items():
            result[category] = result.get(category, 0) + int(count)
    return result


def compute_feature_drift(
    monthly_features: pd.DataFrame,
    distributions: dict[str, dict[str, dict[str, int]]],
    reference_months: Iterable[str],
    epsilon: float = 1e-6,
    scalar_features: Iterable[str] = (),
) -> pd.DataFrame:
    """Compute categorical PSI/JS and scalar reference-relative drift."""
    reference_months = tuple(reference_months)
    distribution_keys = ["eventName", "eventSource", "awsRegion", "userIdentitytype", "errorCode"]
    reference_distributions = {
        key: _reference_distribution(distributions, reference_months, key)
        for key in distribution_keys
    }
    reference_rows = monthly_features[monthly_features["window_id"].isin(reference_months)]
    scalar_features = tuple(scalar_features)
    reference_stats = {}
    for feature in scalar_features:
        values = reference_rows[feature].astype(float).to_numpy()
        reference_stats[feature] = (float(values.mean()), float(values.std(ddof=0)))

    rows: list[dict[str, Any]] = []
    for _, row in monthly_features.sort_values("window_id").iterrows():
        month = str(row["window_id"])
        psi_values = {
            key: psi_from_counts(reference_distributions[key], distributions[month][key], epsilon)
            for key in distribution_keys
        }
        js_values = {
            key: js_from_counts(reference_distributions[key], distributions[month][key], epsilon)
            for key in distribution_keys
        }
        z_values = []
        for feature in scalar_features:
            mean, std = reference_stats[feature]
            scale = std if std > epsilon else max(abs(mean), 1.0)
            z_values.append(abs(float(row[feature]) - mean) / scale)
        scalar_shift = float(np.mean(np.minimum(z_values, 10.0))) if z_values else 0.0
        categorical_score = float(np.mean(list(psi_values.values())))
        rows.append({
            "window_id": month,
            "mean_psi": categorical_score,
            "max_psi": float(max(psi_values.values())),
            "mean_js": float(np.mean(list(js_values.values()))),
            "scalar_shift": scalar_shift,
            "feature_drift_score": categorical_score + scalar_shift / 10.0,
            **{f"psi_{key}": value for key, value in psi_values.items()},
            **{f"js_{key}": value for key, value in js_values.items()},
        })
    return pd.DataFrame(rows)


def _top_features(frame: pd.DataFrame, feature_names: list[str], top_k: int) -> list[str]:
    means = frame[feature_names].abs().mean().sort_values(ascending=False)
    return means.head(top_k).index.tolist()


COUPLING_FEATURES = ("eventName", "eventSource", "awsRegion", "userIdentitytype", "errorCode")


def _cosine_similarity(left: np.ndarray, right: np.ndarray, epsilon: float = 1e-12) -> float:
    left_norm = float(np.linalg.norm(left))
    right_norm = float(np.linalg.norm(right))
    if left_norm <= epsilon or right_norm <= epsilon:
        return 0.0
    return float(np.dot(left, right) / (left_norm * right_norm))


def _centered_alignment(left: np.ndarray, right: np.ndarray, epsilon: float = 1e-12) -> float:
    """Return positive-shifted Pearson alignment for two non-constant vectors."""
    if np.std(left) <= epsilon or np.std(right) <= epsilon:
        return 0.0
    correlation = float(np.corrcoef(left, right)[0, 1])
    if not np.isfinite(correlation):
        return 0.0
    return float(np.clip((correlation + 1.0) / 2.0, 0.0, 1.0))


def _rank_alignment(left: np.ndarray, right: np.ndarray, epsilon: float = 1e-12) -> float:
    """Return a [0, 1] rank agreement score that is robust to scale changes."""
    if np.std(left) <= epsilon or np.std(right) <= epsilon:
        return 0.0
    correlation = float(spearmanr(left, right).statistic)
    if not np.isfinite(correlation):
        return 0.0
    return float(np.clip((correlation + 1.0) / 2.0, 0.0, 1.0))


def compute_shap_drift(
    shap_sample: pd.DataFrame,
    reference_months: Iterable[str],
    feature_names: Iterable[str],
    top_k: int = 3,
) -> pd.DataFrame:
    """Compare signed SHAP distributions and top attribution rankings."""
    feature_names = list(feature_names)
    reference_months = tuple(reference_months)
    reference = shap_sample[shap_sample["window_id"].isin(reference_months)]
    rows: list[dict[str, Any]] = []
    reference_top = _top_features(reference, feature_names, top_k)
    reference_means = reference[feature_names].mean().to_numpy(dtype=np.float64)
    reference_abs_means = reference[feature_names].abs().mean().to_numpy(dtype=np.float64)
    reference_scales = reference[feature_names].std(ddof=0).to_numpy(dtype=np.float64) + 1e-9

    for month, current in shap_sample.groupby("window_id", sort=True):
        wasserstein = np.asarray([
            wasserstein_distance(reference[name].to_numpy(), current[name].to_numpy())
            for name in feature_names
        ])
        normalized_wasserstein = wasserstein / reference_scales
        current_means = current[feature_names].mean().to_numpy(dtype=np.float64)
        current_abs_means = current[feature_names].abs().mean().to_numpy(dtype=np.float64)
        current_top = _top_features(current, feature_names, top_k)
        union = len(set(reference_top) | set(current_top))
        jaccard = len(set(reference_top) & set(current_top)) / union if union else 1.0
        reference_order = np.argsort(-np.abs(reference_means))
        current_order = np.argsort(-np.abs(current_means))
        tau = kendalltau(reference_order, current_order).statistic
        tau = 0.0 if not np.isfinite(tau) else float(tau)
        rows.append({
            "window_id": str(month),
            "mean_wasserstein": float(normalized_wasserstein.mean()),
            "max_wasserstein": float(normalized_wasserstein.max()),
            "top_k_jaccard": float(jaccard),
            "top_k_kendall_tau": tau,
            "mean_signed_attribution_shift": float(np.mean(np.abs(current_means - reference_means))),
            "mean_absolute_attribution_displacement": float(
                np.mean(np.abs(current_abs_means - reference_abs_means))
            ),
            "shap_drift_score": float(
                normalized_wasserstein.mean() + (1.0 - jaccard) + (1.0 - ((tau + 1.0) / 2.0))
            ),
            "reference_top_features": ",".join(reference_top),
            "current_top_features": ",".join(current_top),
            **{
                f"attribution_displacement_{name}": float(abs(current_abs - reference_abs))
                for name, current_abs, reference_abs in zip(
                    feature_names, current_abs_means, reference_abs_means
                )
            },
        })
    return pd.DataFrame(rows)


def compute_drift_coupling(
    feature_drift: pd.DataFrame,
    shap_drift: pd.DataFrame,
    feature_names: Iterable[str] = COUPLING_FEATURES,
) -> pd.DataFrame:
    """Measure whether distributionally changed categorical features also changed model attribution.

    The score is a cosine similarity between the per-feature PSI vector and the per-feature absolute
    SHAP-displacement vector for the shared CloudTrail categorical features. It is label-free and
    therefore safe for observational data and validation/test windows.
    """
    feature_names = tuple(feature_names)
    merged = feature_drift.merge(shap_drift, on="window_id", how="inner")
    rows = []
    for _, row in merged.iterrows():
        feature_vector = np.asarray(
            [float(row.get(f"psi_{name}", 0.0)) for name in feature_names], dtype=np.float64
        )
        attribution_vector = np.asarray(
            [float(row.get(f"attribution_displacement_{name}", 0.0)) for name in feature_names],
            dtype=np.float64,
        )
        coupling = _cosine_similarity(feature_vector, attribution_vector)
        feature_mass = float(np.linalg.norm(feature_vector))
        attribution_mass = float(np.linalg.norm(attribution_vector))
        centered_alignment = _centered_alignment(feature_vector, attribution_vector)
        rank_alignment = _rank_alignment(feature_vector, attribution_vector)
        rows.append({
            "window_id": str(row["window_id"]),
            "feature_attribution_coupling": coupling,
            "coupling_centered_alignment": centered_alignment,
            "coupling_rank_alignment": rank_alignment,
            # A conservative ensemble prevents one alignment definition from
            # dominating when feature and attribution vectors have different scales.
            "coupling_conservative_score": min(coupling, centered_alignment),
            "coupling_feature_mass": feature_mass,
            "coupling_attribution_mass": attribution_mass,
            "coupling_top_feature": feature_names[int(np.argmax(feature_vector))]
            if feature_mass > 0
            else "none",
        })
    return pd.DataFrame(rows)


def save_drift_outputs(
    feature_drift: pd.DataFrame,
    shap_drift: pd.DataFrame,
    output_dir: str | Path,
) -> pd.DataFrame:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    coupling = compute_drift_coupling(feature_drift, shap_drift)
    combined = feature_drift.merge(shap_drift, on="window_id", how="inner").merge(coupling, on="window_id", how="left")
    feature_drift.to_csv(output_dir / "feature_drift.csv", index=False)
    shap_drift.to_csv(output_dir / "shap_drift.csv", index=False)
    coupling.to_csv(output_dir / "coupling_drift.csv", index=False)
    combined.to_csv(output_dir / "combined_drift.csv", index=False)
    return combined
