"""Chronological protocol for the month-level CloudTrail corpus."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


MONTH_PATTERN = re.compile(r"^(\d{4})-(\d{1,2})$")


@dataclass(frozen=True)
class TemporalSplit:
    train: tuple[str, ...]
    validation: tuple[str, ...]
    test: tuple[str, ...]


def normalize_month(value: object) -> str:
    """Return a validated YYYY-MM key."""
    text = str(value).strip()
    match = MONTH_PATTERN.fullmatch(text)
    if not match:
        raise ValueError(f"Expected month-level YYYY-MM value, got {value!r}")
    year, month = int(match.group(1)), int(match.group(2))
    if not 1 <= month <= 12:
        raise ValueError(f"Invalid month value: {value!r}")
    return f"{year:04d}-{month:02d}"


def ordered_months(values: Iterable[object]) -> tuple[str, ...]:
    """Normalize, deduplicate, and chronologically sort month keys."""
    return tuple(sorted({normalize_month(value) for value in values}))


def chronological_split(
    months: Iterable[object],
    train_fraction: float = 0.60,
    validation_fraction: float = 0.20,
    minimum_months_per_split: int = 1,
) -> TemporalSplit:
    """Create contiguous train/validation/test month partitions."""
    if not 0 < train_fraction < 1 or not 0 < validation_fraction < 1:
        raise ValueError("Split fractions must be between zero and one")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("Train and validation fractions must leave a test split")
    if minimum_months_per_split < 1:
        raise ValueError("Each split must contain at least one month")

    ordered = ordered_months(months)
    n_months = len(ordered)
    required = 3 * minimum_months_per_split
    if n_months < required:
        raise ValueError(f"Need at least {required} months, received {n_months}")

    train_end = max(minimum_months_per_split, int(n_months * train_fraction))
    validation_size = max(minimum_months_per_split, int(n_months * validation_fraction))
    if train_end + validation_size > n_months - minimum_months_per_split:
        validation_size = n_months - train_end - minimum_months_per_split
    if validation_size < minimum_months_per_split:
        train_end = n_months - validation_size - minimum_months_per_split

    validation_end = train_end + validation_size
    return TemporalSplit(
        train=ordered[:train_end],
        validation=ordered[train_end:validation_end],
        test=ordered[validation_end:],
    )
