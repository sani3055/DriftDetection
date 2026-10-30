"""Versioned native-time, test-then-update benchmark; legacy results stay unchanged.

Labels may enter only metric computation and integrity checks, never encoding,
window construction, calibration, prediction, candidate screening or update gates.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, rankdata, wasserstein_distance
from sklearn.ensemble import IsolationForest

from src.drift.drift_monitor import psi_from_counts

FEATURES = (
    "eventName", "eventSource", "awsRegion", "userIdentitytype", "errorCode",
    "requestParametersinstanceType", "isRoot",
)
POLICIES = (
    "static", "periodic", "feature_only", "shap_only", "dual_signal",
    "coupled_signal", "conservative_coupled_signal",
)


def ordered_unique(records: list[dict]) -> tuple[list[dict], int]:
    """Deduplicate by event ID, fail on inconsistent labels, and order without labels."""
    seen: dict[str, dict] = {}
    for record in records:
        identifier = str(record.get("eventID") or "")
        if not identifier:
            raise ValueError("Every event needs an eventID for the leakage audit")
        pd.Timestamp(record["eventTime"])  # Fail rather than silently invent time.
        if identifier in seen:
            previous = seen[identifier]
            if previous.get("should_sample", False) != record.get("should_sample", False):
                raise ValueError("Conflicting labels for duplicate event ID")
            if previous["eventTime"] != record["eventTime"] or normalise(previous) != normalise(record):
                raise ValueError("Conflicting features/time for duplicate event ID")
        else:
            seen[identifier] = record
    ordered = sorted(seen.values(), key=lambda row: (pd.Timestamp(row["eventTime"]), str(row["eventID"])))
    return ordered, len(records) - len(ordered)


def normalise(record: dict) -> dict[str, str | int]:
    identity = record.get("userIdentity") or {}
    request = record.get("requestParameters") or {}
    kind = str(identity.get("type") or "Unknown")
    return {
        "eventName": str(record.get("eventName") or "Unknown"),
        "eventSource": str(record.get("eventSource") or "Unknown"),
        "awsRegion": str(record.get("awsRegion") or "Unknown"),
        "userIdentitytype": kind,
        "errorCode": str(record.get("errorCode") or "NoError"),
        "requestParametersinstanceType": str(request.get("instanceType") or "NotApplicable"),
        "isRoot": int(kind == "Root" or ":root" in str(identity.get("arn") or "")),
    }


def fit_maps(records: list[dict]) -> dict[str, dict[str, int]]:
    rows = [normalise(row) for row in records]
    return {name: {value: i for i, value in enumerate(sorted({str(row[name]) for row in rows}))}
            for name in FEATURES if name != "isRoot"}


def encode(records: list[dict], maps: dict[str, dict[str, int]]) -> np.ndarray:
    return np.asarray([
        [float(row[name]) if name == "isRoot" else maps[name].get(str(row[name]), -1)
         for name in FEATURES]
        for row in map(normalise, records)
    ], dtype=float).reshape(-1, len(FEATURES))


def windows(records: list[dict], size: int) -> Iterable[list[dict]]:
    if size < 1:
        raise ValueError("Window size must be positive")
    for start in range(0, len(records), size):
        yield records[start:start + size]


def aligned_rank_tau(reference: np.ndarray, current: np.ndarray) -> float:
    """Kendall tau-b between feature-aligned ranks of mean absolute attribution."""
    reference = np.asarray(reference, dtype=float)
    current = np.asarray(current, dtype=float)
    if reference.shape != current.shape or reference.ndim != 1 or not len(reference):
        raise ValueError("Attribution vectors must be nonempty, aligned and one-dimensional")
    if np.array_equal(reference, current):
        return 1.0
    tau = kendalltau(rankdata(-reference), rankdata(-current)).statistic
    return float(tau) if np.isfinite(tau) else 0.0


def _cosine(left: np.ndarray, right: np.ndarray) -> float:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    return float(np.clip(np.dot(left, right) / denominator, 0, 1)) if denominator > 1e-12 else 0.0


def drift_signals(reference: np.ndarray, current: np.ndarray,
                  reference_shap: np.ndarray, current_shap: np.ndarray) -> dict[str, float]:
    if reference.shape[1] != len(FEATURES) or current.shape[1] != len(FEATURES):
        raise ValueError("Feature contract mismatch")
    psi = np.asarray([
        psi_from_counts(dict(Counter(reference[:, i].tolist())),
                        dict(Counter(current[:, i].tolist())))
        for i in range(len(FEATURES))
    ])
    ref_abs = np.abs(reference_shap).mean(axis=0)
    cur_abs = np.abs(current_shap).mean(axis=0)
    displacement = np.abs(cur_abs - ref_abs)
    std = reference_shap.std(axis=0)
    positive = std[std > 1e-9]
    floor = max(float(np.median(positive)) * 0.1 if len(positive) else 0.0, 1e-6)
    scales = np.maximum(std, floor)
    wasserstein = np.asarray([
        wasserstein_distance(reference_shap[:, i], current_shap[:, i]) / scales[i]
        for i in range(len(FEATURES))
    ])
    ref_top = set(np.argsort(-ref_abs, kind="stable")[:3])
    cur_top = set(np.argsort(-cur_abs, kind="stable")[:3])
    overlap = len(ref_top & cur_top) / len(ref_top | cur_top)
    tau = aligned_rank_tau(ref_abs, cur_abs)
    cosine = _cosine(psi, displacement)
    if psi.std() > 1e-12 and displacement.std() > 1e-12:
        centered = float(np.clip((np.corrcoef(psi, displacement)[0, 1] + 1) / 2, 0, 1))
    else:
        centered = 0.0
    return {
        "feature_score": float(psi.mean()),
        "shap_score": float(wasserstein.mean() + 1 - overlap + (1 - tau) / 2),
        "coupling_score": cosine,
        "conservative_score": min(cosine, centered),
        "kendall_tau": tau, "top_k_jaccard": float(overlap),
        "wasserstein_floor": floor,
        **{f"psi_{name}": float(value) for name, value in zip(FEATURES, psi)},
        **{f"shap_displacement_{name}": float(value) for name, value in zip(FEATURES, displacement)},
    }


@dataclass(frozen=True)
class Gates:
    feature_score: float
    shap_score: float
    coupling_score: float
    conservative_score: float
    quantile: float = 0.95

    def to_dict(self) -> dict:
        return asdict(self)


def calibrate_gates(calibration_signals: list[dict], quantile: float = 0.95) -> Gates:
    """Empirical benign-only gates, not an exchangeability/conformal guarantee."""
    if not calibration_signals or not 0 < quantile < 1:
        raise ValueError("Need calibration rows and a quantile strictly between zero and one")
    values = {}
    for name in ("feature_score", "shap_score", "coupling_score", "conservative_score"):
        column = np.asarray([row[name] for row in calibration_signals], dtype=float)
        if not np.isfinite(column).all():
            raise ValueError("Non-finite calibration signal")
        values[name] = float(np.quantile(column, quantile, method="higher"))
    return Gates(**values, quantile=quantile)


def update_requested(policy: str, signals: dict, gates: Gates, index: int,
                     periodic_interval: int = 5) -> bool:
    if policy not in POLICIES:
        raise ValueError(policy)
    if periodic_interval < 1 or index < 0:
        raise ValueError("Invalid periodic interval/index")
    if policy == "static":
        return False
    if policy == "periodic":
        return (index + 1) % periodic_interval == 0
    feature = signals["feature_score"] > gates.feature_score
    shap = signals["shap_score"] > gates.shap_score
    if policy == "feature_only":
        return bool(feature)
    if policy == "shap_only":
        return bool(shap)
    if policy == "dual_signal":
        return bool(feature and shap)
    score = "coupling_score" if policy == "coupled_signal" else "conservative_score"
    return bool(feature and shap and signals[score] > getattr(gates, score))


def confusion(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, int]:
    truth, pred = np.asarray(y_true).astype(bool), np.asarray(y_pred).astype(bool)
    if truth.shape != pred.shape:
        raise ValueError("Truth/prediction shape mismatch")
    return {"tp": int((truth & pred).sum()), "fp": int((~truth & pred).sum()),
            "tn": int((~truth & ~pred).sum()), "fn": int((truth & ~pred).sum())}


def metrics(counts: dict[str, int]) -> dict[str, float | None]:
    tp, fp, tn, fn = (counts[name] for name in ("tp", "fp", "tn", "fn"))
    def ratio(top: int, bottom: int) -> float | None:
        return top / bottom if bottom else None
    return {"precision": ratio(tp, tp + fp), "recall": ratio(tp, tp + fn),
            "f1": ratio(2 * tp, 2 * tp + fp + fn), "false_positive_rate": ratio(fp, fp + tn)}


def matched_refit(baseline: IsolationForest, replay: np.ndarray, current: np.ndarray,
                  minimum: int = 10) -> tuple[IsolationForest, int, bool]:
    candidates = current[baseline.predict(current) == 1]
    if len(candidates) < minimum:
        return baseline, len(candidates), False
    model = IsolationForest(**baseline.get_params())
    model.fit(np.vstack([replay, candidates]))
    return model, len(candidates), True
