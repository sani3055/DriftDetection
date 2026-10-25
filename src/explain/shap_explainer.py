"""SHAP explanations for the Isolation Forest tree-path output."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import shap


def _as_2d(values: Any) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim == 1:
        return array.reshape(1, -1)
    return array


def explain_matrix(
    model: Any,
    matrix: np.ndarray,
    feature_names: tuple[str, ...] | list[str],
    check_additivity: bool = True,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Explain model tree-path output and return rows plus validation metadata."""
    matrix = np.asarray(matrix, dtype=np.float64)
    explainer = shap.TreeExplainer(model)
    raw_values = _as_2d(explainer.shap_values(matrix, check_additivity=check_additivity))
    expected = float(np.asarray(explainer.expected_value).reshape(-1)[0])

    # SHAP's Isolation Forest adapter explains the internal mean tree-path output.
    # This is monotonic with anomaly score but is not sklearn decision_function.
    explained_output = np.asarray(explainer.model.predict(matrix), dtype=np.float64).reshape(-1)
    reconstructed = expected + raw_values.sum(axis=1)
    residual = reconstructed - explained_output

    values = pd.DataFrame(raw_values, columns=list(feature_names))
    abs_values = values.abs().to_numpy()
    top_indices = abs_values.argmax(axis=1)
    top_features = [feature_names[index] for index in top_indices]
    negative_magnitudes = np.where(values.to_numpy() < 0, -values.to_numpy(), 0.0)
    negative_total = negative_magnitudes.sum(axis=1)
    top_negative = negative_magnitudes.max(axis=1)
    confidence = np.divide(
        top_negative,
        negative_total,
        out=np.zeros_like(top_negative),
        where=negative_total > 0,
    )
    values["top_absolute_feature"] = top_features
    values["attribution_confidence"] = confidence
    values["explained_tree_path_output"] = explained_output

    metadata = {
        "expected_value": expected,
        "max_additivity_residual": float(np.max(np.abs(residual))) if len(residual) else 0.0,
        "mean_additivity_residual": float(np.mean(np.abs(residual))) if len(residual) else 0.0,
        "n_rows": int(matrix.shape[0]),
        "n_features": int(matrix.shape[1]),
    }
    return values, metadata


def explain_score_sample(
    model: Any,
    score_sample: pd.DataFrame,
    feature_names: tuple[str, ...] | list[str],
    sample_per_window: int = 200,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Explain a deterministic prefix sample per monthly window."""
    selected = (
        score_sample.sort_values(["window_id", "row_index_within_stream"])
        .groupby("window_id", sort=True, group_keys=False)
        .head(sample_per_window)
        .reset_index(drop=True)
    )
    matrix = selected.loc[:, list(feature_names)].to_numpy(dtype=np.float64)
    explanations, metadata = explain_matrix(model, matrix, feature_names, check_additivity=True)
    result = pd.concat(
        [selected[["window_id", "row_index_within_stream", "anomaly_score", "is_anomaly"]], explanations],
        axis=1,
    )
    return result, metadata


def save_explanations(
    explanations: pd.DataFrame,
    metadata: dict[str, float],
    output_path: str | Path,
    metadata_path: str | Path,
) -> None:
    output_path = Path(output_path)
    metadata_path = Path(metadata_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    explanations.to_csv(output_path, index=False)
    metadata_path.write_text(pd.Series(metadata).to_json(indent=2) + "\n", encoding="utf-8")

