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

### Review demonstration

A small local Streamlit interface is available in `streamlit_app.py`. It replays
saved held-out scenarios through the actual diagnosis rule and shows plain-English
decisions, including missed cases. It does not retrain models or connect to AWS.

On the configured Windows machine, double-click `Start_Review_Demo.cmd`, then open
<http://127.0.0.1:8501>. See `docs/review_demo.md` for setup and a short walkthrough.
Optional interface dependencies are in `requirements-demo.txt`.

### Research pipeline

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
checklist. The current Project 20106UG03 collection contains 101 selected primary journal
articles, 101 locally retained PDFs and 101 AI-assisted summaries. It is a bounded structured
evidence review, not a completed exhaustive systematic review or independent critical
appraisal. Downloaded PDFs and raw full-text archives are not redistributed here.

### Current papers and review collection

- [Research manuscript for guide review](outputs/CloudTrail_Journal_Manuscript_Guide_Review_Final.docx)
- [Structured review draft](20106UG03/20106UG03_Review_Paper_Guide_Draft.docx)
- [Consolidated summaries of 101 journal articles](20106UG03/20106UG03_Consolidated_Journal_Paper_Summaries.docx)
- [Paper register](20106UG03/Paper_Register.csv)
- [PRISMA completion map](20106UG03/PRISMA_2020_Completion_Map.md)
- [Review package status and limitations](20106UG03/README_FOR_GUIDE.md)

The latest empirical evidence includes candidate-update safety stress tests, matched static
baselines and a separately sourced labelled synthetic transfer test. See
`docs/JOURNAL_V5_SAFETY_FINDINGS.md` and `docs/INDEPENDENT_LABELLED_SYNTHETIC_FINDINGS.md`.
Synthetic transfer is not validation on a second independent real AWS environment.
Neither manuscript has been submitted or accepted; Q1/Q2 acceptance is not guaranteed.

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
