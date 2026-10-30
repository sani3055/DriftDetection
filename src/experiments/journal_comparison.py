"""V3 factorial controls, raw-category monitoring and historical shadow guards.

This module deliberately never reads attack labels. Dataset integrity and outcome
evaluation belong to the runner. Grouped SHAP is a signed sum, not Owen values.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import wasserstein_distance
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import OneHotEncoder
import shap

from src.experiments.journal_protocol import FEATURES, aligned_rank_tau, normalise
from src.drift.drift_monitor import psi_from_counts

CATEGORICAL = FEATURES[:-1]
V3_POLICIES = (
    "static", "periodic", "feature_only", "shap_only", "dual_signal",
    "coupled_signal", "conservative_coupled_signal", "score_wasserstein",
    "adwin_score", "page_hinkley_score", "guarded_dual", "guarded_feature",
    "guarded_periodic",
)


class EventEncoder:
    def __init__(self, representation: str):
        if representation not in {"ordinal", "onehot"}:
            raise ValueError(representation)
        self.representation = representation

    @staticmethod
    def frame(records: list[dict]) -> pd.DataFrame:
        return pd.DataFrame([normalise(record) for record in records], columns=FEATURES)

    def fit(self, records: list[dict]) -> EventEncoder:
        if not records:
            raise ValueError("Empty encoder fitting set")
        frame = self.frame(records)
        self.maps = {name: {value: i for i, value in enumerate(sorted(frame[name].astype(str).unique()))}
                     for name in CATEGORICAL}
        self.groups: list[slice] = []
        if self.representation == "onehot":
            self.onehot = OneHotEncoder(handle_unknown="ignore", sparse_output=False, dtype=np.float64)
            self.onehot.fit(frame.loc[:, list(CATEGORICAL)].astype(str))
            offset = 0
            for categories in self.onehot.categories_:
                self.groups.append(slice(offset, offset + len(categories)))
                offset += len(categories)
            self.groups.append(slice(offset, offset + 1))
            self.width = offset + 1
        else:
            self.groups = [slice(i, i + 1) for i in range(len(FEATURES))]
            self.width = len(FEATURES)
        return self

    def transform(self, records: list[dict]) -> np.ndarray:
        frame = self.frame(records)
        if not len(frame):
            return np.empty((0, self.width), dtype=float)
        if self.representation == "onehot":
            encoded = self.onehot.transform(frame.loc[:, list(CATEGORICAL)].astype(str))
        else:
            encoded = np.column_stack([frame[name].astype(str).map(self.maps[name]).fillna(-1).to_numpy()
                                       for name in CATEGORICAL])
        return np.column_stack([encoded, frame.isRoot.to_numpy(dtype=float)]).astype(float)

    def aggregate_attributions(self, values: np.ndarray) -> np.ndarray:
        values = np.asarray(values, dtype=float)
        if values.ndim != 2 or values.shape[1] != self.width:
            raise ValueError("Attribution width mismatch")
        return np.column_stack([values[:, group].sum(axis=1) for group in self.groups])

    def unknown_rates(self, records: list[dict]) -> dict[str, float]:
        frame = self.frame(records)
        if not len(frame):
            return {name: 0.0 for name in CATEGORICAL}
        return {name: float((~frame[name].astype(str).isin(self.maps[name])).mean()) for name in CATEGORICAL}


def cosine(left: np.ndarray, right: np.ndarray) -> float:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    return float(np.clip(np.dot(left, right) / denominator, 0.0, 1.0)) if denominator > 1e-12 else 0.0


def effective_features(values: np.ndarray) -> float:
    values = np.abs(np.asarray(values, dtype=float))
    denominator = float(np.square(values).sum())
    return float(values.sum() ** 2 / denominator) if denominator > 1e-20 else 0.0


class FrozenMonitor:
    def __init__(self, model: IsolationForest, encoder: EventEncoder, reference: list[dict]):
        self.model, self.encoder = model, encoder
        self.reference_frame = encoder.frame(reference)
        self.reference_matrix = encoder.transform(reference)
        self.explainer = shap.TreeExplainer(model)
        self.max_additivity_residual = 0.0
        self.reference_phi = self.explain(self.reference_matrix)
        self.reference_scores = -model.score_samples(self.reference_matrix)
        self.score_scale = max(float(self.reference_scores.std()), 1e-6)

    def explain(self, matrix: np.ndarray) -> np.ndarray:
        values = np.asarray(self.explainer.shap_values(matrix, check_additivity=True), dtype=float)
        if values.ndim != 2:
            raise ValueError("Unexpected Tree SHAP output shape")
        grouped = self.encoder.aggregate_attributions(values)
        expected = float(np.asarray(self.explainer.expected_value).reshape(-1)[0])
        explained = np.asarray(self.explainer.model.predict(matrix)).reshape(-1)
        residual = float(np.max(np.abs(expected + grouped.sum(axis=1) - explained)))
        self.max_additivity_residual = max(self.max_additivity_residual, residual)
        return grouped

    def signals(self, records: list[dict]) -> tuple[np.ndarray, np.ndarray, dict[str, float | str]]:
        matrix = self.encoder.transform(records)
        frame = self.encoder.frame(records)
        phi = self.explain(matrix)
        ref_abs, cur_abs = np.abs(self.reference_phi).mean(axis=0), np.abs(phi).mean(axis=0)
        displacement = np.abs(cur_abs - ref_abs)
        # PSI uses raw categorical values, preserving distinct unseen categories.
        psi = np.asarray([psi_from_counts(self.reference_frame[name].astype(str).value_counts().to_dict(),
                                         frame[name].astype(str).value_counts().to_dict()) for name in FEATURES])
        scales = self.reference_phi.std(axis=0)
        positive = scales[scales > 1e-9]
        floor = max(float(np.median(positive)) * .1 if len(positive) else 0.0, 1e-6)
        scales = np.maximum(scales, floor)
        distances = [wasserstein_distance(self.reference_phi[:, i], phi[:, i]) / scales[i]
                     for i in range(len(FEATURES))]
        a, b = set(np.argsort(-ref_abs, kind="stable")[:3]), set(np.argsort(-cur_abs, kind="stable")[:3])
        jaccard = len(a & b) / len(a | b)
        tau = aligned_rank_tau(ref_abs, cur_abs)
        alignment = cosine(psi, displacement)
        centered = (float(np.clip((np.corrcoef(psi, displacement)[0, 1] + 1) / 2, 0, 1))
                    if psi.std() > 1e-12 and displacement.std() > 1e-12 else 0.0)
        scores = -self.model.score_samples(matrix)
        signal = {
            "feature_score": float(psi.mean()),
            "shap_score": float(np.mean(distances) + 1 - jaccard + (1 - tau) / 2),
            "coupling_score": alignment, "conservative_score": min(alignment, centered),
            "score_wasserstein": float(wasserstein_distance(self.reference_scores, scores) / self.score_scale),
            "psi_effective_features": effective_features(psi),
            "attribution_effective_features": effective_features(displacement),
            "dominant_drift_feature": FEATURES[int(np.argmax(psi))],
            "dominant_attribution_feature": FEATURES[int(np.argmax(displacement))],
            **{f"psi_{name}": float(v) for name, v in zip(FEATURES, psi)},
            **{f"displacement_{name}": float(v) for name, v in zip(FEATURES, displacement)},
            **{f"unknown_{name}": value for name, value in self.encoder.unknown_rates(records).items()},
        }
        return matrix, scores, signal


@dataclass
class Deployed:
    model: IsolationForest
    cutoff: float

    def predict(self, matrix: np.ndarray) -> np.ndarray:
        return (-self.model.score_samples(matrix) > self.cutoff).astype(int)


def score_cutoff(model: IsolationForest, calibration: np.ndarray, mode: str) -> float:
    if mode == "training_offset":
        return float(-model.offset_)
    if mode != "benign_quantile":
        raise ValueError(mode)
    return float(np.quantile(-model.score_samples(calibration), .95, method="higher"))


def shadow_guard(baseline: Deployed, candidate: Deployed, guard: np.ndarray,
                 anchors: np.ndarray, fpr_margin: float = .01, retention_margin: float = .02) -> dict[str, float | bool]:
    if len(guard) == 0 or len(anchors) == 0:
        raise ValueError("Guard and anchor sets must be nonempty")
    old_alarm_rate = float(baseline.predict(guard).mean())
    new_alarm_rate = float(candidate.predict(guard).mean())
    old_anchor = float((-baseline.model.score_samples(anchors)).mean())
    new_anchor = float((-candidate.model.score_samples(anchors)).mean())
    allowed = new_alarm_rate <= old_alarm_rate + fpr_margin and new_anchor >= old_anchor - retention_margin
    return {"guard_allowed": bool(allowed), "baseline_guard_alarm_rate": old_alarm_rate,
            "candidate_guard_alarm_rate": new_alarm_rate, "baseline_anchor_score": old_anchor,
            "candidate_anchor_score": new_anchor}


def scalar_thresholds(calibration_signals: list[dict]) -> dict[str, float]:
    return {name: float(np.quantile([row[name] for row in calibration_signals], .95, method="higher"))
            for name in ["feature_score", "shap_score", "coupling_score", "conservative_score", "score_wasserstein"]}


def request_v3(policy: str, signals: dict, thresholds: dict, index: int,
               adwin_alarm: bool = False, ph_alarm: bool = False) -> bool:
    if policy not in V3_POLICIES:
        raise ValueError(policy)
    feature = signals["feature_score"] > thresholds["feature_score"]
    attribution = signals["shap_score"] > thresholds["shap_score"]
    if policy == "static": return False
    if policy in {"periodic", "guarded_periodic"}: return (index + 1) % 5 == 0
    if policy in {"feature_only", "guarded_feature"}: return bool(feature)
    if policy == "shap_only": return bool(attribution)
    if policy in {"dual_signal", "guarded_dual"}: return bool(feature and attribution)
    if policy in {"coupled_signal", "conservative_coupled_signal"}:
        key = "coupling_score" if policy == "coupled_signal" else "conservative_score"
        return bool(feature and attribution and signals[key] > thresholds[key])
    if policy == "score_wasserstein": return signals["score_wasserstein"] > thresholds["score_wasserstein"]
    return bool(adwin_alarm if policy == "adwin_score" else ph_alarm)


def moving_block_indices(session_sizes: list[int], block_length: int,
                         rng: np.random.Generator) -> np.ndarray:
    if block_length < 1 or any(size < 1 for size in session_sizes):
        raise ValueError("Positive session and block lengths required")
    chunks, offset = [], 0
    for size in session_sizes:
        length = min(block_length, size)
        starts = rng.integers(0, size - length + 1, size=int(np.ceil(size / length)))
        sample = np.concatenate([np.arange(start, start + length) for start in starts])[:size]
        chunks.append(sample + offset)
        offset += size
    return np.concatenate(chunks)
