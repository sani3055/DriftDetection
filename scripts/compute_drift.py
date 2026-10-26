"""Compute monthly feature and SHAP drift against chronological training months."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.drift.drift_monitor import compute_feature_drift, compute_shap_drift, save_drift_outputs  # noqa: E402
from src.utils.config import load_yaml  # noqa: E402


def main() -> None:
    drift_config = load_yaml(ROOT / "configs" / "drift.yaml")["drift"]
    split = json.loads((ROOT / "data" / "processed" / "temporal_split.json").read_text(encoding="utf-8"))
    features = pd.read_csv(ROOT / "data" / "processed" / "monthly_features.csv")
    distributions = json.loads((ROOT / "data" / "processed" / "monthly_distributions.json").read_text(encoding="utf-8"))
    shap_sample = pd.read_csv(ROOT / "data" / "scores" / "shap_sample.csv")
    model_artifact = __import__("joblib").load(ROOT / "models" / "isolation_forest_event_baseline.joblib")
    feature_drift = compute_feature_drift(
        features,
        distributions,
        split[drift_config["reference_split"]],
        epsilon=float(drift_config["epsilon"]),
        scalar_features=drift_config["scalar_features"],
    )
    shap_drift = compute_shap_drift(
        shap_sample,
        split[drift_config["reference_split"]],
        model_artifact["feature_names"],
        top_k=int(drift_config["top_k"]),
    )
    combined = save_drift_outputs(feature_drift, shap_drift, ROOT / "data" / "drift")
    print(combined[["window_id", "feature_drift_score", "shap_drift_score", "feature_attribution_coupling"]].to_string(index=False))


if __name__ == "__main__":
    main()
