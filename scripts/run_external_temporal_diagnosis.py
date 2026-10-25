"""Validate feature/attribution drift diagnosis on aligned external CloudTrail windows.

This is deliberately a diagnosis-validation script, not a claim of full adaptation validation.
The public external corpus has a benign February reference period and an April target period with
injected labelled attack scenarios, but it does not provide enough post-adaptation temporal
windows to validate recovery or long-run retraining policy.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
import sys
import zipfile

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.drift.diagnosis import apply_diagnosis  # noqa: E402
from src.drift.drift_monitor import compute_feature_drift, compute_shap_drift  # noqa: E402
from src.evaluation.metrics import binary_detection_metrics  # noqa: E402
from src.explain.shap_explainer import explain_matrix  # noqa: E402
from src.features.window_features import DEFAULT_HIGH_RISK_EVENTS  # noqa: E402
from scripts.run_external_validation import FEATURES, encode, load_records, normalize_record  # noqa: E402


def event_day(record: dict) -> str:
    return datetime.fromisoformat(str(record["eventTime"]).replace("Z", "+00:00")).date().isoformat()


def encode_sets(train_records: list[dict], sets: dict[str, list[dict]]) -> dict[str, np.ndarray]:
    all_records = [record for records in sets.values() for record in records]
    combined_train, combined_other, maps = encode(train_records, all_records)
    del combined_other
    encoded: dict[str, np.ndarray] = {}
    offset = 0
    for name, records in sets.items():
        size = len(records)
        frame = pd.DataFrame([normalize_record(record) for record in records])
        matrix = np.zeros((size, len(FEATURES)), dtype=np.float64)
        for index, feature in enumerate(FEATURES):
            if feature == "isRoot":
                matrix[:, index] = frame[feature].astype(float)
            else:
                mapping = maps[feature]
                matrix[:, index] = frame[feature].astype(str).map(mapping).fillna(-1).astype(float)
        encoded[name] = matrix
        offset += size
    return encoded


def aggregate_window(records: list[dict], window_id: str) -> tuple[dict, dict[str, dict[str, int]]]:
    counters = {key: Counter() for key in ["eventName", "eventSource", "awsRegion", "userIdentitytype", "errorCode"]}
    errors = 0
    high_risk = 0
    for record in records:
        normalized = normalize_record(record)
        for key in counters:
            counters[key][normalized[key]] += 1
        errors += int(normalized["errorCode"] not in {"NoError", "Unknown"})
        high_risk += int(normalized["eventName"] in DEFAULT_HIGH_RISK_EVENTS)
    count = len(records)
    row = {
        "window_id": window_id,
        "event_count": count,
        "error_rate": errors / count if count else 0.0,
        "high_risk_event_rate": high_risk / count if count else 0.0,
    }
    return row, {key: dict(value) for key, value in counters.items()}


def main() -> None:
    dataset_root = ROOT / "data" / "external" / "cloud_log_sampling-main"
    train_records = load_records(dataset_root / "TrainOn" / "base_a.zip")
    test_records = load_records(dataset_root / "TestOn" / "labeled_cloudtrail_a.zip")
    reference_records = [record for record in test_records if event_day(record) < "2026-04-01"]
    target_records = [record for record in test_records if event_day(record) >= "2026-04-01"]
    if not reference_records or not target_records:
        raise RuntimeError("External corpus does not contain the expected reference and target periods")

    groups: dict[str, list[dict]] = {"external_benign_reference": sorted(reference_records, key=lambda record: str(record.get("eventTime", "")))}
    for scenario in sorted({str(record.get("attack_name") or "benign") for record in target_records}):
        groups[f"external_{scenario}"] = sorted([
            record for record in target_records if str(record.get("attack_name") or "benign") == scenario
        ], key=lambda record: str(record.get("eventTime", "")))
    groups = {name: records for name, records in groups.items() if records}
    matrices = encode_sets(train_records, groups)
    model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42, n_jobs=1)
    train_matrix, _, _ = encode(train_records, reference_records[:1])
    model.fit(train_matrix)

    feature_rows = []
    distributions = {}
    for name, records in groups.items():
        row, distribution = aggregate_window(records, name)
        feature_rows.append(row)
        distributions[name] = distribution
    feature_frame = pd.DataFrame(feature_rows)
    feature_drift = compute_feature_drift(
        feature_frame,
        distributions,
        ["external_benign_reference"],
        scalar_features=["event_count", "error_rate", "high_risk_event_rate"],
    )

    explanation_frames = []
    for name, records in groups.items():
        ordered = records[:500]
        matrix = matrices[name][: len(ordered)]
        explanations, _ = explain_matrix(model, matrix, list(FEATURES), check_additivity=True)
        explanations["window_id"] = name
        explanation_frames.append(explanations)
    explanation_frame = pd.concat(explanation_frames, ignore_index=True)
    shap_drift = compute_shap_drift(explanation_frame, ["external_benign_reference"], list(FEATURES), top_k=3)
    combined = feature_drift.merge(shap_drift, on="window_id", how="inner")

    thresholds = json.loads((ROOT / "data" / "benchmark" / "diagnosis_thresholds.json").read_text(encoding="utf-8"))
    diagnosed = apply_diagnosis(combined, thresholds)
    diagnosed["ground_truth_binary"] = diagnosed["window_id"].map(
        lambda value: 0 if value in {"external_benign_reference", "external_benign"} else 1
    )
    diagnosed["feature_only_prediction"] = (
        diagnosed["feature_drift_score"] >= thresholds["feature_threshold"]
    ).astype(int)
    diagnosed["shap_only_prediction"] = (
        diagnosed["shap_drift_score"] >= thresholds["shap_threshold"]
    ).astype(int)
    diagnosed["dual_signal_prediction"] = (
        diagnosed["diagnosis"] == "security_relevant_drift"
    ).astype(int)
    metrics = {
        policy: binary_detection_metrics(
            diagnosed["ground_truth_binary"].to_numpy(), diagnosed[column].to_numpy()
        )
        for policy, column in {
            "feature_only": "feature_only_prediction",
            "shap_only": "shap_only_prediction",
            "dual_signal": "dual_signal_prediction",
        }.items()
    }

    output = ROOT / "data" / "external_validation"
    output.mkdir(parents=True, exist_ok=True)
    diagnosed.to_csv(output / "external_temporal_diagnosis.csv", index=False)
    (output / "external_temporal_diagnosis_metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "protocol": "fit on benign training archive; use benign February reference window and April target scenario windows",
        "reference_records": len(reference_records),
        "target_records": len(target_records),
        "scenario_windows": {name: len(records) for name, records in groups.items()},
        "diagnosis_threshold_source": "data/benchmark/diagnosis_thresholds.json",
        "evaluation_unit": "scenario window, not individual event",
        "metrics": metrics,
        "limitations": [
            "The external corpus provides one target attack period and is insufficient for long-run adaptation recovery.",
            "The primary threshold is transferred without target-label tuning.",
            "The labels are used only for evaluation, never for fitting or diagnosis.",
        ],
    }
    (output / "external_temporal_diagnosis_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
