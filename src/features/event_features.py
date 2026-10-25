"""Leakage-safe event-level encoding for the month-level CloudTrail corpus."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd


CATEGORICAL_FEATURES = (
    "eventName",
    "eventSource",
    "awsRegion",
    "userIdentitytype",
    "errorCode",
    "requestParametersinstanceType",
)
FEATURE_NAMES = CATEGORICAL_FEATURES + ("isRoot",)
REQUIRED_COLUMNS = ("eventTime",) + CATEGORICAL_FEATURES


def fit_category_maps(frame: pd.DataFrame) -> dict[str, dict[str, int]]:
    """Fit deterministic category maps on training data only."""
    maps: dict[str, dict[str, int]] = {}
    for column in CATEGORICAL_FEATURES:
        values = sorted(frame[column].fillna("Unknown").astype(str).unique())
        maps[column] = {value: index for index, value in enumerate(values)}
    return maps


def encode_events(
    frame: pd.DataFrame,
    category_maps: Mapping[str, Mapping[str, int]],
) -> np.ndarray:
    """Encode events with unknown categories mapped to -1."""
    encoded = []
    for column in CATEGORICAL_FEATURES:
        mapping = category_maps[column]
        values = frame[column].fillna("Unknown").astype(str)
        encoded.append(values.map(mapping).fillna(-1).to_numpy(dtype=np.float64))
    identity_type = frame["userIdentitytype"].fillna("Unknown").astype(str)
    encoded.append((identity_type == "Root").to_numpy(dtype=np.float64))
    return np.column_stack(encoded)


def clean_event_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with required fields normalized as strings."""
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing event feature columns: {missing}")
    cleaned = frame.loc[:, REQUIRED_COLUMNS].copy()
    for column in CATEGORICAL_FEATURES:
        cleaned[column] = cleaned[column].fillna("Unknown").astype(str)
    return cleaned

