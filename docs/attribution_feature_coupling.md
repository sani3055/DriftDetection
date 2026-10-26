# Attribution-Feature Drift Coupling

## Method

The project now computes a label-free coupling score between distributional feature drift and
model-attribution drift. For the shared CloudTrail categorical features
(`eventName`, `eventSource`, `awsRegion`, `userIdentitytype`, and `errorCode`), the method builds:

1. a per-feature PSI drift vector; and
2. a per-feature absolute SHAP-attribution displacement vector.

The coupling score is their cosine similarity:

```text
coupling = cosine(feature_PSI_vector, attribution_displacement_vector)
```

The implementation also records centered Pearson alignment, rank alignment, and a conservative
alignment score:

```text
conservative_score = min(cosine_coupling, centered_alignment)
```

This minimum operator is an ablation, not a claim that it is universally optimal.

The score is bounded between 0 and 1. It is computed without scenario labels, attack labels, or
future-window information.

## Interpretation

The coupled diagnosis uses feature drift, SHAP drift, and the coupling threshold:

| Signal pattern | Interpretation |
|---|---|
| low feature drift + low SHAP drift | stable |
| high feature drift + low SHAP drift | likely benign distributional drift |
| high feature drift + high SHAP drift + high coupling | security-relevant/model-relevant drift |
| low feature drift + high SHAP drift + low coupling | hidden model instability |
| conflicting or weakly aligned signals | review required |

## Current result

The method is integrated into the controlled benchmark and adaptation comparison as the
`coupled_signal` policy. Its validation macro-F1 is `0.4384` under the five validation seeds, while
the held-out test diagnosis currently produces the same category counts as the existing dual rule.
The coupled policy also matches the existing dual policy in the current adaptation benchmark:
trigger rate `0.242857`, unnecessary-adaptation rate `0.000000`, mean F1 `0.287314`, and FPR
`0.339707`.

On the aligned external scenario-window checkpoint, the transferred coupling threshold produced
precision `1.0000`, recall `0.1000`, F1 `0.1818`, and FPR `0.0000`. This negative transfer result
shows that the coupling threshold is not yet portable across corpora.

The source-tuned conservative threshold is also neutral in the controlled benchmark. On the
external checkpoint, both source-tuned coupling variants obtained precision `1.0000`, recall
`0.1000`, F1 `0.1818`, and FPR `0.0000`; this is negative transfer caused by a threshold calibrated
on the primary corpus.

## Unsupervised transfer calibration

The external script separately tests a label-free transfer calibration. Among target windows that
exceed the transferred feature and SHAP thresholds, it places the coupling threshold at the
largest observed gap in the conservative-score distribution. The threshold was `0.4991`, selected
without attack labels. At scenario-window level this obtained precision `1.0000`, recall `1.0000`,
F1 `1.0000`, and FPR `0.0000` on the current external checkpoint.

This is encouraging but small evidence: the external target contains only 12 scenario windows, and
the threshold is estimated from the target score distribution. Prospective multi-period validation
is required before claiming general transfer.

## Reproduction

```text
python scripts/compute_drift.py
python scripts/run_controlled_benchmark.py
python scripts/run_adaptation_experiments.py
```

Outputs include `data/drift/coupling_drift.csv`, the coupling and diagnosis columns in
`data/benchmark/diagnosis_results.csv`, the coupled policy rows in
`data/benchmark/adaptation_summary.csv`, and the external transfer-calibration metrics in
`data/external_validation/external_temporal_diagnosis_metrics.json`.
