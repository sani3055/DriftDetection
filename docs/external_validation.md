# Independent external validation

## Dataset

The external validation uses the public [Cloud Log Sampling Dataset](https://github.com/ArielCyber/cloud_log_sampling).
It is separate from the CloudGuard-derived corpus used in the primary study. The downloaded
archives are recorded in `data/external_validation/external_validation_manifest.json`.

- benign-only training records: 16,495
- labeled mixed test records: 24,087
- test attack records: 2,585
- test benign records: 21,502
- attack scenarios: 10

The detector is fitted only on the benign-only training archive. The labeled test archive is used
only for evaluation. The same seven-feature contract is reconstructed from the nested CloudTrail
JSON, with category maps learned from training data only and unseen categories encoded as `-1`.

## Results

| Detector | Precision | Recall | F1 | False-positive rate |
|---|---:|---:|---:|---:|
| Isolation Forest | 0.3306 | 0.7137 | 0.4519 | 0.1738 |
| Local Outlier Factor | 0.3643 | 0.9954 | 0.5334 | 0.2088 |
| One-Class SVM | 0.0215 | 0.0008 | 0.0015 | 0.0042 |

These results provide independent evidence that the feature contract can be applied to a separate
labeled CloudTrail corpus, but also demonstrate detector sensitivity.

## External temporal diagnosis checkpoint

An aligned reference/target-window checkpoint is now implemented by
`scripts/run_external_temporal_diagnosis.py`. It uses benign February records as the reference
window and April 2026 scenario windows as the target. The Isolation Forest is fitted only on the
benign training archive; attack labels are used only after diagnosis for evaluation. The transferred
primary thresholds produced the following **scenario-window-level** results:

| Policy | Precision | Recall | F1 | False-positive rate |
|---|---:|---:|---:|---:|
| Feature-only | 0.9091 | 1.0000 | 0.9524 | 0.5000 |
| SHAP-only | 0.9091 | 1.0000 | 0.9524 | 0.5000 |
| Dual-signal | 0.9091 | 1.0000 | 0.9524 | 0.5000 |
| Coupled-signal | 1.0000 | 0.1000 | 0.1818 | 0.0000 |
| Unsupervised coupled calibration | 1.0000 | 1.0000 | 1.0000 | 0.0000 |

The feature-only, SHAP-only, and dual policies are identical at this coarse window level, while
the source-tuned coupled policy is conservative and misses most external attack windows. This
negative transfer result is important. The additional unsupervised calibration uses the largest
gap in the unlabeled target coupling-score distribution; its threshold was `0.4991` and it
recovered all 10 attack windows without flagging the benign target window in this checkpoint.
This is promising but small evidence: the target has only 12 scenario windows and the calibration
threshold is estimated from the target stream. One benign target window is falsely flagged by the
other policies. The result demonstrates why event-level or multi-window evaluation is required.
Outputs are stored in `data/external_validation/external_temporal_diagnosis.csv`,
`external_temporal_diagnosis_metrics.json`, and `external_temporal_diagnosis_manifest.json`.

The detailed protocol is documented in `docs/unsupervised_transfer_calibration.md`.

The external corpus still does not contain enough independent post-adaptation windows to validate
recovery, retraining safety, or long-run adaptation cost. Those claims remain open.

## Reproduction

```text
python scripts/run_external_validation.py
python scripts/run_external_temporal_diagnosis.py
```

The outputs are:

- `data/external_validation/external_detector_metrics.csv`
- `data/external_validation/external_scenario_metrics.csv`
- `data/external_validation/external_validation_manifest.json`
- `data/external_validation/external_temporal_diagnosis.csv`
- `data/external_validation/external_temporal_diagnosis_metrics.json`
- `data/external_validation/external_temporal_diagnosis_manifest.json`
