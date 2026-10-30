"""Audit retrieved PDF identity without implying study inclusion or appraisal."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'review_2022_2026/search_v3'


def normal(text):
    text = unicodedata.normalize('NFKD', text.lower())
    return re.sub(r'[^a-z0-9]', '', text)


def identity(title, doi, first):
    target, found = normal(title), normal(first)
    exact = target in found
    tokens = {normal(word) for word in title.split() if len(normal(word)) > 3}
    coverage = sum(token in found for token in tokens) / len(tokens) if tokens else 0
    doi_present = normal(doi) in found
    # Automated evidence only; ambiguous versions require manual source checking.
    passed = exact or (coverage >= .85 and doi_present)
    return {'title_normalised_match': exact, 'title_token_coverage': coverage,
            'opening_doi_normalised_match': doi_present,
            'automated_identity': 'supported' if passed else 'needs_source_check'}


def main():
    register = json.loads((OUT / 'retrieval/register.json').read_text(encoding='utf-8'))
    records = []
    for record in register:
        if not record.get('path'):
            continue
        path = ROOT / record['path']
        reader = PdfReader(path)
        first = '\n'.join(page.extract_text() or '' for page in reader.pages[:2])
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        records.append({'paper_id': record['paper_id'], 'doi': record['doi'], 'title': record['title'],
                        'path': record['path'], 'sha256': digest, 'pages': len(reader.pages),
                        **identity(record['title'], record['doi'], first),
                        'fulltext_eligibility_assessed': False, 'critical_appraisal_completed': False,
                        'final_included': False, 'reviewer': 'automated identity check only'})
    (OUT / 'pdf_identity_audit.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    counts = Counter(row['automated_identity'] for row in records)
    hashes = Counter(row['sha256'] for row in records)
    report = {'retrieved_pdf_records': len(records), 'unique_pdf_hashes': len(hashes),
              'supported_automated_identity': counts['supported'],
              'requires_source_check': counts['needs_source_check'],
              'repeated_file_hashes': [h for h, count in hashes.items() if count > 1],
              'final_study_inclusions_created': 0,
              'caveat': 'PDF identity is not full-text eligibility, critical appraisal, or independent human review.'}
    (OUT / 'pdf_identity_summary.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
