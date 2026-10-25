"""Run validation-tuned diagnosis on held-out controlled scenarios."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.experiments.controlled_benchmark import run_benchmark  # noqa: E402
from src.utils.config import load_yaml  # noqa: E402


def main() -> None:
    config = load_yaml(ROOT / "configs" / "benchmark.yaml")["benchmark"]
    artifact = joblib.load(ROOT / "models" / "isolation_forest_event_baseline.joblib")
    scores = pd.read_csv(ROOT / "data" / "scores" / "event_score_sample.csv")
    train_months = set(json.loads((ROOT / "data" / "processed" / "temporal_split.json").read_text(encoding="utf-8"))["train"])
    base = scores[scores["window_id"].isin(train_months)].sort_values(["window_id", "row_index_within_stream"]).head(int(config["sample_size"])).loc[:, list(artifact["feature_names"])].to_numpy(dtype=np.float64)
    raw, thresholds, diagnosed = run_benchmark(
        artifact["model"],
        artifact["category_maps"],
        base,
        list(config["scenario_types"]),
        list(config["validation_seeds"]),
        list(config["test_seeds"]),
        float(config["intensity"]),
    )
    output = ROOT / "data" / "benchmark"
    output.mkdir(parents=True, exist_ok=True)
    raw.to_csv(output / "scenario_signals.csv", index=False)
    diagnosed.to_csv(output / "diagnosis_results.csv", index=False)
    (output / "diagnosis_thresholds.json").write_text(json.dumps(thresholds, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(thresholds, indent=2))
    print(diagnosed[diagnosed["split"] == "test"]["diagnosis"].value_counts().to_string())


if __name__ == "__main__":
    main()

