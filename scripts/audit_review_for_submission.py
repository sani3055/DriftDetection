"""Verify candidate metadata/PDF availability without claiming final inclusion.

Network mode requests public DOI metadata from Crossref and downloads only links
associated with an explicit Creative Commons licence. Never bypass access controls.
Old artifacts are read-only; all new evidence is written under submission_audit.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import calendar
from datetime import date, datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "review_2022_2026/submission_audit"
TODAY = date(2026, 10, 29)
HEADERS = {"User-Agent": "DriftDetection-ResearchAudit/2.0 (https://github.com/sani3055/DriftDetection)"}


def clean_abstract(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(text or ""))).strip()


def verified_metadata(row: dict, resolve: bool, download: bool) -> dict:
    record = dict(row)
    doi = row["doi"].lower().removeprefix("https://doi.org/")
    key = hashlib.sha256(doi.encode()).hexdigest()[:20]
    cache = OUT / "crossref_cache" / f"{key}.json"
    existing_pdf = OUT / "Downloaded_Papers" / f"{row['paper_id']}_{key}.pdf"
    if existing_pdf.is_file():
        record['new_download_path'] = str(existing_pdf.relative_to(ROOT))
    record.update({"metadata_verified": False, "journal_type_verified": False,
                   "publication_date_verified": False, "pdf_parse_verified": False,
                   "full_text_reviewed": False, "final_inclusion": "pending"})
    if cache.exists() or resolve:
        try:
            if cache.exists():
                work = json.loads(cache.read_text(encoding="utf-8"))
            else:
                request = Request("https://api.crossref.org/works/" + quote(doi, safe=""), headers=HEADERS)
                with urlopen(request, timeout=25) as response:
                    work = json.load(response)["message"]
                cache.write_text(json.dumps(work, ensure_ascii=False, indent=2), encoding="utf-8")
            if str(work.get("DOI", "")).lower() != doi:
                raise ValueError("Crossref DOI mismatch")
            record["metadata_verified"] = True
            record["verified_type"] = work.get("type", "")
            record["journal_type_verified"] = work.get("type") == "journal-article"
            record["verified_title"] = " ".join(work.get("title", []))
            record["verified_journal"] = " ".join(work.get("container-title", []))
            record["verified_authors"] = "; ".join(" ".join([a.get("given", ""), a.get("family", "")]).strip()
                                                          for a in work.get("author", []))
            dates = []
            for field in ("published-online", "published-print", "published"):
                parts = work.get(field, {}).get("date-parts", [[]])[0]
                if parts:
                    year=parts[0]
                    month=parts[1] if len(parts)>1 else 1
                    low=date(year,month,parts[2] if len(parts)>2 else 1)
                    high=(low if len(parts)>2 else date(year,month,calendar.monthrange(year,month)[1])
                          if len(parts)>1 else date(year,12,31))
                    dates.append((low,high,parts,field))
            if dates:
                earliest_low=min(item[0] for item in dates)
                earliest_high=min(item[1] for item in dates)
                chosen=min(dates,key=lambda item:(item[0],-len(item[2])))
                record["verified_first_publication_date"]='-'.join(str(value).zfill(2) for value in chosen[2])
                record["publication_date_precision"]={1:'year',2:'month',3:'day'}[len(chosen[2])]
                record["publication_date_lower_bound"]=str(earliest_low)
                record["publication_date_upper_bound"]=str(earliest_high)
                record["publication_date_source"]=chosen[3]
                record["publication_date_verified"]=date(2022,1,1)<=earliest_low and earliest_high<=TODAY
            else:
                record["verified_first_publication_date"]=''
            record["verified_abstract"] = clean_abstract(work.get("abstract", ""))
            # A publisher licence URL is not evidence of OA unless it grants an explicit CC licence.
            cc = [item.get("URL", "") for item in work.get("license", [])
                  if "creativecommons.org/" in item.get("URL", "").lower()]
            record["verified_cc_licenses"] = "; ".join(sorted(set(cc)))
            record["crossref_update_notice"] = json.dumps(work.get("update-to", []))
            pdf_links = [link.get("URL", "") for link in work.get("link", [])
                         if "pdf" in link.get("content-type", "").lower()]
            if download and cc:
                for url in pdf_links[:2]:
                    target = OUT / "Downloaded_Papers" / f"{row['paper_id']}_{key}.pdf"
                    if target.exists():
                        record["new_download_path"] = str(target.relative_to(ROOT))
                        break
                    try:
                        with urlopen(Request(url, headers=HEADERS), timeout=20) as response:
                            payload = response.read(20_000_001)
                            landed = response.geturl()
                        if len(payload) > 20_000_000 or not payload.startswith(b"%PDF"):
                            raise ValueError("Response is not a PDF or exceeds 20 MB")
                        target.write_bytes(payload)
                        record["new_download_path"] = str(target.relative_to(ROOT))
                        record["new_download_source"] = landed
                        break
                    except Exception as exc:
                        record["new_download_error"] = str(exc)[:200]
        except Exception as exc:
            record["metadata_error"] = str(exc)[:240]
    paths = [record.get("new_download_path", ""), record.get("download_path", "")]
    for relative in paths:
        if not relative:
            continue
        path = ROOT / relative
        if not path.is_file():
            continue
        try:
            from pypdf import PdfReader
            reader = PdfReader(path)
            pages = len(reader.pages)
            first_text = "\n".join((page.extract_text() or "") for page in reader.pages[:2])
            if pages == 0 or len(first_text.strip()) < 40:
                raise ValueError("No extractable article text on first two pages")
            record["pdf_parse_verified"] = True
            record["verified_pdf_path"] = str(path.relative_to(ROOT))
            record["pdf_pages"] = pages
            record["pdf_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            record["doi_found_on_first_two_pages"] = doi in first_text.lower()
            excerpt = OUT / "extracted_text" / f"{row['paper_id']}.txt"
            # Extraction is an access aid, not a claim of reading or critical appraisal.
            excerpt.write_text("\n\n".join(page.extract_text() or "" for page in reader.pages), encoding="utf-8")
            record["extracted_text_path"] = str(excerpt.relative_to(ROOT))
            break
        except Exception as exc:
            record["pdf_verification_error"] = str(exc)[:240]
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resolve", action="store_true")
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--include-core", action="store_true")
    args = parser.parse_args()
    for folder in (OUT, OUT / "crossref_cache", OUT / "Downloaded_Papers", OUT / "extracted_text"):
        folder.mkdir(parents=True, exist_ok=True)
    source = ROOT / "review_2022_2026/evidence_matrix_100.csv"
    with source.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if args.include_core:
        references = json.loads((ROOT / 'docs/journal_references.json').read_text(encoding='utf-8'))
        additions = [references[key] for key in ['arora', 'kuppa', 'lee', 'li', 'maseno']]
        additions.append({'title':'A Framework for Drift Detection and Adaptation in AI-driven Anomaly and Threat Detection Systems',
                          'url':'https://doi.org/10.1007/s10207-025-01118-9', 'year':'2025'})
        existing = {row['doi'].lower() for row in rows}
        for i, item in enumerate(additions, 1):
            doi = item['url'].removeprefix('https://doi.org/').lower()
            if doi not in existing:
                rows.append({'paper_id':f'CORE{i:02d}', 'doi':doi, 'title':item['title'],
                             'publication_year':item['year'], 'download_path':'',
                             'query_source':'directed citation/primary-source follow-up, 29 October 2026'})
                existing.add(doi)
    completed = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        tasks = [executor.submit(verified_metadata, row, args.resolve, args.download) for row in rows]
        for task in as_completed(tasks):
            completed.append(task.result())
            if len(completed) % 10 == 0:
                print(f"Audited {len(completed)}/{len(rows)}", flush=True)
    completed.sort(key=lambda row: row["paper_id"])
    (OUT / "verified_candidates.json").write_text(json.dumps(completed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {"candidate_records": len(rows),
        "unique_dois": len({row["doi"].lower() for row in rows}),
        "crossref_metadata_verified": sum(row["metadata_verified"] for row in completed),
        "journal_article_type_verified": sum(row["journal_type_verified"] for row in completed),
        "publication_date_within_2022_to_cutoff_verified": sum(row["publication_date_verified"] for row in completed),
        "readable_pdf_files_verified": sum(row["pdf_parse_verified"] for row in completed),
        "pdf_with_doi_on_first_two_pages": sum(row.get("doi_found_on_first_two_pages", False) for row in completed),
        "new_pdf_downloads": sum(bool(row.get("new_download_path")) for row in completed),
        "full_text_reviews_completed_by_this_script": 0, "final_included_studies": 0}
    (OUT / "audit_manifest.json").write_text(json.dumps({"cutoff": str(TODAY),
        "created_utc": datetime.now(timezone.utc).isoformat(), "counts": counts,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "caveats": ["Metadata/PDF parsing is not critical appraisal or final inclusion",
                    "An accessible PDF is not proof of journal quality or permission to redistribute",
                    "No NotebookLM or SciSpace usage is claimed", "100 is a candidate target, not a PRISMA minimum"]}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(counts, indent=2), flush=True)


if __name__ == "__main__":
    main()
