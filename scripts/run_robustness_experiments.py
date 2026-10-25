"""Run detector, sample-size, and temporal-resolution robustness experiments."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.inference import bootstrap_mean_ci  # noqa: E402
from src.evaluation.metrics import binary_detection_metrics  # noqa: E402
from src.experiments.controlled_benchmark import perturb_sample_with_mask  # noqa: E402
from src.utils.config import load_yaml  # noqa: E402


SCENARIOS = (
    "stable",
    "benign_region",
    "benign_identity",
    "benign_service",
    "security_privilege",
    "security_defense",
    "security_credential",
)


def make_detector(name: str, seed: int):
    if name.startswith("isolation_forest_"):
        estimators = int(name.rsplit("_", 1)[1])
        return IsolationForest(
            n_estimators=estimators,
            contamination=0.05,
            random_state=seed,
            n_jobs=1,
        )
    if name == "local_outlier_factor":
        return LocalOutlierFactor(n_neighbors=20, contamination=0.05, novelty=True)
    if name == "one_class_svm":
        return OneClassSVM(nu=0.05, gamma="scale")
    raise ValueError(f"Unknown detector family: {name}")


def evaluate_detector(
    detector_name: str,
    base: np.ndarray,
    category_maps: dict[str, dict[str, int]],
    seeds: list[int],
    intensity: float,
    seed: int,
) -> pd.DataFrame:
    detector = make_detector(detector_name, seed)
    detector.fit(base)
    rows = []
    for test_seed in seeds:
        for scenario in SCENARIOS:
            current, changed = perturb_sample_with_mask(
                base,
                scenario,
                category_maps,
                intensity,
                np.random.default_rng(test_seed),
            )
            predictions = (detector.predict(current) == -1).astype(int)
            truth = changed.astype(int) if scenario.startswith("security_") else np.zeros(len(changed), dtype=int)
            rows.append({
                "detector": detector_name,
                "seed": test_seed,
                "scenario": scenario,
                "sample_size": len(base),
                **binary_detection_metrics(truth, predictions),
            })
    return pd.DataFrame(rows)


def summarize_detector_results(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for detector, group in frame.groupby("detector"):
        security = group[group["scenario"].str.startswith("security_")]
        benign = group[~group["scenario"].str.startswith("security_")]
        row = {"detector": detector}
        for label, values in {
            "overall_f1": group["f1"],
            "overall_false_positive_rate": group["false_positive_rate"],
            "security_recall": security["recall"],
            "security_f1": security["f1"],
            "benign_false_positive_rate": benign["false_positive_rate"],
        }.items():
            mean, low, high = bootstrap_mean_ci(values, seed=42 + len(rows))
            row.update({label: mean, f"{label}_ci_low": low, f"{label}_ci_high": high})
        rows.append(row)
    return pd.DataFrame(rows)


def run_window_ablation(
    full_base: np.ndarray,
    category_maps: dict[str, dict[str, int]],
    sizes: list[int],
    seeds: list[int],
    intensity: float,
    seed: int,
) -> pd.DataFrame:
    rows = []
    for size in sizes:
        base = full_base[:size]
        detector = IsolationForest(n_estimators=100, contamination=0.05, random_state=seed, n_jobs=1).fit(base)
        for test_seed in seeds:
            for scenario in SCENARIOS:
                current, changed = perturb_sample_with_mask(
                    base,
                    scenario,
                    category_maps,
                    intensity,
                    np.random.default_rng(test_seed),
                )
                predictions = (detector.predict(current) == -1).astype(int)
                truth = changed.astype(int) if scenario.startswith("security_") else np.zeros(len(changed), dtype=int)
                rows.append({
                    "sample_size": size,
                    "seed": test_seed,
                    "scenario": scenario,
                    **binary_detection_metrics(truth, predictions),
                })
    return pd.DataFrame(rows)


def summarize_window_results(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for size, group in frame.groupby("sample_size"):
        security = group[group["scenario"].str.startswith("security_")]
        benign = group[~group["scenario"].str.startswith("security_")]
        row = {"sample_size": int(size)}
        for label, values in {
            "security_recall": security["recall"],
            "security_f1": security["f1"],
            "benign_false_positive_rate": benign["false_positive_rate"],
        }.items():
            mean, low, high = bootstrap_mean_ci(values, seed=100 + int(size))
            row.update({label: mean, f"{label}_ci_low": low, f"{label}_ci_high": high})
        rows.append(row)
    return pd.DataFrame(rows).sort_values("sample_size")


def main() -> None:
    benchmark = load_yaml(ROOT / "configs" / "benchmark.yaml")["benchmark"]
    robustness = load_yaml(ROOT / "configs" / "robustness.yaml")["robustness"]
    artifact = joblib.load(ROOT / "models" / "isolation_forest_event_baseline.joblib")
    scores = pd.read_csv(ROOT / "data" / "scores" / "event_score_sample.csv")
    split = json.loads((ROOT / "data" / "processed" / "temporal_split.json").read_text(encoding="utf-8"))
    train_rows = scores[scores["window_id"].isin(set(split["train"]))].sort_values(["window_id", "row_index_within_stream"])
    max_size = max(int(size) for size in robustness["sample_sizes"])
    full_base = train_rows.head(max_size).loc[:, list(artifact["feature_names"])].to_numpy(dtype=np.float64)
    if len(full_base) < max_size:
        raise RuntimeError(f"Need {max_size} training rows, found {len(full_base)}")
    test_seeds = list(benchmark["test_seeds"])
    intensity = float(benchmark["intensity"])
    output = ROOT / "data" / "robustness"
    output.mkdir(parents=True, exist_ok=True)

    detector_frames = [
        evaluate_detector(
            name,
            full_base[: int(robustness["sample_sizes"][1])],
            artifact["category_maps"],
            test_seeds,
            intensity,
            int(robustness["detector_seed"]),
        )
        for name in list(robustness["detector_families"])
    ]
    detector_results = pd.concat(detector_frames, ignore_index=True)
    detector_results.to_csv(output / "detector_ablation_results.csv", index=False)
    summarize_detector_results(detector_results).to_csv(output / "detector_ablation_summary.csv", index=False)

    window_results = run_window_ablation(
        full_base,
        artifact["category_maps"],
        [int(size) for size in robustness["sample_sizes"]],
        test_seeds,
        intensity,
        int(robustness["detector_seed"]),
    )
    window_results.to_csv(output / "window_size_results.csv", index=False)
    summarize_window_results(window_results).to_csv(output / "window_size_summary.csv", index=False)

    metadata = {
        "detector_families": list(robustness["detector_families"]),
        "sample_sizes": [int(size) for size in robustness["sample_sizes"]],
        "test_seeds": test_seeds,
        "intensity": intensity,
        "training_months": split["train"],
        "note": "Ablations use controlled perturbations of the real corpus; they are not independent-dataset validation.",
    }
    (output / "robustness_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print("Detector and window-size robustness artifacts generated")


if __name__ == "__main__":
    main()
