"""Generate and validate SHAP explanations for scored event samples."""

from __future__ import annotations

from pathlib import Path
import sys

import joblib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.explain.shap_explainer import explain_score_sample, save_explanations  # noqa: E402
from src.utils.config import load_yaml  # noqa: E402


def main() -> None:
    model_config = joblib.load(ROOT / "models" / "isolation_forest_event_baseline.joblib")
    score_sample = __import__("pandas").read_csv(ROOT / "data" / "scores" / "event_score_sample.csv")
    explain_config = load_yaml(ROOT / "configs" / "explain.yaml")["explain"]
    explanations, metadata = explain_score_sample(
        model_config["model"],
        score_sample,
        model_config["feature_names"],
        sample_per_window=int(explain_config["sample_per_window"]),
    )
    save_explanations(
        explanations,
        metadata,
        ROOT / "data" / "scores" / "shap_sample.csv",
        ROOT / "data" / "scores" / "shap_validation.json",
    )
    print(metadata)
    print(f"explanation_rows={len(explanations)}")


if __name__ == "__main__":
    main()

