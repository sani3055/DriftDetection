# Phase 0 Validation

Status: **Complete; waiting for approval before Phase 1**

## Files created

- `IMPLEMENTATION_PLAN.md`
- `configs/base.yaml`
- `requirements.in`
- `src/utils/config.py`
- `src/utils/seed.py`
- `src/utils/logging.py`
- `src/data/dataset_audit.py`
- `scripts/audit_dataset.py`
- `tests/test_scaffolding.py`
- `tests/test_dataset_audit.py`
- `data_manifest/real_cloudtrail_manifest.json`

## Test result

Command:

```text
python -m pytest tests -q
```

Result:

```text
....                                                                     [100%]
4 passed in 0.64s
```

The validation used the installed Python 3.13 interpreter because Python 3.11 is not currently
available on this machine. The project target remains Python 3.11 and must be revalidated in a
Python 3.11 environment before final packaging.

## Dataset audit result

Source:

```text
D:\Projects\CloudGuard\data\dec12_18features.csv
```

Recorded in `data_manifest/real_cloudtrail_manifest.json`:

- file size: 830,904,812 bytes;
- SHA-256: `b3aa4fcf28747f4f84457d2d3b76f4c27901bd2e6289bf6d6288cb9587d20589`;
- row count: 1,939,207;
- column count: 18;
- malformed rows: 0;
- blank values in audited key columns: 0.

The CSV row count differs from the earlier report's stated 1,939,214 rows. The manifest value is
the value obtained by reading the current file and must be used in future reports unless the source
file changes.

## Observed limitations

- `eventTime` is month-level in this file, so event-level session order and hour-based features
  cannot yet be claimed.
- The corpus has no attack labels.
- The source file is external to this repository; provenance and redistribution permissions still
  need to be documented in Phase 1.
- Phase 1 must determine whether the dataset represents one account, multiple accounts, or a
  merged corpus before identity-based aggregation is finalized.

