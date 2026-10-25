from __future__ import annotations

import csv
from pathlib import Path


def test_literature_matrix_has_verified_core_records() -> None:
    path = Path("docs/literature_matrix.csv")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) >= 10
    assert {row["status"] for row in rows} >= {"verified core", "verified operational source"}
    assert all(row["title"] and row["verification_url"] for row in rows)
    assert len({row["id"] for row in rows}) == len(rows)


def test_literature_review_and_gap_exist() -> None:
    assert Path("docs/literature_review.md").is_file()
    assert Path("docs/research_gap.md").is_file()

