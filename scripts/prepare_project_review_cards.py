"""Create source-linked reading cards, without making study-quality claims."""
import argparse
import html
import json
from pathlib import Path
import re

import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / '20106UG03/Review_Records'
OUT = RECORDS / 'Assessment_Cards'
OUT.mkdir(exist_ok=True)
METADATA = {r['doi']: r for r in json.loads((ROOT / 'review_2022_2026/search_v3/all_retrieved_candidates.json').read_text(encoding='utf-8'))}


def clean(s):
    s = html.unescape(s)
    s = re.sub(r'(\w)-\s*\n(\w)', r'\1\2', s)
    s = re.sub(r'\\documentclass.*?\\end\{document\}', ' [equation] ', s)
    return re.sub(r'\s+', ' ', s).strip()


def snippets(pages, pattern, cap=3, width=600):
    found = []
    for page, body in enumerate(pages, 1):
        for m in re.finditer(pattern, body, re.I):
            start = max(body.rfind('. ', 0, m.start()) + 2, m.start() - 160, 0)
            val = body[start:min(len(body), m.end()+width)]
            if len(val) < 100 or any(val[:100] in x['text'] for x in found):
                continue
            found.append({'pdf_page': page, 'text': val})
            break
        if len(found) >= cap:
            break
    return found


def original():
    queue = json.loads((RECORDS / 'fulltext_screening_queue.json').read_text(encoding='utf-8'))
    queue.append({'record_id': 'CORE05', 'doi': '10.1007/s10207-026-01299-x',
        'title': 'Detecting adversarial evasion in deep learning intrusion detection systems using explainable AI',
        'journal': 'International Journal of Information Security', 'publication_date': '2026-07-15',
        'path': 'review_2022_2026/submission_audit/Downloaded_Papers/CORE05_c104141fd5c3ba61e552.pdf',
        'source_type': 'journal-article', 'final_included': False})
    rows = []
    for q in queue:
        doi = q['doi']
        if not doi.startswith(('10.1007/', '10.1016/', '10.1038/', '10.1109/', '10.1186/', '10.32604/', '10.3389/', '10.3390/', '10.3934/', '10.7494/')):
            continue
        rid = q['record_id']
        cache = OUT / f'{rid}.json'
        if cache.exists():
            rows.append(json.loads(cache.read_text(encoding='utf-8')))
            continue
        reader = pdfium.PdfDocument(str(ROOT / q['path']))
        pages = [clean(p.get_textpage().get_text_range()) for p in reader]
        m = METADATA.get(doi, {})
        abstract = clean(m.get('abstract') or '')
        if not abstract:
            opening = ' '.join(pages[:2])
            match = re.search(r'\babstract\b[:\s]*(.*?)(?:\bkeywords\b|\bkey words\b|\b1\.? introduction\b)', opening, re.I)
            abstract = match.group(1) if match else ''
        row = dict(q)
        row.update(authors=m.get('authors', ''), abstract=abstract,
            method_evidence=snippets(pages, r'we propose|we present|our (?:method|model|framework)|proposed (?:method|model|framework)', 2, 600),
            data_evidence=snippets(pages, r'(?:data ?sets?|benchmark|train.{0,8}test|chronolog|temporal split)', 3, 500),
            limitations_evidence=snippets(pages, r'limitation|future (?:work|research)|data availability|code availability', 2, 550),
            conclusion_evidence=[{'pdf_page': len(pages)-j, 'text': body[-2200:]}
                                 for j, body in enumerate(reversed(pages[-5:]))
                                 if re.search(r'\bconclusion|\bconcluding', body, re.I)][:1],
            opening_evidence=[{'pdf_page': i+1, 'text': s[:1600]} for i,s in enumerate(pages[:2])],
            fulltext_cache=str((OUT/f'{rid}_pages.json').relative_to(ROOT)),
            source='Original OpenAlex bounded search or separately logged targeted discovery',
            pdf_path=q['path'])
        (OUT / f'{rid}_pages.json').write_text(json.dumps(pages, ensure_ascii=False), encoding='utf-8')
        cache.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
        rows.append(row)
        print(f'Extracted {rid}', flush=True)
    return rows


def supplementary():
    folder = RECORDS/'Supplementary_Search'
    register = folder/'retrieval_register.json'
    if not register.exists():
        register = folder/'retrieval_checkpoint.json'
    if not register.exists():
        return []
    rows = []
    for r in json.loads(register.read_text(encoding='utf-8')):
        if not r.get('fulltext_retrieved') or not r.get('pdf_retrieved') or r.get('is_retracted'):
            continue
        parsed = json.loads((ROOT/r['parsed_path']).read_text(encoding='utf-8'))
        r['abstract'] = clean(parsed['abstract'] or r.get('abstract', ''))
        r['xml_sections'] = [{'title': x['title'], 'text': clean(x['text'])}
                             for x in parsed['sections']]
        r['data_evidence'] = []
        r['limitations_evidence'] = []
        r['conclusion_evidence'] = []
        for sec in r['xml_sections']:
            if re.search('conclu', sec['title'], re.I):
                r['conclusion_evidence'].append({'section': sec['title'], 'text': sec['text'][:3000]})
            if re.search('method|data|experiment|evaluat', sec['title'], re.I):
                r['data_evidence'].append({'section': sec['title'], 'text': sec['text'][:1000]})
            if re.search('limitation|future', sec['title'], re.I):
                r['limitations_evidence'].append({'section': sec['title'], 'text': sec['text'][:1700]})
        (OUT / (r['record_id']+'.json')).write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding='utf-8')
        rows.append(r)
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--supplement-only', action='store_true')
    args = p.parse_args()
    old = [] if args.supplement_only else original()
    new = supplementary()
    by_doi = {r['doi']: r for r in old}
    for r in new:
        # Prefer structured article XML for repeated DOI records.
        by_doi[r['doi']] = r
    if args.supplement_only:
        for path in OUT.glob('S*.json'):
            if path.name.endswith('_pages.json'):
                continue
            r = json.loads(path.read_text(encoding='utf-8'))
            by_doi.setdefault(r['doi'], r)
        for path in OUT.glob('CORE*.json'):
            r = json.loads(path.read_text(encoding='utf-8')); by_doi.setdefault(r['doi'],r)
    all_rows = list(by_doi.values())
    (RECORDS/'available_evidence_cards.json').write_text(json.dumps(all_rows, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'distinct_doi_cards': len(all_rows), 'supplementary_pdf_cards': len(new)}, indent=2))


if __name__ == '__main__':
    main()
