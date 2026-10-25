# Literature Review: Attribution-Guided Drift Diagnosis in CloudTrail Anomaly Detection

## Scope and protocol

Phase 1 reviewed primary papers and official documentation covering five connected areas:

1. unsupervised anomaly detection;
2. explainable feature attribution;
3. drift detection without continuous labels;
4. selective or drift-type-aware adaptation;
5. CloudTrail and production attribution monitoring.

The initial verified matrix is stored in `docs/literature_matrix.csv`. It is a core matrix rather
than a claim of a completed systematic review. The automated 100-record evidence set is a triage
set, not the final included corpus. Its audit is stored in
`review_2022_2026/automated_quality_audit_100.csv`; this audit does not make inclusion decisions.
The set currently contains 18 records with a direct cloud/audit signal, while 82 are adjacent
security, IoT, industrial, log, or general drift studies. This is useful for gap discovery, but
the CloudTrail-specific review must be rebuilt after human screening and journal verification.

Before journal submission, the search should be expanded across IEEE Xplore, ACM Digital Library,
Scopus/Web of Science, ScienceDirect, SpringerLink, and Google Scholar using combinations of:

```text
CloudTrail AND anomaly detection
cloud audit log AND machine learning
feature attribution drift OR SHAP drift
concept drift AND cybersecurity AND adaptation
unlabeled drift detection AND intrusion detection
normality shift AND anomaly detection
```

Each candidate paper must be verified for title, authors, venue, year, DOI, dataset, labels,
temporal protocol, and evaluation design. Unverified references from earlier drafts must not be
presented as established literature.

## What the literature establishes

### 1. Isolation Forest is a baseline, not the contribution

Isolation Forest provides a practical unsupervised detector for a corpus without attack labels.
Its use is justified as a reproducible baseline and as the detector whose behavior will be
monitored. The algorithm itself is established and should not be claimed as novel.

### 2. SHAP provides attribution, not security causality

SHAP gives feature-level additive contributions to a model output. In this project, SHAP values
are evidence about the behavior of the trained detector, not proof that a feature caused an attack.
The implementation must validate additivity, output polarity, feature order, and stability before
using attribution distributions as monitoring signals.

### 3. Feature drift alone is not necessarily model-relevant drift

The drift literature distinguishes a change in the observed input distribution from a change that
actually harms the deployed model. Unlabeled feature-based detectors can generate false alarms
when the observed change is unrelated to the decision process. This supports monitoring both raw
feature distributions and model-dependent signals.

### 4. Normality shift is especially important for anomaly detection

Anomaly detectors trained with few or no positive attack examples can be affected strongly when
legitimate normal behavior changes. This supports the project's focus on benign behavioral change,
false positives, and unnecessary retraining rather than only attack recall.

### 5. Drift type can guide adaptation

Prior work shows that identifying how drift occurs can improve the choice or timing of adaptation.
This supports the idea of a diagnosis layer before retraining, but the present project must justify
its diagnosis signals specifically for CloudTrail behavior.

### 6. Explanation-based drift monitoring is already an active area

AWS production monitoring documentation and recent research such as Lee et al.'s SHAP-based
unsupervised drift detection, OWAD's normality-shift explanation/adaptation framework, and
explanation-instability monitoring for adversarial IDS inputs show that attribution changes are
not an untouched concept. Therefore, the project's novelty must not be phrased as inventing SHAP
drift. The contribution is the CloudTrail-specific empirical protocol, the separation of real
observational data from controlled labelled perturbations, and the test of whether attribution
drift improves protected adaptation decisions.

## Evidence-to-gap mapping

| Literature evidence | Remaining problem | Project response |
|---|---|---|
| CloudTrail anomaly/XAI pipelines exist | They do not establish attribution-conditioned drift gating on this real corpus | Evaluate drift and adaptation explicitly |
| Feature-based drift detection can over-alert | Any distribution change is not necessarily model-relevant | Compare feature drift with SHAP drift |
| Normality shift harms zero-positive anomaly detection | Adaptation can also absorb contamination or cause unnecessary retraining | Measure false positives, adaptation frequency, and protected retraining |
| Drift-type-aware adaptation exists | Existing methods are not tailored to CloudTrail attribution behavior | Use interpretable dual-signal diagnosis |
| Explanation-based drift monitoring exists in adjacent IDS/production work | General explanation drift is not evidence for CloudTrail security relevance | Use a real CloudTrail corpus and controlled security perturbations |

## Defensible research gap

The defensible gap is not that SHAP, drift detection, or CloudTrail anomaly detection is new.

> There is a need for a reproducible CloudTrail-specific evaluation of whether model-attribution
> drift adds decision-relevant information beyond feature-distribution drift when controlling
> adaptation of an unlabeled anomaly detector.

The study addresses this gap through:

1. an observational monthly analysis of the existing real corpus;
2. a controlled semi-synthetic benchmark because the corpus has no attack labels;
3. a dual-signal diagnosis with a review-required state for inconsistent signals;
4. direct comparison against static, periodic, feature-only, and SHAP-only adaptation;
5. evaluation of unnecessary adaptation and detection delay in addition to detection metrics.

The study must additionally compare mean absolute attribution displacement and top-k attribution
overlap baselines, because these signals are already used in recent security work. It must also
test whether any dual-signal benefit transfers to aligned external temporal windows; detector-only
external scores are not sufficient evidence for transfer of the complete drift-and-adaptation
protocol.

## Claims that are prohibited

The final paper must not claim:

- that this is the first use of SHAP drift;
- that the original CSV contains ground-truth attacks;
- that month-level data support event-level causal sessions;
- that attribution identifies the true cause of an attack;
- that a single synthetic injection result proves production security value;
- that journal acceptance or Q1/Q2 placement is guaranteed.

The project draft's reference to a specific Pawlicki et al. attribution-drift paper is not included
in the verified matrix because its full bibliographic record was not established during this phase.
It may be added after the exact title, venue, year, and DOI are confirmed.

The E2D2 and EDDI records are conference/workshop evidence rather than journal papers and must not
be counted toward the guide's 100 journal-paper requirement.
