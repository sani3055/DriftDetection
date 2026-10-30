"""Read saved held-out experiments and replay the real diagnosis rule.

The scenario target is used only after diagnosis, to explain agreement or failure.
No functions in this module train models or write research artifacts.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
import json
import math
from pathlib import Path

from src.adaptation.controller import should_adapt
from src.drift.diagnosis import diagnose_coupled

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_NAMES = {
    "stable": "Stable activity",
    "benign_region": "Routine change: AWS region",
    "benign_identity": "Routine change: identity type",
    "benign_service": "Routine change: AWS service",
    "security_privilege": "Simulated security change: privilege",
    "security_defense": "Simulated security change: defence",
    "security_credential": "Simulated security change: credentials",
}
DIAGNOSIS_NAMES = {
    "stable": "Stable period",
    "benign_drift": "Routine drift",
    "security_relevant_drift": "Security-relevant drift",
    "review_required": "Closer review needed",
    "hidden_model_instability": "Possible model instability",
}
REASONS = {
    "stable": "Both data drift and explanation drift stay below their decision limits.",
    "benign_drift": "The data changed enough to pass its limit, but the SHAP explanation change stays below its limit.",
    "security_relevant_drift": "Both drift signals pass their limits, and the changes align on the same features.",
    "review_required": "The drift signals do not agree enough to request an update under the coupling rule.",
    "hidden_model_instability": "The explanations changed without a matching data-drift signal. This needs closer investigation.",
}
SIGNALS = (
    ("feature_drift_score", "feature_threshold", "Input data change"),
    ("shap_drift_score", "shap_threshold", "SHAP explanation change"),
    ("feature_attribution_coupling", "coupling_threshold", "Feature alignment"),
)


@dataclass(frozen=True)
class ReviewExample:
    scenario: str
    seed: int
    feature_drift_score: float
    shap_drift_score: float
    feature_attribution_coupling: float
    recorded_diagnosis: str
    recorded_update: bool
    expected_class: str


@dataclass(frozen=True)
class DiagnosisResult:
    diagnosis: str
    update_requested: bool
    matches_target: bool
    reason: str


def evaluate_example(example: ReviewExample, thresholds: dict[str, float]) -> DiagnosisResult:
    """Recompute diagnosis without giving scenario targets to the decision rule."""
    diagnosis = diagnose_coupled(
        example.feature_drift_score, example.shap_drift_score,
        example.feature_attribution_coupling, thresholds["feature_threshold"],
        thresholds["shap_threshold"], thresholds["coupling_threshold"],
    )
    update = should_adapt(
        policy="coupled_signal", feature_score=example.feature_drift_score,
        shap_score=example.shap_drift_score, diagnosis=diagnosis,
        feature_threshold=thresholds["feature_threshold"],
        shap_threshold=thresholds["shap_threshold"], sequence_index=0,
        periodic_interval=3,
    )
    return DiagnosisResult(diagnosis, update, diagnosis == example.expected_class, REASONS[diagnosis])


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_review_data(root: Path = PROJECT_ROOT) -> tuple[tuple[ReviewExample, ...], dict[str, float]]:
    """Load only held-out test rows, and reject stale or inconsistent evidence."""
    base = root / "data/benchmark"
    raw_thresholds = json.loads((base / "diagnosis_thresholds.json").read_text(encoding="utf-8"))
    thresholds = {key: float(raw_thresholds[key]) for _, key, _ in SIGNALS}
    if not all(math.isfinite(v) and v > 0 for v in thresholds.values()):
        raise ValueError("Decision limits must be finite and greater than zero.")
    if thresholds["coupling_threshold"] > 1:
        raise ValueError("The coupling threshold must lie between zero and one.")
    rows = [row for row in _read_csv(base / "diagnosis_results.csv") if row["split"] == "test"]
    if not rows:
        raise ValueError("No held-out test scenarios are available.")
    test_keys = {(row["scenario"], int(row["seed"])) for row in rows}
    if len(test_keys) != len(rows):
        raise ValueError("Duplicate held-out scenario/run pairs.")
    adaptations = {}
    for row in _read_csv(base / "adaptation_results.csv"):
        key = (row["scenario"], int(row["seed"]))
        if row["policy"] != "coupled_signal" or key not in test_keys:
            continue
        if key in adaptations:
            raise ValueError("Duplicate saved coupling-policy result.")
        if row["triggered"] not in {"0", "1"}:
            raise ValueError("Saved update request must be zero or one.")
        adaptations[key] = row["triggered"] == "1"
    if adaptations.keys() != test_keys:
        raise ValueError("Diagnosis and adaptation results cover different test pairs.")
    examples = []
    for row in rows:
        scenario, seed = row["scenario"], int(row["seed"])
        if scenario not in SCENARIO_NAMES:
            raise ValueError(f"Unrecognised scenario: {scenario}")
        scores = [float(row[key]) for key, _, _ in SIGNALS]
        if not all(math.isfinite(v) and v >= 0 for v in scores) or scores[2] > 1:
            raise ValueError("Saved drift scores must be finite, nonnegative and valid.")
        expected = "stable" if scenario == "stable" else (
            "benign_drift" if scenario.startswith("benign_") else "security_relevant_drift"
        )
        example = ReviewExample(scenario, seed, *scores, row["coupled_diagnosis"], adaptations[(scenario, seed)], expected)
        result = evaluate_example(example, thresholds)
        if result.diagnosis != example.recorded_diagnosis or result.update_requested != example.recorded_update:
            raise ValueError(f"Recomputed decision disagrees with saved evidence for {scenario}, seed {seed}.")
        examples.append(example)
    return tuple(examples), thresholds
