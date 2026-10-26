# SHAP-Guided Drift Diagnosis for AWS CloudTrail

This repository studies whether feature-distribution drift and SHAP-attribution drift provide
complementary information for deciding when an unsupervised CloudTrail anomaly detector should be
adapted.

## Data

The project uses the external real corpus configured in `configs/base.yaml`:

```text
D:/Projects/CloudGuard/data/dec12_18features.csv
```

The source is read-only and is not copied into this repository. The audited manifest is stored in
`data_manifest/real_cloudtrail_manifest.json`.

The corpus is month-level and unlabeled. Consequently, the project reports observational real-data
drift separately from controlled semi-synthetic diagnosis and adaptation results.

## Run

Use the supported Python version and install the pinned dependencies from `requirements.txt`. Then
run:

```text
python scripts/run_all.py
python scripts/audit_rich_timestamp_source.py
python scripts/run_robustness_experiments.py
python scripts/run_external_validation.py
python scripts/run_external_temporal_diagnosis.py
python scripts/run_cost_sensitivity.py
python scripts/build_presentation.py
python scripts/validate_submission_package.py
python -m pytest tests -q
```

The pipeline creates models, monthly features, drift artifacts, benchmark results, tables, and
figures. Evaluation and reporting read saved result files; they do not retrain models.

Journal-strengthening artifacts are written under `data/robustness/` and include detector-family
and sample-size ablations with bootstrap intervals. `results/paired_inference.csv` contains paired
effect sizes, bootstrap confidence intervals, Wilcoxon tests, and Benjamini–Hochberg adjusted
values. `docs/manuscript_draft.md` is a manuscript-ready draft populated only from saved results.

The richer raw export is audited for timestamp resolution, but it belongs to the same underlying
corpus and is explicitly not treated as independent validation.

An independent validation track is available through `scripts/run_external_validation.py`. It uses
the public Cloud Log Sampling Dataset in `data/external/` and writes isolated results to
`data/external_validation/`. `scripts/run_external_temporal_diagnosis.py` additionally performs a
coarse external reference/target diagnosis checkpoint. Its scenario-window result is not a claim
of long-run adaptation recovery.

`scripts/run_cost_sensitivity.py` evaluates the held-out policy results under transparent cost
assumptions for missed security changes, benign false alarms, and unnecessary adaptation. It is a
sensitivity analysis, not a production cost estimate.

The literature package is an automated initial evidence set until two reviewers complete title/
abstract and full-text screening, exclusion reasons, study-level risk of bias, and the PRISMA
checklist. The current set contains 100 DOI records but only 12 downloaded open-access PDFs and
must not yet be described as a completed systematic review.

## Research positioning

Isolation Forest, SHAP, drift detection, and explanation-based monitoring are established areas.
The project contribution is the CloudTrail-specific protocol: real monthly observation, controlled
labelled perturbations, dual-signal diagnosis, protected adaptation, and unnecessary-adaptation
evaluation.

The current method extension adds label-free attribution-feature coupling: cosine similarity between
per-feature PSI drift and per-feature SHAP-attribution displacement. It is evaluated as a separate
`coupled_signal` policy and a conservative alignment ablation. The controlled benchmark is neutral;
the external checkpoint additionally tests a label-free largest-gap transfer calibration, which
improved recall in that small checkpoint but requires prospective validation.

See:

- `IMPLEMENTATION_PLAN.md`
- `docs/literature_matrix.csv`
- `docs/literature_review.md`
- `docs/research_gap.md`
- `LIMITATIONS.md`
- `docs/external_validation.md`
- `docs/final_validation.md`
- `docs/next_experiments.md`
- `docs/presentation_speaker_notes.md`
- `docs/attribution_feature_coupling.md`
- `docs/unsupervised_transfer_calibration.md`
- `review_2022_2026/automated_quality_audit_100.csv`
- `scripts/audit_review_set.py`
- `scripts/run_external_temporal_diagnosis.py`
- `scripts/run_cost_sensitivity.py`
- `scripts/compute_drift.py`
- `scripts/validate_submission_package.py`
