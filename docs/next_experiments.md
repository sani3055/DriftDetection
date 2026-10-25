# Highest-value next experiments

The current project is a defensible research prototype. The following extensions would improve
journal strength in priority order. They are not silently claimed as completed results.

## 1. Rolling-origin temporal validation

Repeat the complete diagnosis and adaptation protocol over multiple chronological reference and
target pairs rather than one transferred external checkpoint. Report per-period F1, false-positive
rate, detection delay, recovery time, adaptation count, and bootstrap intervals. This is the most
important technical addition because the current external checkpoint is neutral and scenario-window
based.

## 2. Independent cloud-audit corpora

Add at least one more legally accessible cloud or audit-log corpus with a compatible temporal
protocol. Keep the primary CloudTrail-style corpus, the controlled perturbation benchmark, and each
external corpus analytically separate.

## 3. Attribution-drift ablations

Compare mean absolute attribution displacement, top-k attribution overlap, signed attribution
shift, and the existing aggregate SHAP drift score. Tune all thresholds on validation periods only
and report whether the dual policy is robust to the drift definition.

## 4. Cost-sensitive adaptation analysis

Vary the relative cost of an unnecessary retraining, a delayed adaptation, and a missed
security-relevant change. Report a policy utility curve instead of relying only on F1. This makes
the operational value of the adaptation gate explicit.

## 5. Expert-validated security scenarios

Have a security practitioner review the injected benign and security-relevant scenarios for
semantic plausibility. Record the review protocol and disagreements; do not present synthetic
scenario labels as real incident labels.

## 6. Final systematic-review completion

Complete database-specific searches, two-reviewer screening, full-text exclusion reasons,
risk-of-bias judgments, and the PRISMA 2020/PRISMA-S reporting fields before calling the review
complete. The current 100-record set remains an automated triage set with 12 downloaded open-access
PDFs.
