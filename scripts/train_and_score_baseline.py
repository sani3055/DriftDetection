"""Train the chronological Isolation Forest baseline and score monthly samples."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import joblib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.isolation_forest import save_training_metadata, score_csv, train_detector  # noqa: E402
from src.utils.config import load_yaml, project_path  # noqa: E402


def main() -> None:
    base = load_yaml(ROOT / "configs" / "base.yaml")
    temporal = json.loads((ROOT / "data" / "processed" / "temporal_split.json").read_text(encoding="utf-8"))
    model_config = load_yaml(ROOT / "configs" / "model.yaml")["model"]
    dataset = project_path(ROOT, base["dataset"]["source_path"])
    artifact_path = ROOT / "models" / "isolation_forest_event_baseline.joblib"
    artifact = train_detector(
        dataset,
        temporal["train"],
        artifact_path,
        n_estimators=int(model_config["n_estimators"]),
        contamination=float(model_config["contamination"]),
        max_samples=model_config["max_samples"],
        random_state=int(model_config["random_state"]),
        n_jobs=int(model_config["n_jobs"]),
        chunk_size=int(model_config["chunk_size"]),
    )
    save_training_metadata(ROOT / "models" / "isolation_forest_event_baseline.json", artifact)
    scores = score_csv(
        dataset,
        artifact,
        ROOT / "data" / "scores" / "event_score_sample.csv",
        sample_per_window=int(model_config["score_sample_per_window"]),
        chunk_size=int(model_config["chunk_size"]),
    )
    print(f"trained_rows={artifact['training_rows']}")
    print(f"sampled_scores={len(scores)}")
    print(f"artifact={artifact_path}")


if __name__ == "__main__":
    main()

