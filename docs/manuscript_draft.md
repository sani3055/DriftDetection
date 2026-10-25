# SHAP-Guided Drift Diagnosis for Adaptive Anomaly Detection in AWS CloudTrail

## Abstract

Unsupervised anomaly detectors for cloud audit logs can become unreliable when the behavior of a
cloud account changes. A change in the input distribution, however, does not necessarily mean
that the detector's decision logic has changed in a security-relevant way. This study evaluates
whether feature-distribution drift and drift in SHAP attribution distributions provide
complementary evidence for selective model adaptation. We use a real CloudTrail-style corpus of
1,939,207 records covering 45 monthly windows. Because the source is unlabeled and its primary
export stores month-level timestamps, real-data analysis is restricted to observational drift
analysis. We then construct a controlled semi-synthetic benchmark by injecting reproducible
benign and security-relevant perturbations into held-out real-data samples. An Isolation Forest
provides the primary detector, TreeSHAP validates attribution behavior, and a protected
adaptation controller compares static, periodic, feature-only, SHAP-only, and dual-signal
policies. The held-out controlled benchmark obtained a validation-tuned diagnosis macro-F1 of
0.7306. In the adaptation comparison, dual-signal and static policies had similar mean F1
(`-0.0028` paired difference; 95% bootstrap CI `[-0.0181, 0.0112]`), while dual-signal reduced
false-positive rate by `0.0885` (95% CI `[-0.1272, -0.0561]`; Benjamini–Hochberg adjusted
Wilcoxon `q=0.00043`). These values apply only to the defined semi-synthetic protocol. Detector
and sample-size ablations show material sensitivity, supporting the need for uncertainty reporting
rather than a single headline configuration. The study contributes a reproducible CloudTrail
drift-diagnosis protocol and an explicit separation between real-data observations and controlled
labelled evidence.

**Keywords:** CloudTrail, anomaly detection, concept drift, SHAP, explainable cybersecurity,
adaptive retraining, unsupervised learning.

## 1. Introduction

CloudTrail records provide an important audit trail for AWS activity, but the operational behavior
of an account changes over time. New services, regions, identity types, and legitimate automation
can produce distributional changes that resemble attack activity. An unsupervised detector that is
never updated may become stale, whereas indiscriminate retraining can absorb anomalous behavior or
create unnecessary model-version changes.

This paper studies a narrower question: can drift in the detector's explanation distribution help
decide whether an observed feature change warrants adaptation? The central distinction is between
input drift and attribution drift. Feature drift indicates that the observed records differ from
the reference population. Attribution drift indicates that the detector is relying on a different
set or direction of feature contributions. The two signals may therefore support a more cautious
adaptation policy.

The study makes four design commitments. First, it audits and preserves the real source corpus
without treating it as attack-labelled. Second, it uses chronological monthly windows rather than
randomized temporal splits. Third, it evaluates diagnosis on controlled perturbations whose labels
are hidden from the detector. Fourth, it reports unnecessary adaptation and uncertainty alongside
security-detection metrics.

The research questions are:

1. How do feature and attribution distributions change across the real monthly corpus?
2. Does attribution drift add information beyond feature drift in controlled diagnosis?
3. Can dual-signal gating reduce unnecessary adaptation while preserving controlled security
   detection?
4. How sensitive are conclusions to detector family, sample size, and random seed?

## 2. Related work and research gap

The literature matrix in `docs/literature_matrix.csv` covers CloudTrail anomaly detection,
unsupervised security monitoring, explainable cybersecurity, data/concept drift, and adaptive
retraining. Existing work establishes the individual components—Isolation Forest-style anomaly
detection, SHAP explanations, drift monitoring, and selective adaptation—but does not by itself
answer the CloudTrail-specific question evaluated here: whether a joint feature/attribution drift
protocol can gate adaptation while measuring unnecessary model changes.

The contribution is therefore methodological and empirical, not a claim that SHAP or drift
detection is newly invented. The novelty claim should remain limited to the reproducible protocol,
the separation of observational and controlled evidence, semantic perturbation benchmark, and
protected adaptation evaluation.

## 3. Materials and methods

### 3.1 Dataset and audit

The primary CSV contains 1,939,207 records and 18 columns. Its `eventTime` field is represented as
`YYYY-MM`, yielding 45 monthly windows. The richer raw export contains the same underlying corpus
with 1,330 distinct days and all 24 hours observed, as recorded in
`data_manifest/rich_timestamp_manifest.json`. It is used only for a temporal-resolution audit,
not as independent validation.

The source has no attack labels. The dataset manifest records the schema, row count, file size,
checksum, and concentration findings. In particular, one month and one event type dominate the
corpus, so all conclusions are reported with this limitation.

### 3.2 Temporal protocol and representation

The 45 monthly windows are divided chronologically into 27 training months, 9 validation months,
and 9 held-out test months. Event-level detector features are encoded using mappings learned from
training data only. The primary seven-column representation contains event name, event source,
AWS region, identity type, error code, instance type, and root-identity status. Monthly aggregate
features include volume, error rate, high-risk event rate, diversity, entropy, and concentration.

### 3.3 Detector and explanations

The primary detector is an Isolation Forest trained on the training-month sample. SHAP TreeExplainer
is applied to the fitted tree ensemble. The implementation verifies additivity against the
ensemble's internal tree-path output; it does not incorrectly describe the SHAP values as a direct
decomposition of scikit-learn's `decision_function`.

### 3.4 Drift monitoring and diagnosis

Feature drift combines categorical PSI/JS-type distribution changes with scalar distribution
shifts. Attribution drift combines normalized Wasserstein distance, top-k attribution overlap,
rank agreement, and signed attribution shifts. Thresholds are tuned only on validation scenarios.
The threshold policy maps low/low signals to stable, high feature and low attribution drift to
candidate benign drift, and high/high signals to candidate security-relevant drift.

### 3.5 Controlled benchmark

The benchmark applies semantic perturbations to real training-window samples. Benign scenarios
alter region, identity, or service composition. Security-relevant scenarios alter privilege,
defense, or credential-related event mixtures. Perturbation labels are used only for evaluation;
the detector and controller receive feature matrices and drift signals without labels. Five
validation seeds tune thresholds and ten held-out seeds provide the primary test comparison.

### 3.6 Selective adaptation and inference

The adaptation comparison includes static, periodic, feature-only, SHAP-only, and dual-signal
policies. Retraining uses replay data and candidates predicted normal by the baseline detector;
the protected controller does not blindly absorb all current-window records. Results include F1,
precision, recall, false-positive rate, trigger rate, and unnecessary-adaptation rate.

Uncertainty is estimated with deterministic percentile bootstrap intervals. Paired comparisons use
Wilcoxon tests, standardized paired differences, and Benjamini–Hochberg correction. Detector and
sample-size robustness artifacts are generated by `scripts/run_robustness_experiments.py`.

## 4. Results

### 4.1 Real-data observations

The real corpus exhibits substantial month-to-month variation in both feature and attribution
signals. The complete timeline is in `figures/monthly_drift_signals.png` and the saved values are
in `data/drift/combined_drift.csv`. These results are descriptive; without attack labels they do
not support a claim of attack-detection recall.

### 4.2 Controlled diagnosis

The validation-tuned threshold policy achieved macro-F1 `0.7306` on the validation scenarios.
The held-out confusion matrix is in `figures/diagnosis_confusion_matrix.png`. This result measures
classification of the defined perturbation scenarios, not naturally occurring incidents.

### 4.3 Adaptation comparison

The dual-signal policy triggered on 24.3% of held-out scenario windows and had zero unnecessary
adaptations under the implemented benchmark. Relative to static adaptation, its paired F1
difference was not statistically distinguishable from zero, while false-positive rate was lower
by 0.0885 with adjusted `q=0.00043`. Full values and intervals are in
`results/paired_inference.csv`; policy means are in `results/adaptation_summary.csv`.

### 4.4 Robustness

The detector ablation shows that One-Class SVM had higher controlled security recall (0.8080,
95% CI [0.7865, 0.8286]) but also higher benign false-positive rate (0.1301, 95% CI [0.1213,
0.1393]) than the primary Isolation Forest configuration. Local Outlier Factor was substantially
less sensitive in this representation. The sample-size ablation produced security recall of
0.0884 at 100 rows, 0.4918 at 200 rows, and 0.4152 at 500 rows. These findings are robustness
evidence and not grounds for selecting a favorable detector after seeing the results.

### 4.5 Independent external validation

To test portability beyond the primary corpus, the feature contract was applied to the public
Cloud Log Sampling Dataset. A detector was fitted on its benign-only training archive and evaluated
on the labeled mixed test archive. Isolation Forest achieved precision 0.3306, recall 0.7137,
F1 0.4519, and false-positive rate 0.1738. Local Outlier Factor achieved higher recall (0.9954)
but a higher false-positive rate (0.2088), while One-Class SVM produced recall 0.0008. This
external result supports portability of the representation but also confirms that detector choice
materially affects conclusions. Because the external files are not aligned to the primary
month-level drift protocol, this is detector-only validation; it is not presented as validation
of the SHAP drift or adaptation policy.

### 4.6 External temporal diagnosis checkpoint

An additional external checkpoint used benign February records as a reference window and April
2026 scenario windows as target windows. Primary thresholds were transferred without target-label
tuning. At the scenario-window level, feature-only, SHAP-only, and dual-signal policies all
obtained precision 0.9091, recall 1.0000, F1 0.9524, and false-positive rate 0.5000. The identical
results are a neutral transfer finding rather than evidence of dual-signal superiority: one benign
target window was falsely flagged and the coarse window unit provides little statistical power.
The external corpus does not provide enough post-adaptation windows to evaluate recovery or
long-run retraining cost.

## 5. Discussion

The results support a cautious interpretation: attribution-aware gating can reduce adaptation
activity and false-positive rate in the defined controlled benchmark, but the benefit is not a
universal increase in F1. Detector and sample-size sensitivity further indicate that a deployment
should calibrate thresholds and minimum window sizes using representative data rather than copy
the reported values.

The most defensible contribution is the protocol. It prevents an unlabeled month-level corpus
from being overinterpreted while still enabling a controlled test of diagnosis and adaptation.
The neutral external temporal checkpoint also demonstrates that attribution drift does not
automatically add decision value at every evaluation granularity. This makes the research question
falsifiable rather than assuming that the dual signal will transfer.

## 6. Threats to validity

The corpus is a single source and lacks attack labels. Controlled perturbations are semantic but
not real attack campaigns. Ordinal encoding introduces artificial geometry. Month-level primary
features cannot establish event-order or causal-session behavior, although the richer source shows
that a future submonthly study is technically possible. The adaptation controller is an offline
research prototype and does not enforce AWS IAM changes. These limitations prevent claims of
production security effectiveness or guaranteed Q1/Q2 acceptance.

## 7. Reproducibility and availability

The repository contains configuration files, audit manifests, scripts, tests, result CSVs, figures,
and the literature matrix. Reproduction uses `python scripts/run_all.py`; the full test suite is
run with `python -m pytest tests -q`. External source files remain read-only and are referenced by
path and checksum rather than copied into the repository.

## 8. Submission checklist

- [x] Separate real-data observation from controlled labelled evaluation.
- [x] Chronological split and validation-only threshold tuning.
- [x] Detector, sample-size, and seed robustness artifacts.
- [x] Bootstrap intervals, paired effects, and corrected p-values.
- [x] Explicit limitation that same-corpus richness is not independent validation.
- [x] Obtain and document an independent labeled CloudTrail dataset for detector portability.
- [x] Add an aligned external reference/target temporal diagnosis checkpoint; report its neutral
  result and retain the limitation that full adaptation recovery is not validated.
- [ ] Add external validation of the full SHAP-drift/adaptation recovery protocol and, if possible,
  analyst-confirmed incident cases.
- [ ] Lock the final dependency versions and archive the exact source snapshot.
- [ ] Complete venue-specific formatting, reference verification, and supervisor review.
