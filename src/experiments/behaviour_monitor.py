"""Mixed input contracts and reference-only numeric bins for the v4 comparison."""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import wasserstein_distance
import shap
from src.experiments.behaviour_context import BEHAVIOUR_FEATURES
from src.experiments.journal_protocol import FEATURES, aligned_rank_tau
from src.experiments.journal_comparison import EventEncoder, cosine
from src.drift.drift_monitor import psi_from_counts


class MixedEncoder:
    def __init__(self, inputs: str, representation: str):
        if inputs not in {'event', 'behaviour', 'combined'}: raise ValueError(inputs)
        if inputs == 'behaviour' and representation != 'none': raise ValueError('Behaviour encoding is numeric only')
        self.inputs, self.representation = inputs, representation

    def fit(self, records: list[dict], behaviour: np.ndarray):
        self.features, self.groups = [], []
        width = 0
        if self.inputs != 'behaviour':
            self.event = EventEncoder(self.representation).fit(records)
            self.features.extend(FEATURES)
            self.groups.extend(self.event.groups)
            width = self.event.width
        if self.inputs != 'event':
            if behaviour.shape != (len(records), len(BEHAVIOUR_FEATURES)): raise ValueError('Behaviour contract mismatch')
            self.features.extend(BEHAVIOUR_FEATURES)
            self.groups.extend(slice(width + i, width + i + 1) for i in range(len(BEHAVIOUR_FEATURES)))
            width += len(BEHAVIOUR_FEATURES)
        self.width = width
        self.features = tuple(self.features)
        self.numeric = set(BEHAVIOUR_FEATURES) & set(self.features)
        return self

    def transform(self, records, behaviour):
        parts = []
        if self.inputs != 'behaviour': parts.append(self.event.transform(records))
        if self.inputs != 'event': parts.append(np.asarray(behaviour, dtype=float))
        result = np.column_stack(parts)
        if result.shape != (len(records), self.width) or not np.isfinite(result).all():
            raise ValueError('Invalid model matrix')
        return result

    def frame(self, records, behaviour):
        parts = []
        if self.inputs != 'behaviour': parts.append(EventEncoder.frame(records))
        if self.inputs != 'event': parts.append(pd.DataFrame(behaviour, columns=BEHAVIOUR_FEATURES))
        return pd.concat(parts, axis=1)

    def aggregate(self, values):
        return np.column_stack([values[:, group].sum(axis=1) for group in self.groups])


def reference_edges(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if not len(values) or not np.isfinite(values).all(): raise ValueError('Invalid reference')
    unique = np.unique(values)
    if len(unique) == 1:
        epsilon = max(abs(float(unique[0])) * 1e-8, 1e-8)
        return np.array([unique[0] - epsilon, unique[0] + epsilon])
    return np.unique(np.quantile(values, np.arange(.1, 1, .1)))


class MixedMonitor:
    def __init__(self, model, encoder, records, behaviour):
        self.model, self.encoder = model, encoder
        self.reference_matrix = encoder.transform(records, behaviour)
        self.reference_frame = encoder.frame(records, behaviour)
        self.edges = {name: reference_edges(self.reference_frame[name].to_numpy()) for name in encoder.numeric}
        self.explainer = shap.TreeExplainer(model)
        self.max_residual = 0.0
        self.reference_phi = self.explain(self.reference_matrix)
        self.reference_scores = -model.score_samples(self.reference_matrix)
        self.score_scale = max(float(self.reference_scores.std()), 1e-6)

    def explain(self, matrix):
        raw = np.asarray(self.explainer.shap_values(matrix, check_additivity=True))
        grouped = self.encoder.aggregate(raw)
        expected = float(np.asarray(self.explainer.expected_value).reshape(-1)[0])
        predicted = np.asarray(self.explainer.model.predict(matrix)).reshape(-1)
        self.max_residual = max(self.max_residual, float(np.max(np.abs(expected + grouped.sum(axis=1) - predicted))))
        return grouped

    def counts(self, frame, name):
        if name in self.edges:
            values = np.searchsorted(self.edges[name], frame[name].to_numpy(), side='right')
            return pd.Series(values).value_counts().to_dict()
        return frame[name].astype(str).value_counts().to_dict()

    def signals(self, records, behaviour):
        matrix = self.encoder.transform(records, behaviour)
        frame = self.encoder.frame(records, behaviour)
        phi = self.explain(matrix)
        ref_abs, cur_abs = np.abs(self.reference_phi).mean(axis=0), np.abs(phi).mean(axis=0)
        psi = np.array([psi_from_counts(self.counts(self.reference_frame, name), self.counts(frame, name))
                        for name in self.encoder.features])
        displacement = np.abs(cur_abs - ref_abs)
        scales = self.reference_phi.std(axis=0)
        positive = scales[scales > 1e-9]
        floor = max(float(np.median(positive)) * .1 if len(positive) else 0, 1e-6)
        scales = np.maximum(scales, floor)
        distances = [wasserstein_distance(self.reference_phi[:, i], phi[:, i]) / scales[i]
                     for i in range(len(self.encoder.features))]
        a, b = set(np.argsort(-ref_abs, kind='stable')[:3]), set(np.argsort(-cur_abs, kind='stable')[:3])
        overlap = len(a & b) / len(a | b)
        tau = aligned_rank_tau(ref_abs, cur_abs)
        scores = -self.model.score_samples(matrix)
        signal = {'feature_score': float(psi.mean()),
                  'shap_score': float(np.mean(distances) + 1 - overlap + (1 - tau) / 2),
                  'coupling_score': cosine(psi, displacement),
                  'score_wasserstein': float(wasserstein_distance(self.reference_scores, scores) / self.score_scale),
                  **{f'psi_{name}': float(v) for name, v in zip(self.encoder.features, psi)},
                  **{f'displacement_{name}': float(v) for name, v in zip(self.encoder.features, displacement)}}
        return matrix, scores, signal


def chronological_partitions(records: list[dict], coverage: str) -> tuple[list[int], ...]:
    times = np.array([str(row['eventTime']) for row in records])
    if coverage == 'narrow':
        first = np.where(np.char.startswith(times, times[0][:10]))[0]
        boundary = times[first[int(.7 * len(first))]]
        days = sorted({value[:10] for value in times})
        if len(days) != 3: raise ValueError('Expected three benign development days')
        return (np.where(times < boundary)[0].tolist(),
                [i for i in first if times[i] >= boundary],
                np.where(np.char.startswith(times, days[1]))[0].tolist(),
                np.where(np.char.startswith(times, days[2]))[0].tolist())
    if coverage != 'broad': raise ValueError(coverage)
    boundaries = [times[int(fraction * len(times))] for fraction in (.7, .8, .9)]
    result = (np.where(times < boundaries[0])[0].tolist(),
              np.where((times >= boundaries[0]) & (times < boundaries[1]))[0].tolist(),
              np.where((times >= boundaries[1]) & (times < boundaries[2]))[0].tolist(),
              np.where(times >= boundaries[2])[0].tolist())
    if any(not part for part in result): raise ValueError('Ties exhausted a partition')
    return result
