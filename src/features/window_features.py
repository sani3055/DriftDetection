"""Streaming month-level feature aggregation for the CloudTrail corpus."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Any

import pandas as pd

from src.data.temporal_protocol import normalize_month


DEFAULT_HIGH_RISK_EVENTS = frozenset({
    "AttachUserPolicy", "AttachRolePolicy", "PutUserPolicy", "PutRolePolicy",
    "CreateAccessKey", "DeleteTrail", "StopLogging", "UpdateTrail",
    "AssumeRole", "PutBucketPolicy", "PutBucketAcl",
})


def _entropy(counter: Counter[str]) -> float:
    total = sum(counter.values())
    if total == 0:
        return 0.0
    return -sum((count / total) * math.log2(count / total) for count in counter.values())


def _top_share(counter: Counter[str]) -> float:
    total = sum(counter.values())
    return (counter.most_common(1)[0][1] / total) if total else 0.0


def _clean(value: object) -> str:
    text = str(value).strip()
    return "Unknown" if text in {"", "nan", "None"} else text


def aggregate_cloudtrail_csv(
    path: str | Path,
    chunk_size: int = 100000,
    high_risk_events: Iterable[str] = DEFAULT_HIGH_RISK_EVENTS,
) -> tuple[pd.DataFrame, dict[str, dict[str, dict[str, int]]]]:
    """Aggregate scalar features and categorical distributions by month."""
    high_risk_events = frozenset(high_risk_events)
    required = [
        "eventTime", "eventName", "eventSource", "awsRegion", "userIdentitytype",
        "userIdentityaccountId", "userIdentityprincipalId", "errorCode",
    ]
    state: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "event_count": 0,
        "error_count": 0,
        "high_risk_count": 0,
        "eventName": Counter(),
        "eventSource": Counter(),
        "awsRegion": Counter(),
        "userIdentitytype": Counter(),
        "userIdentityaccountId": Counter(),
        "userIdentityprincipalId": Counter(),
        "errorCode": Counter(),
    })

    for chunk in pd.read_csv(path, usecols=required, chunksize=chunk_size, dtype=str):
        chunk = chunk.fillna("Unknown")
        for row in chunk.itertuples(index=False, name=None):
            event_time, event_name, event_source, region, identity_type, account, principal, error = row
            month = normalize_month(event_time)
            current = state[month]
            event_name = _clean(event_name)
            event_source = _clean(event_source)
            region = _clean(region)
            identity_type = _clean(identity_type)
            account = _clean(account)
            principal = _clean(principal)
            error = _clean(error)
            current["event_count"] += 1
            current["error_count"] += int(error not in {"NoError", "None", "Unknown"})
            current["high_risk_count"] += int(event_name in high_risk_events)
            for key, value in {
                "eventName": event_name,
                "eventSource": event_source,
                "awsRegion": region,
                "userIdentitytype": identity_type,
                "userIdentityaccountId": account,
                "userIdentityprincipalId": principal,
                "errorCode": error,
            }.items():
                current[key][value] += 1

    rows: list[dict[str, Any]] = []
    distributions: dict[str, dict[str, dict[str, int]]] = {}
    distribution_keys = [
        "eventName", "eventSource", "awsRegion", "userIdentitytype", "errorCode",
    ]
    for month in sorted(state):
        current = state[month]
        count = current["event_count"]
        rows.append({
            "window_id": month,
            "event_count": count,
            "error_rate": current["error_count"] / count,
            "high_risk_event_rate": current["high_risk_count"] / count,
            "unique_event_names": len(current["eventName"]),
            "unique_event_sources": len(current["eventSource"]),
            "unique_regions": len(current["awsRegion"]),
            "unique_identity_types": len(current["userIdentitytype"]),
            "unique_accounts": len(current["userIdentityaccountId"]),
            "unique_principals": len(current["userIdentityprincipalId"]),
            "event_name_entropy": _entropy(current["eventName"]),
            "event_source_entropy": _entropy(current["eventSource"]),
            "region_entropy": _entropy(current["awsRegion"]),
            "identity_type_entropy": _entropy(current["userIdentitytype"]),
            "error_code_entropy": _entropy(current["errorCode"]),
            "top_event_name_share": _top_share(current["eventName"]),
            "top_region_share": _top_share(current["awsRegion"]),
            "top_principal_share": _top_share(current["userIdentityprincipalId"]),
        })
        distributions[month] = {
            key: dict(current[key]) for key in distribution_keys
        }

    return pd.DataFrame(rows), distributions


def save_window_features(
    features: pd.DataFrame,
    distributions: dict[str, dict[str, dict[str, int]]],
    feature_path: str | Path,
    distribution_path: str | Path,
) -> None:
    """Persist deterministic feature and distribution artifacts."""
    feature_path = Path(feature_path)
    distribution_path = Path(distribution_path)
    feature_path.parent.mkdir(parents=True, exist_ok=True)
    distribution_path.parent.mkdir(parents=True, exist_ok=True)
    features.sort_values("window_id").to_csv(feature_path, index=False)
    distribution_path.write_text(json.dumps(distributions, indent=2, sort_keys=True) + "\n", encoding="utf-8")

