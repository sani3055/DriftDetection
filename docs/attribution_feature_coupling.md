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

This is an initial neutral result. It shows that coupling is measurable and reproducible, but the
current controlled scenarios do not yet demonstrate an advantage over the simpler dual rule.
That result is retained as a falsification/ablation finding rather than being presented as proof
of superiority.

## Reproduction

```text
python scripts/compute_drift.py
python scripts/run_controlled_benchmark.py
python scripts/run_adaptation_experiments.py
```

Outputs include `data/drift/coupling_drift.csv`, the `feature_attribution_coupling` and
`coupled_diagnosis` columns in `data/benchmark/diagnosis_results.csv`, and the `coupled_signal`
row in `data/benchmark/adaptation_summary.csv`.
