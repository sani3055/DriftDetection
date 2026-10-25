# Research Gap and Study Positioning

## Problem statement

An unsupervised anomaly detector trained on historical CloudTrail behavior may encounter a later
window whose feature distribution has changed. A feature-distribution alarm alone cannot establish
that the detector's useful behavior has degraded. Retraining on every alarm can create unnecessary
model changes, absorb contaminated data, and make operational auditing harder.

## Proposed question

Does comparing conventional feature-distribution drift with drift in the detector's SHAP
attribution distribution improve the decision of whether to adapt an unsupervised CloudTrail
anomaly detector?

## Position relative to prior work

The following are established and are used as baselines or design inputs:

- Isolation Forest for unsupervised anomaly scoring;
- SHAP for feature attribution;
- statistical and unlabeled drift detection;
- drift-type-aware and selective adaptation;
- explanation-based drift monitoring in adjacent security and production settings.

The project contribution is narrower:

1. reuse and audit a real CloudTrail-style corpus;
2. respect its monthly temporal resolution and absence of attack labels;
3. separate real-data observation from controlled labelled perturbation evaluation;
4. test whether attribution drift adds information to feature drift for adaptation gating;
5. report unnecessary adaptation, delay, and overhead as first-class outcomes.

## Updated literature boundary (October 2026)

The novelty claim has been stress-tested against recent and closely related work. SHAP-based
drift detection is already established in unsupervised cybersecurity settings: Lee et al. use
SHAP-derived drift scores for DGA detection and explicitly motivate label-free model monitoring
([DOI](https://doi.org/10.32604/cmc.2023.040235)). OWAD already addresses unsupervised normality
shift, explanation, and adaptation for security anomaly detection
([NDSS paper](https://www.ndss-symposium.org/ndss-paper/anomaly-detection-in-the-open-world-normality-shift-detection-explanation-and-adaptation/)).
Recent work also treats attribution instability and top-k explanation overlap as operational
signals for adversarial monitoring in intrusion detection ([Springer article](https://link.springer.com/article/10.1007/s10207-026-01299-x)).

Accordingly, this project must not claim to be the first to use SHAP for drift or the first to
use explanations for security monitoring. The defensible gap is the combination of:

1. a CloudTrail-specific audit-log protocol rather than a generic network or DGA benchmark;
2. explicit separation of observational real data from controlled labelled evaluation;
3. comparison of feature drift, attribution drift, and their joint decision value;
4. protected adaptation with an explicit unnecessary-adaptation and contamination-risk outcome;
5. independent temporal validation of the complete diagnosis-and-adaptation protocol.

The last item is currently an evidence requirement, not a completed result.

## Study design implication

The original corpus cannot support a fully labelled precision/recall evaluation by itself. The
study therefore has two result tracks:

- **Track A — Real corpus:** distributional drift, score drift, attribution drift, and stability
  analysis only.
- **Track B — Controlled benchmark:** labelled benign/security perturbations applied to real-data
  windows, used for diagnosis and adaptation metrics.

All paper tables and figures must label which track produced them.

## Primary hypotheses

- **H1:** Some real monthly changes will alter feature distributions without proportionally changing
  the detector's attribution profile.
- **H2:** Dual-signal diagnosis will distinguish controlled benign and security perturbations more
  accurately than feature drift alone, subject to validation on held-out scenarios.
- **H3:** Selective adaptation will reduce unnecessary retraining relative to drift-blind adaptation
  while preserving detection performance on controlled security perturbations.

These are testable hypotheses, not expected results. A failure to observe the proposed separation
will be reported as a result.

## Stronger hypotheses and falsification tests

- **H1 (incremental signal):** attribution drift improves diagnosis over feature drift alone.
  Falsification: report paired performance and confidence intervals showing no improvement.
- **H2 (operational value):** dual-signal gating reduces unnecessary adaptation at a matched
  security-recall level. Falsification: report equal or worse adaptation cost after calibration.
- **H3 (transfer):** the direction of the dual-signal effect persists on an independent temporal
  CloudTrail-style corpus. Falsification: report a non-transfer result instead of generalizing.

The evaluation must include explanation-drift baselines based on mean absolute SHAP displacement
and top-k attribution overlap, because these signals are already used in recent security work.
The project should also report calibration, detection delay, false-positive burden, model-version
count, and contamination checks rather than only macro-F1.
