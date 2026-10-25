"""Metrics for row-level controlled perturbation and adaptation experiments."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score


def binary_detection_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "false_positive_rate": float(((y_true == 0) & (y_pred == 1)).sum() / max(1, (y_true == 0).sum())),
    }

