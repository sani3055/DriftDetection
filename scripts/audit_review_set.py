"""Audit the automated 100-record evidence set without making final inclusion decisions.

The output is a transparent triage aid for the required human screening. It deliberately does
not call a paper included or excluded: relevance, full-text eligibility, journal status, and
risk of bias still require reviewer judgment.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "review_2022_2026" / "evidence_matrix_100.csv"
OUTPUT = ROOT / "review_2022_2026" / "automated_quality_audit_100.csv"


def contains(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.casefold()
    return any(term.casefold() in lowered for term in terms)


def classify(row: dict[str, str]) -> dict[str, str]:
    text = " ".join(
        [
            row.get("title", ""),
            row.get("abstract", ""),
            row.get("journal", ""),
        ]
    )
    direct_cloud = contains(
        text,
        (
            "cloudtrail",
            "aws",
            "cloud audit",
            "audit log",
            "cloud log",
            "cloud api",
            "cloud platform",
            "cloud security",
            "cloud computing",
        ),
    )
    security = contains(
        text,
        (
            "cybersecurity",
            "cyber security",
            "intrusion",
            "malware",
            "ransomware",
            "threat detection",
            "security",
            "adversarial",
        ),
    )
    drift = contains(
        text,
        (
            "concept drift",
            "data drift",
            "distribution shift",
            "drift-aware",
            "adaptive",
            "adaptation",
            "evolving",
            "online learning",
        ),
    )
    explainability = contains(
        text,
        (
            "shap",
            "shapley",
            "explainable",
            "explainability",
            "interpret",
            "feature attribution",
        ),
    )
    review = contains(text, ("survey", "systematic review", "research agenda", "review"))
    no_abstract = not row.get("abstract", "").strip()
    journal_risk = contains(
        row.get("journal", ""),
        (
            "international journal",
            "multidisciplinary",
            "world journal",
            "towards excellence",
            "transactions on sustainable",
            "science and technology",
        ),
    )

    if direct_cloud and security and (drift or explainability):
        relevance_band = "direct_cloud_security_method"
    elif security and (drift or explainability):
        relevance_band = "strong_adjacent_security_method"
    elif direct_cloud or (security and review):
        relevance_band = "context_or_background"
    else:
        relevance_band = "weak_or_unclear_from_metadata"

    flags: list[str] = []
    if no_abstract:
        flags.append("abstract_missing")
    if journal_risk:
        flags.append("journal_status_verify")
    if review:
        flags.append("review_or_survey_verify_primary_study_role")
    if not direct_cloud:
        flags.append("not_direct_cloudtrail_or_cloud_audit")
    if not security:
        flags.append("security_connection_unclear")
    if not (drift or explainability):
        flags.append("drift_or_explainability_connection_unclear")
    if row.get("full_text_status") != "downloaded_open_access":
        flags.append("full_text_manual_retrieval_needed")

    return {
        "paper_id": row.get("paper_id", ""),
        "doi": row.get("doi", ""),
        "title": row.get("title", ""),
        "publication_year": row.get("publication_year", ""),
        "journal": row.get("journal", ""),
        "relevance_band": relevance_band,
        "direct_cloud_or_audit_signal": "yes" if direct_cloud else "no",
        "security_detection_signal": "yes" if security else "no",
        "drift_adaptation_signal": "yes" if drift else "no",
        "explainability_signal": "yes" if explainability else "no",
        "review_or_survey_signal": "yes" if review else "no",
        "full_text_status": row.get("full_text_status", ""),
        "automated_flags": ";".join(flags),
        "human_action": "Verify title/abstract, obtain full text, extract methods, then decide include/exclude",
    }


def main() -> None:
    with INPUT.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    audited = [classify(row) for row in rows]
    fields = list(audited[0])
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(audited)
    print(f"Wrote {len(audited)} non-decisive screening audits to {OUTPUT}")


if __name__ == "__main__":
    main()
