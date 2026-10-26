"""Evaluate static, blind, ablation, and dual-signal adaptation policies."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.adaptation.controller import POLICIES, protected_retrain, should_adapt  # noqa: E402
from src.evaluation.metrics import binary_detection_metrics  # noqa: E402
from src.experiments.controlled_benchmark import perturb_sample_with_mask  # noqa: E402
from src.utils.config import load_yaml  # noqa: E402


def main() -> None:
    benchmark_config = load_yaml(ROOT / "configs" / "benchmark.yaml")["benchmark"]
    adaptation_config = load_yaml(ROOT / "configs" / "adaptation.yaml")["adaptation"]
    artifact = joblib.load(ROOT / "models" / "isolation_forest_event_baseline.joblib")
    scores = pd.read_csv(ROOT / "data" / "scores" / "event_score_sample.csv")
    diagnosis = pd.read_csv(ROOT / "data" / "benchmark" / "diagnosis_results.csv")
    thresholds = json.loads((ROOT / "data" / "benchmark" / "diagnosis_thresholds.json").read_text(encoding="utf-8"))
    split = json.loads((ROOT / "data" / "processed" / "temporal_split.json").read_text(encoding="utf-8"))
    base = scores[scores["window_id"].isin(set(split["train"]))].sort_values(["window_id", "row_index_within_stream"]).head(int(benchmark_config["sample_size"])).loc[:, list(artifact["feature_names"])].to_numpy(dtype=np.float64)
    baseline_model = artifact["model"]
    policies = list(POLICIES)
    rows = []
    test_rows = diagnosis[diagnosis["split"] == "test"].reset_index(drop=True)
    for policy in policies:
        for sequence_index, record in test_rows.iterrows():
            scenario = str(record["scenario"])
            seed = int(record["seed"])
            current, changed = perturb_sample_with_mask(
                base,
                scenario,
                artifact["category_maps"],
                float(benchmark_config["intensity"]),
                np.random.default_rng(seed),
            )
            trigger = should_adapt(
                policy,
                float(record["feature_drift_score"]),
                float(record["shap_drift_score"]),
                str(
                    record["coupled_diagnosis"]
                    if policy == "coupled_signal"
                    else record["conservative_coupled_diagnosis"]
                    if policy == "conservative_coupled_signal"
                    else record["diagnosis"]
                ),
                float(thresholds["feature_threshold"]),
                float(thresholds["shap_threshold"]),
                sequence_index,
                int(adaptation_config["periodic_interval"]),
            )
            model = baseline_model
            candidate_count = 0
            if trigger:
                model, candidate_count = protected_retrain(
                    baseline_model,
                    base,
                    current,
                    random_state=int(adaptation_config["random_state"]) + seed + sequence_index,
                    n_estimators=int(adaptation_config["adapted_n_estimators"]),
                    contamination=float(adaptation_config["contamination"]),
                    n_jobs=int(adaptation_config["n_jobs"]),
                    minimum_normal_candidates=int(adaptation_config["minimum_normal_candidates"]),
                )
            predictions = (model.predict(current) == -1).astype(int)
            attack_mask = changed.astype(int) if scenario.startswith("security_") else np.zeros(len(changed), dtype=int)
            metrics = binary_detection_metrics(attack_mask, predictions)
            rows.append({
                "policy": policy,
                "scenario": scenario,
                "seed": seed,
                "triggered": int(trigger),
                "candidate_count": candidate_count,
                "anomaly_rate": float(predictions.mean()),
                "unnecessary_adaptation": int(trigger and not scenario.startswith("security_")),
                **metrics,
            })
    result = pd.DataFrame(rows)
    output = ROOT / "data" / "benchmark"
    result.to_csv(output / "adaptation_results.csv", index=False)
    summary = result.groupby("policy").agg(
        trigger_rate=("triggered", "mean"),
        unnecessary_adaptation_rate=("unnecessary_adaptation", "mean"),
        mean_anomaly_rate=("anomaly_rate", "mean"),
        mean_precision=("precision", "mean"),
        mean_recall=("recall", "mean"),
        mean_f1=("f1", "mean"),
        mean_false_positive_rate=("false_positive_rate", "mean"),
    ).reset_index()
    summary.to_csv(output / "adaptation_summary.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
