# Phase 1 Validation

Status: **Complete; waiting for approval before Phase 2**

## Files created

- `docs/literature_matrix.csv`
- `docs/literature_review.md`
- `docs/research_gap.md`
- `tests/test_literature_artifacts.py`

## Literature artifact validation

The matrix contains 13 records covering:

- Isolation Forest;
- SHAP;
- legitimate behavioral change and selective retraining;
- unlabeled drift detection;
- security-domain drift adaptation;
- normality shift in zero-positive anomaly detection;
- drift-type-aware adaptation;
- CloudTrail anomaly detection and explanation;
- explanation-based intrusion-detection drift;
- general drift explanation;
- production attribution-drift monitoring;
- CloudTrail event semantics;
- a concept-drift survey.

The matrix records a verification URL and a limitation for each item. The draft's Pawlicki et al.
reference was intentionally not added because its complete bibliographic record was not verified.

## Test result

Command:

```text
python -m pytest tests -q
```

Result:

```text
......                                                                   [100%]
6 passed in 0.31s
```

## Research-positioning decision

The project will not claim that SHAP drift or explanation-based drift monitoring is itself new.
The study is positioned around CloudTrail-specific real-data analysis, controlled labelled
perturbations, and testing whether attribution drift improves selective adaptation decisions.

## Remaining literature work before submission

The matrix is a verified core matrix, not a final systematic review. Before journal submission,
it should be expanded through IEEE Xplore, ACM Digital Library, Scopus/Web of Science,
ScienceDirect, and Google Scholar using the search protocol in `docs/literature_review.md`.

