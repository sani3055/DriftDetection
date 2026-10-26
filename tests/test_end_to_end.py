from __future__ import annotations

from pathlib import Path


def test_generated_research_artifacts_exist() -> None:
    required = [
        Path("data_manifest/real_cloudtrail_manifest.json"),
        Path("data/processed/monthly_features.csv"),
        Path("data/processed/temporal_split.json"),
        Path("models/isolation_forest_event_baseline.joblib"),
        Path("data/scores/shap_validation.json"),
        Path("data/drift/combined_drift.csv"),
        Path("data/drift/coupling_drift.csv"),
        Path("data/benchmark/diagnosis_results.csv"),
        Path("data/benchmark/adaptation_results.csv"),
        Path("results/adaptation_summary.csv"),
        Path("results/paired_inference.csv"),
        Path("data_manifest/rich_timestamp_manifest.json"),
        Path("data/robustness/detector_ablation_summary.csv"),
        Path("data/robustness/window_size_summary.csv"),
        Path("docs/manuscript_draft.md"),
        Path("data/external_validation/external_detector_metrics.csv"),
        Path("data/external_validation/external_validation_manifest.json"),
        Path("data/external_validation/external_temporal_diagnosis_metrics.json"),
        Path("data/robustness/cost_sensitivity_results.csv"),
        Path("data/robustness/cost_sensitivity_winners.csv"),
        Path("docs/external_validation.md"),
        Path("docs/final_validation.md"),
        Path("docs/next_experiments.md"),
        Path("docs/cost_sensitivity.md"),
        Path("docs/attribution_feature_coupling.md"),
        Path("docs/unsupervised_transfer_calibration.md"),
        Path("figures/monthly_drift_signals.png"),
    ]
    missing = [str(path) for path in required if not path.is_file()]
    assert not missing, f"Missing generated artifacts: {missing}"
