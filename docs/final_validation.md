# Final implementation validation

## Scope

This validation covers the implemented reproducible pipeline using the external, read-only
CloudTrail-style CSV recorded in `data_manifest/real_cloudtrail_manifest.json`.

## Dataset facts

- Source rows audited: 1,939,207
- Columns: 18
- Temporal resolution: month-level `eventTime`
- Malformed rows: none observed in the audit
- Attack labels: unavailable
- SHA-256: `b3aa4fcf28747f4f84457d2d3b76f4c27901bd2e6289bf6d6288cb9587d20589`

## Implemented pipeline

1. Read-only audit and provenance manifest.
2. Chronological monthly feature construction with train/validation/test partitions.
3. Train-only categorical encoding and Isolation Forest anomaly scoring.
4. SHAP TreeExplainer validation with additivity checks.
5. Feature-distribution and attribution-drift monitoring.
6. Controlled semi-synthetic benchmark with benign and security-relevant perturbations.
7. Validation-tuned threshold diagnosis evaluated on held-out scenarios.
8. Protected adaptation-policy comparison with static, periodic, feature-only, SHAP-only, and
   dual-signal policies.
9. Saved result summaries and publication-oriented figures.
10. Independent detector validation and a coarse external reference/target temporal diagnosis
    checkpoint.
11. Attribution-feature coupling and a separate coupled-signal adaptation ablation.

## Validation evidence

- Full test suite: **26 passed**.
- SHAP maximum additivity residual: `2.6645352591003757e-14`.
- Benchmark validation macro-F1: `0.7306397306397306`.
- Held-out diagnosis confusion matrix and adaptation-policy comparison were rendered and
  visually inspected.
- Paired Wilcoxon comparison for dual-signal versus static adaptation produced an FPR
  p-value of `0.00028961940975555264` in the implemented benchmark.
- Detector-family and sample-size ablations were completed with deterministic bootstrap 95% CIs.
- Mean absolute SHAP-attribution displacement is reported as an explicit attribution-drift metric.
- Feature-attribution coupling is reported as cosine similarity between aligned PSI and SHAP
  displacement vectors in `data/drift/coupling_drift.csv`.
- The richer raw export audit found 1,330 distinct days and all 24 hours, while confirming that it
  is the same underlying corpus and not independent validation.
- Detector-only external validation completed on a separate labeled CloudTrail corpus: Isolation
  Forest F1 `0.451874`, recall `0.713733`, and FPR `0.173751`.
- External temporal diagnosis checkpoint completed at scenario-window level: feature-only,
  SHAP-only, and dual-signal policies each achieved F1 `0.952381` and FPR `0.500000`.
- The coupled external checkpoint achieved F1 `0.181818`, recall `0.100000`, and FPR `0.000000`,
  exposing negative transfer of the coupling threshold rather than supporting a superiority claim.
- Coupled-signal adaptation ablation completed; it matched the dual policy in the current held-out
  benchmark and is retained as a neutral result.
- The pinned environment was used to regenerate the model, SHAP, drift, benchmark, adaptation,
  and reporting artifacts; `requirements.txt` records the declared versions.

These benchmark metrics are evidence for the defined semi-synthetic protocol only. They are not
claims of attack recall on the original unlabeled CloudTrail corpus.

## Generated artifacts

- `data/processed/monthly_features.csv`
- `data/processed/monthly_distributions.json`
- `data/processed/temporal_split.json`
- `models/isolation_forest_event_baseline.joblib`
- `data/scores/event_score_sample.csv`
- `data/scores/shap_sample.csv`
- `data/drift/feature_drift.csv`
- `data/drift/shap_drift.csv`
- `data/drift/combined_drift.csv`
- `data/drift/coupling_drift.csv`
- `data/benchmark/scenario_signals.csv`
- `data/benchmark/diagnosis_results.csv`
- `data/benchmark/adaptation_results.csv`
- `results/adaptation_summary.csv`
- `results/paired_wilcoxon.csv`
- `results/paired_inference.csv`
- `data/robustness/detector_ablation_results.csv`
- `data/robustness/detector_ablation_summary.csv`
- `data/robustness/window_size_results.csv`
- `data/robustness/window_size_summary.csv`
- `data_manifest/rich_timestamp_manifest.json`
- `docs/manuscript_draft.md`
- `data/external_validation/external_detector_metrics.csv`
- `data/external_validation/external_scenario_metrics.csv`
- `data/external_validation/external_validation_manifest.json`
- `data/external_validation/external_temporal_diagnosis.csv`
- `data/external_validation/external_temporal_diagnosis_metrics.json`
- `data/external_validation/external_temporal_diagnosis_manifest.json`
- `docs/external_validation.md`
- `figures/monthly_drift_signals.png`
- `figures/diagnosis_confusion_matrix.png`
- `figures/adaptation_policy_comparison.png`

## Remaining journal-level work

The implementation is a reproducible primary experiment with detector-level external validation
and a coarse temporal diagnosis checkpoint, but it is not by itself a Q1/Q2 acceptance guarantee.
Before submission, add external temporal validation of the full SHAP-diagnosis/adaptation
recovery protocol or real incident validation, and complete venue-specific reference, PRISMA,
risk-of-bias, and threat-to-validity review.
