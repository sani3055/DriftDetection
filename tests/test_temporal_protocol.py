from __future__ import annotations

import csv

from src.data.temporal_protocol import chronological_split, normalize_month, ordered_months
from src.features.window_features import aggregate_cloudtrail_csv


def test_month_normalization_and_ordering() -> None:
    assert normalize_month("2020-2") == "2020-02"
    assert ordered_months(["2020-02", "2019-12", "2020-01"]) == (
        "2019-12", "2020-01", "2020-02"
    )


def test_chronological_split_has_no_overlap() -> None:
    split = chronological_split([f"2020-{month:02d}" for month in range(1, 13)])
    assert set(split.train).isdisjoint(split.validation)
    assert set(split.validation).isdisjoint(split.test)
    assert split.train < split.validation < split.test


def test_window_features_are_aggregated_by_month(tmp_path) -> None:
    path = tmp_path / "events.csv"
    header = [
        "eventTime", "eventName", "eventSource", "awsRegion", "userIdentitytype",
        "userIdentityaccountId", "userIdentityprincipalId", "errorCode",
    ]
    rows = [
        ["2020-01", "ListBuckets", "s3.amazonaws.com", "us-east-1", "IAMUser", "a", "p1", "None"],
        ["2020-01", "DeleteTrail", "cloudtrail.amazonaws.com", "us-east-1", "Root", "a", "p2", "AccessDenied"],
        ["2020-02", "RunInstances", "ec2.amazonaws.com", "us-west-2", "IAMUser", "b", "p3", "NoError"],
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)

    features, distributions = aggregate_cloudtrail_csv(path, chunk_size=2)
    january = features.loc[features["window_id"] == "2020-01"].iloc[0]
    assert january["event_count"] == 2
    assert january["high_risk_event_rate"] == 0.5
    assert distributions["2020-01"]["eventName"]["DeleteTrail"] == 1

