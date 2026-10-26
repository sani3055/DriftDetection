# Unsupervised Transfer Calibration

## Purpose

The primary-corpus coupling threshold is learned from validation scenarios. Directly transferring
that threshold to another CloudTrail corpus produced a conservative but low-recall result. This
experiment tests whether the coupling threshold can be recalibrated from the unlabeled
target-window score distribution without using attack labels.

## Protocol

1. Fit the detector on the external benign training archive.
2. Use benign February records as the reference and April scenario windows as targets.
3. Compute feature drift, SHAP drift, and conservative attribution-feature coupling.
4. Keep the feature and SHAP thresholds fixed from the primary validation protocol.
5. Select the coupling threshold as the midpoint of the largest gap among target windows that
   exceed both transferred feature and SHAP thresholds.
6. Use labels only after diagnosis to compute evaluation metrics.

The rule is label-free, deterministic, and deliberately separated from the source-tuned result.
It is not a replacement for prospective calibration on a larger stream.

## Current result

The largest-gap threshold was `0.4990795305`. At the scenario-window level, the resulting
`unsupervised_coupled_signal` policy achieved:

| Precision | Recall | F1 | False-positive rate |
|---:|---:|---:|---:|
| 1.0000 | 1.0000 | 1.0000 | 0.0000 |

The external target contains 10 attack windows, one benign target window, and one benign reference
window. These values are a transfer checkpoint, not production performance.

## Reproduction

```text
python scripts/run_external_temporal_diagnosis.py
```

The per-window output is in `data/external_validation/external_temporal_diagnosis.csv`; metrics
and calibration provenance are in the corresponding JSON files in that directory.
