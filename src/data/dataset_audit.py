"""Read-only audit of the external CloudTrail CSV corpus."""

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from pathlib import Path
from typing import Iterable, Any


DEFAULT_KEY_COLUMNS = (
    "eventTime",
    "eventName",
    "eventSource",
    "awsRegion",
    "userIdentitytype",
    "userIdentityaccountId",
    "userIdentityprincipalId",
    "errorCode",
)


def _sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _top_values(counter: Counter[str], limit: int = 10) -> list[dict[str, Any]]:
    return [{"value": value, "count": count} for value, count in counter.most_common(limit)]


def audit_csv(
    path: str | Path,
    key_columns: Iterable[str] = DEFAULT_KEY_COLUMNS,
    encoding: str = "utf-8-sig",
    include_sha256: bool = True,
) -> dict[str, Any]:
    """Audit schema, row widths, missingness, and key-column distributions."""
    csv_path = Path(path)
    if not csv_path.is_file():
        raise FileNotFoundError(csv_path)

    key_columns = tuple(key_columns)
    counters = {column: Counter() for column in key_columns}
    missing = Counter()
    malformed_rows = 0
    row_count = 0

    with csv_path.open("r", encoding=encoding, newline="", errors="replace") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError(f"CSV is empty: {csv_path}") from exc

        header = [column.strip() for column in header]
        header_set = set(header)
        absent_key_columns = [column for column in key_columns if column not in header_set]
        if absent_key_columns:
            raise ValueError(f"Missing audit columns: {absent_key_columns}")

        positions = {column: header.index(column) for column in key_columns}
        for row in reader:
            row_count += 1
            if len(row) != len(header):
                malformed_rows += 1
            for column, position in positions.items():
                value = row[position].strip() if position < len(row) else ""
                if value == "":
                    missing[column] += 1
                counters[column][value] += 1

    manifest: dict[str, Any] = {
        "path": str(csv_path.resolve()),
        "file_size_bytes": csv_path.stat().st_size,
        "sha256": _sha256(csv_path) if include_sha256 else None,
        "row_count": row_count,
        "column_count": len(header),
        "columns": header,
        "malformed_row_count": malformed_rows,
        "missing_counts": dict(missing),
        "key_column_top_values": {
            column: _top_values(counter) for column, counter in counters.items()
        },
    }
    return manifest

