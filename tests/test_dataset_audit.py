from __future__ import annotations

import csv

from src.data.dataset_audit import audit_csv


def test_audit_reports_schema_counts_and_top_values(tmp_path) -> None:
    path = tmp_path / "sample.csv"
    rows = [
        ["2020-01", "RunInstances", "ec2.amazonaws.com", "us-east-1", "IAMUser", "None", "OK", "None"],
        ["2020-02", "ListBuckets", "s3.amazonaws.com", "us-east-1", "Root", "None", "AccessDenied", "AccessDenied"],
        ["2020-02", "ListBuckets", "s3.amazonaws.com", "us-west-2", "Root", "None", "AccessDenied", "AccessDenied"],
    ]
    header = [
        "eventTime",
        "eventName",
        "eventSource",
        "awsRegion",
        "userIdentitytype",
        "userIdentityaccountId",
        "userIdentityprincipalId",
        "errorCode",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)

    manifest = audit_csv(path, include_sha256=False)
    assert manifest["row_count"] == 3
    assert manifest["column_count"] == len(header)
    assert manifest["malformed_row_count"] == 0
    assert manifest["key_column_top_values"]["eventName"][0] == {
        "value": "ListBuckets",
        "count": 2,
    }
