"""Documented reproducibility entry point for the complete pipeline."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    "scripts/audit_dataset.py",
    "scripts/build_temporal_features.py",
    "scripts/train_and_score_baseline.py",
    "scripts/generate_shap_explanations.py",
    "scripts/compute_drift.py",
    "scripts/run_controlled_benchmark.py",
    "scripts/run_adaptation_experiments.py",
    "scripts/run_cost_sensitivity.py",
    "scripts/make_reports.py",
]


def main() -> None:
    for step in STEPS:
        print(f"===== {step} =====", flush=True)
        subprocess.run([sys.executable, step], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
