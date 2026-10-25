"""Collect a reproducible 2022–2026 journal-paper evidence set from OpenAlex.

This script performs metadata discovery and an automated initial screen. It does not claim that
automated screening replaces independent human screening. Open-access PDFs are downloaded only
when an explicit OA PDF URL is provided by the scholarly metadata record.
"""

from __future__ import annotations

import csv
import html
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

import yaml


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "review_2022_2026"

EXCLUDED_DOMAIN_TERMS = (
    "groundwater", "water quality", "road anomaly", "automotive quality", "eco-driving",
    "mining truck", "nuclear power", "drug delivery", "aviation", "agriculture",
    "salary advance", "medical imaging", "healthcare diagnosis", "quality assurance",
)


def fetch_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "DriftDetectionReview/1.0 (mailto:research-review@example.org)"})
    with urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_crossref(query: str, year_from: int, year_to: int) -> dict:
    url = (
        "https://api.crossref.org/works?query.bibliographic=" + quote_plus(query)
        + f"&filter=from-pub-date:{year_from}-01-01,until-pub-date:{year_to}-12-31,type:journal-article"
        + "&rows=200"
    )
    return fetch_json(url)


def reconstruct_abstract(inverted_index: dict | None) -> str:
    if not inverted_index:
        return ""
    words = []
    for word, positions in inverted_index.items():
        for position in positions:
            words.append((position, word))
    return " ".join(word for _, word in sorted(words))


def normalize_doi(value: str | None) -> str:
    return re.sub(r"^https?://doi.org/", "", (value or "").strip(), flags=re.I).lower()


def topic_score(text: str) -> tuple[int, list[str]]:
    groups = {
        "cloud_audit": ["cloudtrail", "cloud audit", "audit log", "cloud log", "aws"],
        "security_detection": ["anomaly detection", "intrusion detection", "threat detection", "cybersecurity", "cyber security", "security analytics"],
        "drift_adaptation": ["concept drift", "data drift", "distribution drift", "adaptive", "retraining", "normality shift"],
        "explainability": ["shap", "explainable", "explanation", "feature attribution", "interpretable"],
        "machine_learning": ["machine learning", "deep learning", "unsupervised", "isolation forest", "outlier"],
    }
    matched = [name for name, words in groups.items() if any(word in text for word in words)]
    return len(matched), matched


def record_from_work(work: dict, query: str) -> dict:
    primary = work.get("primary_location") or {}
    source = primary.get("source") or {}
    oa = work.get("open_access") or {}
    best_oa = work.get("best_oa_location") or {}
    authors = []
    for author in work.get("authorships") or []:
        author_name = (author.get("author") or {}).get("display_name")
        if author_name:
            authors.append(author_name)
    abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
    title = (work.get("title") or "").strip()
    searchable = f"{title} {abstract}".lower()
    score, matched = topic_score(searchable)
    return {
        "openalex_id": work.get("id", ""),
        "doi": normalize_doi(work.get("doi")),
        "title": title,
        "authors": "; ".join(authors),
        "publication_year": work.get("publication_year"),
        "type": work.get("type"),
        "journal": source.get("display_name", ""),
        "issn": "; ".join(source.get("issn_l") or [] if isinstance(source.get("issn_l"), list) else ([source.get("issn_l")] if source.get("issn_l") else [])),
        "cited_by_count": work.get("cited_by_count", 0),
        "abstract": abstract,
        "query_source": query,
        "topic_score": score,
        "matched_topic_groups": "; ".join(matched),
        "is_open_access": bool(oa.get("is_oa", False)),
        "oa_license": oa.get("oa_status", ""),
        "oa_pdf_url": best_oa.get("pdf_url", "") or "",
        "oa_landing_url": best_oa.get("landing_page_url", "") or work.get("doi", "") or "",
        "is_retracted": bool(work.get("is_retracted", False)),
    }


def record_from_crossref(work: dict, query: str) -> dict:
    title = " ".join(work.get("title") or []).strip()
    abstract = re.sub(r"<[^>]+>", " ", html.unescape(work.get("abstract", ""))).strip()
    searchable = f"{title} {abstract}".lower()
    score, matched = topic_score(searchable)
    authors = []
    for author in work.get("author") or []:
        name = " ".join(part for part in [author.get("given", ""), author.get("family", "")] if part).strip()
        if name:
            authors.append(name)
    year_parts = ((work.get("published") or {}).get("date-parts") or [[None]])[0]
    year = year_parts[0]
    licenses = work.get("license") or []
    pdf_links = [link.get("URL", "") for link in work.get("link") or [] if "pdf" in (link.get("content-type", "") or "").lower()]
    oa_pdf = pdf_links[0] if licenses and pdf_links else ""
    return {
        "openalex_id": "",
        "doi": normalize_doi(work.get("DOI")),
        "title": title,
        "authors": "; ".join(authors),
        "publication_year": year,
        "type": work.get("type"),
        "journal": " ".join(work.get("container-title") or []),
        "issn": "; ".join(work.get("ISSN") or []),
        "cited_by_count": work.get("is-referenced-by-count", 0),
        "abstract": abstract,
        "query_source": query,
        "topic_score": score,
        "matched_topic_groups": "; ".join(matched),
        "is_open_access": bool(licenses),
        "oa_license": licenses[0].get("URL", "") if licenses else "",
        "oa_pdf_url": oa_pdf,
        "oa_landing_url": work.get("URL", ""),
        "is_retracted": False,
    }


def download_open_access(record: dict, directory: Path) -> str:
    url = record.get("oa_pdf_url", "")
    if not url:
        return "not_available"
    safe = re.sub(r"[^A-Za-z0-9]+", "_", record["title"][:100]).strip("_")
    path = directory / f"{record['publication_year']}_{safe}_{hashlib.sha1(record['doi'].encode()).hexdigest()[:8]}.pdf"
    try:
        request = Request(url, headers={"User-Agent": "DriftDetectionReview/1.0"})
        with urlopen(request, timeout=60) as response:
            payload = response.read()
        if not payload.startswith(b"%PDF"):
            return "oa_link_not_pdf"
        path.write_bytes(payload)
        record["download_path"] = str(path.relative_to(ROOT))
        return "downloaded_open_access"
    except Exception as exc:  # noqa: BLE001
        record["download_error"] = str(exc)[:200]
        return "download_failed"


def main() -> None:
    config = yaml.safe_load((ROOT / "configs" / "review.yaml").read_text(encoding="utf-8"))["review"]
    OUT.mkdir(parents=True, exist_ok=True)
    pdf_dir = OUT / config["project_folder"] / "Downloaded_Papers"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    query_log = []
    candidates: dict[str, dict] = {}
    seen_dois: set[str] = set()
    raw_records = 0
    eligible_records = 0
    for query in config["queries"]:
        url = (
            "https://api.openalex.org/works?search=" + quote_plus(query)
            + f"&filter=from_publication_date:{config['year_from']}-01-01,to_publication_date:{config['year_to']}-12-31,type:article,has_doi:true"
            + "&per-page=200&mailto=" + quote_plus(config["openalex_mailto"])
        )
        try:
            payload = fetch_json(url)
            raw_results = payload.get("results", [])
            source_api = "OpenAlex"
            normalized = [record_from_work(work, query) for work in raw_results]
        except HTTPError as exc:
            if exc.code != 429:
                raise
            payload = fetch_crossref(query, int(config["year_from"]), int(config["year_to"]))
            raw_results = payload.get("message", {}).get("items", [])
            source_api = "Crossref"
            normalized = [record_from_crossref(work, query) for work in raw_results]
        raw_records += len(normalized)
        query_log.append({"query": query, "api": source_api, "returned": len(raw_results), "meta": payload.get("meta", payload.get("message", {}).get("total-results", {}))})
        for record in normalized:
            doi = record["doi"]
            if doi:
                seen_dois.add(doi)
            if not doi or record["is_retracted"] or record["type"] != "article":
                if source_api == "Crossref" and record["type"] != "journal-article":
                    continue
                if not doi or record["is_retracted"]:
                    continue
            if record["topic_score"] < 2:
                continue
            searchable_record = f"{record['title']} {record['abstract']} {record['journal']}".lower()
            if "security_detection" not in record["matched_topic_groups"] or any(term in searchable_record for term in EXCLUDED_DOMAIN_TERMS):
                continue
            eligible_records += 1
            prior = candidates.get(doi)
            if prior is None or (record["topic_score"], record["cited_by_count"]) > (prior["topic_score"], prior["cited_by_count"]):
                candidates[doi] = record
        time.sleep(0.2)
    records = sorted(candidates.values(), key=lambda row: (-row["topic_score"], -row["cited_by_count"], row["title"]))
    records = records[: int(config["target_records"])]
    if len(records) < int(config["target_records"]):
        raise RuntimeError(f"Only {len(records)} eligible records found; target is {config['target_records']}")
    for index, record in enumerate(records, start=1):
        record["paper_id"] = f"P{index:03d}"
        record["screening_decision"] = "automated_include_pending_human_confirmation"
        record["full_text_status"] = download_open_access(record, pdf_dir)
        time.sleep(0.05)
    fields = sorted({key for record in records for key in record.keys()})
    with (OUT / "evidence_matrix_100.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    screening_rows = []
    for record in records:
        screening_rows.append({
            "record_id": record["paper_id"],
            "doi": record["doi"],
            "title": record["title"],
            "year": record["publication_year"],
            "source": record["query_source"],
            "automated_decision": record["screening_decision"],
            "reason": "journal article, DOI present, 2022–2026, topic score >= 2, not retracted",
            "manual_screening_required": "yes",
        })
    with (OUT / "screening_log_100.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(screening_rows[0].keys()))
        writer.writeheader()
        writer.writerows(screening_rows)
    sources = sorted({entry["api"] for entry in query_log})
    (OUT / "search_log.json").write_text(json.dumps({"queries": query_log, "retrieval_source": sources, "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, indent=2) + "\n", encoding="utf-8")
    (OUT / "collection_manifest.json").write_text(json.dumps({
        "target_records": config["target_records"],
        "records_retrieved": raw_records,
        "unique_dois_seen": len(seen_dois),
        "eligible_after_automated_screen": eligible_records,
        "collected_records": len(records),
        "year_range": [config["year_from"], config["year_to"]],
        "open_access_downloads": sum(row["full_text_status"] == "downloaded_open_access" for row in records),
        "manual_screening_required": len(records),
        "caveat": "This is an automated initial screen; two-reviewer title/abstract and full-text screening is still required for a publishable PRISMA review.",
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"collected": len(records), "open_access_downloads": sum(row["full_text_status"] == "downloaded_open_access" for row in records)}, indent=2))


if __name__ == "__main__":
    main()
