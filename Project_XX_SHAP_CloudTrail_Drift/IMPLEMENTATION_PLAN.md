# SHAP-Guided Drift Diagnosis for AWS CloudTrail

## Project direction

This project reuses the real CloudTrail-style dataset from the earlier CloudGuard project:

```text
D:\Projects\CloudGuard\data\dec12_18features.csv
```

The dataset is treated as an external, read-only input. It is not copied into this repository.
The final study separates two kinds of evidence:

1. **Observational real-data analysis:** monthly changes in CloudTrail behavior, anomaly scores,
   and SHAP attribution distributions.
2. **Controlled semi-synthetic evaluation:** labelled benign and security-relevant perturbations
   injected into real-data windows for evaluating diagnosis and adaptation.

The original corpus is unlabeled and its `eventTime` field is month-level. Therefore, the study
must not claim event-level causal sessions, real-time sequence reconstruction, or ground-truth
attack recall on the unmodified corpus.

## Research objective

Investigate whether feature-distribution drift and SHAP-attribution drift provide complementary
signals for deciding when an unsupervised CloudTrail anomaly detector should be adapted.

The contribution is methodological and empirical rather than a new Isolation Forest or SHAP
algorithm:

- a reproducible real-data drift protocol for CloudTrail-style logs;
- identity-aggregated and time-window behavioral representations;
- attribution-aware drift diagnosis;
- selective adaptation evaluated by detection quality and unnecessary retraining cost;
- a controlled labelled benchmark built on the real corpus without pretending that its original
  records have attack labels.

## Research questions

- **RQ1:** How do feature distributions, anomaly scores, and SHAP attributions change across
  monthly CloudTrail windows?
- **RQ2:** Does attribution drift provide information that is not captured by feature drift alone?
- **RQ3:** Can dual-signal diagnosis reduce unnecessary adaptation without degrading detection on
  controlled security-relevant changes?
- **RQ4:** How sensitive are the conclusions to detector choice, drift metric, window size, and
  random seed?

## Non-negotiable research rules

- No invented results or conclusions.
- The original CSV is never modified.
- Dataset provenance, checksum, row count, schema, and limitations are recorded.
- Chronological splits are used for drift experiments; random splits are legacy baselines only.
- The original corpus is not treated as attack-labelled.
- Controlled injection labels are hidden from the detector and adaptation controller.
- Thresholds are tuned on validation windows and evaluated on held-out windows/seeds.
- No feature may use attack, scenario, or future-window labels.
- SHAP additivity and output polarity are explicitly tested.
- Every phase ends with tests, validation evidence, limitations, and an approval gate.

## Phase plan

### Phase 0 — Reproducibility and dataset-audit scaffolding

Status: **completed**

Deliverables:

- `configs/base.yaml`
- deterministic seed, configuration, and logging utilities;
- read-only CSV audit utility;
- dataset manifest output;
- pinned dependency input file;
- initial unit tests.

Validation gate:

- pytest passes;
- the external CSV is readable without modification;
- the manifest records the actual row count and schema;
- repeated audit runs produce the same manifest apart from runtime fields, if any.

Validation evidence is recorded in `docs/phase_0_validation.md`.

### Phase 1 — Literature survey and research-gap matrix

Status: **completed for the core verified matrix; final PRISMA review remains open**

Create:

```text
docs/literature_matrix.csv
docs/literature_review.md
docs/research_gap.md
```

Cover CloudTrail anomaly detection, unsupervised detection, XAI for cybersecurity, concept/data
drift, adaptive retraining, and safe security automation. For each paper record its dataset,
labels, temporal resolution, detector, drift detector, adaptation policy, explanation method,
metrics, and limitations. Verify DOI, venue, and dataset claims before using them.

### Phase 2 — Temporal data protocol

Status: **completed**

Build chronological monthly partitions and define:

- early reference/training period;
- validation period for thresholds and policy selection;
- held-out test period;
- minimum window-size and sample-count rules;
- handling for the highly imbalanced months and dominant event types.

Resolve and document the report/CSV row-count discrepancy before final evaluation.

### Phase 3 — Feature representations

Status: **completed for the reproducible event-level baseline and monthly aggregate protocol**

Reproduce the legacy five-feature representation as a baseline, but do not treat `hour` as valid
unless a richer timestamp source is obtained. Build window-level and identity-aggregated features:

- event-name and event-source frequencies;
- region and identity-type distributions;
- error-code rates;
- service and principal diversity;
- entropy and concentration measures;
- high-risk API frequency;
- request-parameter distributions where reliable.

Raw ARNs, access keys, and high-cardinality identifiers are not used directly as model features.

### Phase 4 — Detector baselines

Status: **completed for the primary Isolation Forest baseline**

Compare:

1. legacy Isolation Forest;
2. extended-feature Isolation Forest;
3. one additional unsupervised detector such as One-Class SVM or Local Outlier Factor;
4. optional autoencoder sensitivity baseline if runtime permits.

The old `model.pkl` is retained as a legacy reference, but all headline results use models rebuilt
from reproducible scripts.

### Phase 5 — SHAP explanation validation

Status: **completed**

Explain the exact model score used for anomaly decisions. Store per-window attribution vectors,
top-k features, signed attribution distributions, absolute-attribution rankings, and explanation
runtime. Test additivity, sign interpretation, feature-order consistency, and attribution
stability.

### Phase 6 — Real-data drift analysis checkpoint

Status: **completed for the observational monthly analysis**

Monitor monthly windows against the reference period with KS, PSI, Wasserstein distance, and
Jensen-Shannon divergence. Separately monitor anomaly-score drift and SHAP-attribution drift.

Required outputs:

- feature-drift timeline;
- score-drift timeline;
- SHAP-drift timeline;
- changed-feature and changed-attribution tables;
- window-size sensitivity analysis.

This phase is observational. Precision/recall for drift diagnosis are not claimed on the original
unlabeled corpus.

### Phase 7 — Controlled semi-synthetic benchmark

Status: **completed**

Inject labelled perturbations into real-data windows.

Benign scenarios include service-volume changes, new-region mixtures, new identity proportions,
and altered but non-malicious error patterns. Security scenarios include privilege escalation,
defense evasion, credential-access, and unusual high-risk API mixtures.

Each scenario records its seed, window, magnitude, injected rows, and ground-truth type. The
detector receives only the resulting feature stream, never the labels.

### Phase 8 — Drift diagnosis

Status: **completed with threshold-based diagnosis and held-out evaluation**

Implement an interpretable threshold rule first:

```text
low feature drift + low SHAP drift  -> stable
high feature drift + low SHAP drift -> candidate benign drift
high feature drift + high SHAP drift -> candidate security drift
inconsistent signals                -> review required
```

Only add Logistic Regression or another classifier if the threshold model is inadequate. Tune on
validation scenarios and evaluate on held-out scenarios.

### Phase 9 — Selective adaptation

Status: **completed for the protected policy comparison**

Compare static, periodic, feature-drift-only, SHAP-only, and dual-signal adaptation.

Adaptation uses replay data and high-confidence normal candidates. Suspicious windows are
quarantined rather than blindly added to the training set. Every model version and adaptation
decision is logged.

### Phase 10 — Experiments and statistical evaluation

Status: **completed for the implemented benchmark metrics and paired Wilcoxon comparison**

Use at least 10 paired seeds where feasible. Report detection metrics, diagnosis metrics, delay,
unnecessary-adaptation rate, model-version count, recovery after drift, and SHAP overhead.

Use confidence intervals, paired Wilcoxon tests, effect sizes, and multiple-comparison correction.
Evaluation reads saved result files and never retrains models.

### Phase 11 — Figures, tables, and manuscript artifacts

Status: **completed for generated result summaries and core figures**

Generate the pipeline diagram, data audit table, drift timelines, diagnosis confusion matrices,
adaptation comparison, ablations, runtime analysis, and limitations section. Numerical claims are
written only from generated result files.

### Phase 12 — Reproducibility package

Status: **completed for the generated submission package; human manuscript and PRISMA gates remain**

Finalize:

```text
README.md
LIMITATIONS.md
requirements.in
requirements.txt
scripts/run_pipeline.py
tests/test_end_to_end.py
```

The final repository distinguishes observational real-data results from controlled
semi-synthetic results. The generated package also contains the consolidated review document,
project report draft, journal shortlist, audit CSV, PRISMA protocol, and progress presentation.

### Journal-strengthening extension

Status: **completed for detector portability and a coarse external temporal checkpoint; full independent temporal recovery remains open**

Added:

- detector-family ablations using Isolation Forest, Local Outlier Factor, and One-Class SVM;
- sample-size sensitivity analysis for 100, 200, and 500 event windows;
- deterministic bootstrap confidence intervals;
- paired standardized effects, Wilcoxon tests, and Benjamini–Hochberg correction;
- mean absolute SHAP-attribution displacement as an explicit drift metric;
- automated cost-sensitive policy analysis across missed-security, false-alarm, and unnecessary-adaptation cost assumptions;
- attribution-feature coupling using aligned per-feature PSI and SHAP displacement, with a separate coupled adaptation policy;
- conservative coupling ensemble using cosine and centered alignment, plus a label-free largest-gap
  transfer-calibration experiment kept separate from source-tuned results;
- richer-source timestamp-resolution audit without treating the same corpus as external data;
- manuscript draft and venue-readiness checklist in `docs/manuscript_draft.md`.

Research updates added during the literature reassessment:

- `scripts/audit_review_set.py` produces a non-decisive relevance and metadata-risk audit for the
  automated 100-record evidence set;
- `review_2022_2026/automated_quality_audit_100.csv` shows that only 18 records currently have a
  direct cloud/audit signal and 82 are adjacent studies requiring human confirmation;
- recent close comparators are recorded in `docs/literature_matrix.csv`, including SHAP-based
  unsupervised drift detection and explanation-instability monitoring;
- the defensible novelty claim is now limited to CloudTrail-specific dual-signal adaptation
  gating, protected retraining, and independent temporal validation;
- `journal_targets.md` no longer treats Computers & Security as the default target because its
  current official scope warns of an AI/ML moratorium.

Detector-only validation is now completed on an independent labeled CloudTrail corpus, and a coarse
reference/target temporal diagnosis checkpoint has been added. The source-tuned coupling result
shows negative transfer, while the separately reported label-free largest-gap calibration succeeds
on the current small checkpoint. This does not establish full post-adaptation recovery. The
remaining evidence gap is multi-period independent temporal recovery evaluation or
analyst-confirmed incident data.

## Intended repository structure

```text
configs/
docs/
src/data/
src/drift/
src/evaluation/
src/explain/
src/features/
src/models/
src/adaptation/
src/experiments/
src/reporting/
src/utils/
tests/
data_manifest/
results/
figures/
tables/
```

## Current status

Phases 0–12 are implemented for the current research prototype and validated with the automated
test suite. The core reproducibility and submission package is present. Remaining work is the
human-controlled submission gate: two-reviewer full-text PRISMA screening, risk-of-bias scoring,
current journal verification, supervisor review, and a stronger independent post-adaptation
validation if the team can obtain suitable temporal or incident labels.
