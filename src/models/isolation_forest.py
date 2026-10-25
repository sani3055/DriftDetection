"""Chronological event-level Isolation Forest training and scoring."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from src.data.temporal_protocol import normalize_month
from src.features.event_features import (
    CATEGORICAL_FEATURES,
    FEATURE_NAMES,
    clean_event_frame,
    encode_events,
    fit_category_maps,
)


def _read_chunks(path: str | Path, chunk_size: int):
    usecols = ["eventTime", *CATEGORICAL_FEATURES]
    for chunk in pd.read_csv(path, usecols=usecols, chunksize=chunk_size, dtype=str):
        chunk["eventTime"] = chunk["eventTime"].map(normalize_month)
        yield clean_event_frame(chunk)


def _select_months(frame: pd.DataFrame, months: set[str]) -> pd.DataFrame:
    return frame[frame["eventTime"].isin(months)].copy()


def fit_category_maps_from_csv(
    path: str | Path,
    train_months: Iterable[str],
    chunk_size: int = 100000,
) -> dict[str, dict[str, int]]:
    """Fit category vocabularies using only chronological training months."""
    train_months = set(train_months)
    values = {column: set() for column in CATEGORICAL_FEATURES}
    for frame in _read_chunks(path, chunk_size):
        selected = _select_months(frame, train_months)
        for column in CATEGORICAL_FEATURES:
            values[column].update(selected[column].tolist())
    maps: dict[str, dict[str, int]] = {}
    for column in CATEGORICAL_FEATURES:
        maps[column] = {value: index for index, value in enumerate(sorted(values[column]))}
    return maps


def load_training_matrix(
    path: str | Path,
    train_months: Iterable[str],
    category_maps: dict[str, dict[str, int]],
    chunk_size: int = 100000,
) -> np.ndarray:
    train_months = set(train_months)
    matrices = []
    for frame in _read_chunks(path, chunk_size):
        selected = _select_months(frame, train_months)
        if not selected.empty:
            matrices.append(encode_events(selected, category_maps))
    if not matrices:
        raise ValueError("No training rows found for the requested months")
    return np.vstack(matrices)


def train_detector(
    path: str | Path,
    train_months: Iterable[str],
    output_path: str | Path,
    n_estimators: int = 100,
    contamination: float = 0.05,
    max_samples: str | int = "auto",
    random_state: int = 42,
    n_jobs: int = -1,
    chunk_size: int = 100000,
) -> dict:
    """Fit and save a detector with a train-only category contract."""
    train_months = tuple(train_months)
    category_maps = fit_category_maps_from_csv(path, train_months, chunk_size)
    matrix = load_training_matrix(path, train_months, category_maps, chunk_size)
    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        max_samples=max_samples,
        random_state=random_state,
        n_jobs=n_jobs,
    )
    model.fit(matrix)
    artifact = {
        "model": model,
        "category_maps": category_maps,
        "feature_names": FEATURE_NAMES,
        "categorical_features": CATEGORICAL_FEATURES,
        "train_months": train_months,
        "training_rows": int(matrix.shape[0]),
        "random_state": random_state,
    }
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, output_path)
    return artifact


def score_csv(
    path: str | Path,
    artifact: dict,
    output_path: str | Path,
    sample_per_window: int = 1000,
    chunk_size: int = 100000,
) -> pd.DataFrame:
    """Score a deterministic prefix sample from every month and save results."""
    model = artifact["model"]
    category_maps = artifact["category_maps"]
    sampled: dict[str, list[dict]] = {}
    for frame in _read_chunks(path, chunk_size):
        encoded = encode_events(frame, category_maps)
        scores = model.decision_function(encoded)
        predictions = model.predict(encoded)
        for index, month in enumerate(frame["eventTime"].tolist()):
            rows = sampled.setdefault(month, [])
            if len(rows) >= sample_per_window:
                continue
            rows.append({
                "window_id": month,
                "row_index_within_stream": len(rows),
                "anomaly_score": float(scores[index]),
                "is_anomaly": bool(predictions[index] == -1),
                **{name: float(encoded[index, col]) for col, name in enumerate(artifact["feature_names"])},
            })

    rows = [row for month in sorted(sampled) for row in sampled[month]]
    result = pd.DataFrame(rows)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    return result


def save_training_metadata(path: str | Path, artifact: dict) -> None:
    metadata = {
        "feature_names": list(artifact["feature_names"]),
        "train_months": list(artifact["train_months"]),
        "training_rows": artifact["training_rows"],
        "random_state": artifact["random_state"],
        "category_counts": {key: len(value) for key, value in artifact["category_maps"].items()},
    }
    Path(path).write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

