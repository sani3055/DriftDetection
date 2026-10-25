"""Audit the richer raw export without modifying or copying it."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.utils.config import load_yaml  # noqa: E402


def main() -> None:
    config = load_yaml(ROOT / "configs" / "base.yaml")["dataset"]
    source = Path(config["rich_timestamp_source_path"])
    if not source.is_file():
        raise FileNotFoundError(source)
    rows = 0
    parse_failures = 0
    month_values: set[str] = set()
    day_values: set[str] = set()
    hour_values: set[int] = set()
    for chunk in pd.read_csv(source, usecols=["eventTime"], chunksize=int(config["chunk_size"]), encoding=config["encoding"]):
        rows += len(chunk)
        parsed = pd.to_datetime(chunk["eventTime"], errors="coerce", utc=True)
        parse_failures += int(parsed.isna().sum())
        valid = parsed.dropna()
        month_values.update(valid.dt.strftime("%Y-%m").unique().tolist())
        day_values.update(valid.dt.strftime("%Y-%m-%d").unique().tolist())
        hour_values.update(valid.dt.hour.astype(int).unique().tolist())
    manifest = {
        "source_path": str(source),
        "file_size_bytes": source.stat().st_size,
        "rows": rows,
        "timestamp_parse_failures": parse_failures,
        "unique_months": len(month_values),
        "unique_days": len(day_values),
        "observed_hours": sorted(hour_values),
        "supports_submonthly_resolution": bool(len(day_values) > len(month_values)),
        "independence": "same underlying CloudTrail corpus as the month-level study; not external validation",
    }
    output = ROOT / "data_manifest" / "rich_timestamp_manifest.json"
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
