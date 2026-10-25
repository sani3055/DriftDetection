"""Run the Phase 0 external-dataset audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.dataset_audit import audit_csv  # noqa: E402
from src.utils.config import load_yaml, project_path  # noqa: E402
from src.utils.logging import configure_logging  # noqa: E402
from src.utils.seed import seed_everything  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT / "configs" / "base.yaml"))
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    config = load_yaml(args.config)
    seed_everything(int(config["random"]["seed"]))
    configure_logging(str(config["logging"]["level"]))

    dataset_path = args.dataset or config["dataset"]["source_path"]
    output_path = args.output or config["dataset"]["manifest_path"]
    dataset = project_path(ROOT, dataset_path)
    output = project_path(ROOT, output_path)

    manifest = audit_csv(
        dataset,
        encoding=str(config["dataset"]["encoding"]),
        include_sha256=True,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print(f"Manifest written to {output}")


if __name__ == "__main__":
    main()

