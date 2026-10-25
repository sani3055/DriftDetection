"""Build chronological monthly features from the external CloudTrail CSV."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.temporal_protocol import chronological_split  # noqa: E402
from src.features.window_features import aggregate_cloudtrail_csv, save_window_features  # noqa: E402
from src.utils.config import load_yaml, project_path  # noqa: E402


def main() -> None:
    base = load_yaml(ROOT / "configs" / "base.yaml")
    temporal = load_yaml(ROOT / "configs" / "temporal_protocol.yaml")
    dataset = project_path(ROOT, base["dataset"]["source_path"])
    output_dir = ROOT / "data" / "processed"

    features, distributions = aggregate_cloudtrail_csv(
        dataset,
        chunk_size=int(base["dataset"]["chunk_size"]),
        high_risk_events=temporal["features"]["high_risk_events"],
    )
    split = chronological_split(
        features["window_id"].tolist(),
        train_fraction=float(temporal["temporal"]["train_fraction"]),
        validation_fraction=float(temporal["temporal"]["validation_fraction"]),
        minimum_months_per_split=int(temporal["temporal"]["minimum_months_per_split"]),
    )
    split_map = {
        month: "train" for month in split.train
    } | {month: "validation" for month in split.validation} | {month: "test" for month in split.test}
    features["split"] = features["window_id"].map(split_map)

    save_window_features(
        features,
        distributions,
        output_dir / "monthly_features.csv",
        output_dir / "monthly_distributions.json",
    )
    (output_dir / "temporal_split.json").write_text(
        json.dumps({"train": split.train, "validation": split.validation, "test": split.test}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(features.to_string(index=False))
    print(json.dumps({"train": split.train, "validation": split.validation, "test": split.test}, indent=2))


if __name__ == "__main__":
    main()

