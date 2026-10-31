"""Archive a supplementary public-index search and extract auditable evidence.

Acquisition is not an inclusion decision. No generative model or fabricated
appraisal is used here. Original searches and all returned records are retained.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import requests
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '20106UG03/Review_Records/Supplementary_Search'
OUT.mkdir(parents=True, exist_ok=True)
TEXT = OUT / 'Fulltext'
TEXT.mkdir(exist_ok=True)
PDF = OUT / 'Downloaded_Papers'
PDF.mkdir(exist_ok=True)
API = 'https://www.ebi.ac.uk/europepmc/webservices/rest/'
QUERIES = [
    'intrusion detection AND explainable',
    'intrusion detection AND concept drift',
    'cloud AND log AND anomaly detection',
]
QUERIES += [f'intrusion detection AND explainable AND FIRST_PDATE:[{y}-01-01 TO {y}-12-31]'
            for y in (2022, 2023, 2024, 2025)]
QUERIES += [f'intrusion detection AND concept drift AND FIRST_PDATE:[{y}-01-01 TO {y}-12-31]'
            for y in (2022, 2023, 2024, 2025)]
HEADERS = {'User-Agent': 'Project20106UG03-literature-review/1.0 (public OA research)'}


def get(url, params=None):
    last = None
    for _ in range(2):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=40)
            r.raise_for_status()
            return r
        except requests.RequestException as exc:
            last = exc
    raise last


def text(el):
    return ' '.join(' '.join(el.itertext()).split()) if el is not None else ''


def acquire(row):
    rid, pmcid = row['record_id'], row.get('pmcid')
    stable = hashlib.sha256(row['doi'].encode()).hexdigest()[:20]
    result = dict(row)
    result.update(fulltext_retrieved=False, pdf_retrieved=False, final_included=False)
    if not pmcid:
        return result
    try:
        target = TEXT / f'{stable}.xml'
        if not target.exists():
            target.write_bytes(get(API + pmcid + '/fullTextXML').content)
        tree = ET.fromstring(target.read_bytes())
        body = tree.find('body')
        if body is None:
            raise ValueError('No article body in XML')
        article_dois = [text(x).lower() for x in tree.findall('.//article-id')
                        if x.attrib.get('pub-id-type') == 'doi']
        if row['doi'] not in article_dois:
            raise ValueError('Requested DOI not present in article front matter')
        abstract = ' '.join(text(x) for x in tree.findall('./front/article-meta/abstract'))
        sections = [{'title': text(sec.find('title')), 'text': text(sec)}
                    for sec in body.findall('sec')]
        if not sections:
            sections = [{'title': 'Body', 'text': text(body)}]
        rights = [text(x) for x in tree.findall('.//permissions')]
        parsed = {'doi': row['doi'], 'record_id': rid, 'pmcid': pmcid,
                  'article_type': tree.attrib.get('article-type'),
                  'abstract': abstract, 'sections': sections, 'rights': rights,
                  'back': text(tree.find('back'))}
        (TEXT / f'{stable}.json').write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding='utf-8')
        result.update(fulltext_retrieved=True, fulltext_path=str(target.relative_to(ROOT)),
                      parsed_path=str((TEXT / f'{stable}.json').relative_to(ROOT)),
                      article_type=parsed['article_type'], rights=rights)
        # NCBI's documented 2026 Cloud Service replaces its retired OA service.
        # Use published public metadata; do not scrape a protected PDF endpoint.
        dest = PDF / f'{pmcid}_{stable}.pdf'
        cloud = get(f'https://pmc-oa-opendata.s3.amazonaws.com/{pmcid}.1/{pmcid}.1.json').json()
        if str(cloud.get('doi', '')).lower() != row['doi']:
            raise ValueError('Cloud metadata DOI mismatch')
        if cloud.get('is_retracted'):
            result['is_retracted'] = True
            return result
        cloud_path = cloud.get('pdf_url') or ''
        if not cloud_path.startswith('s3://pmc-oa-opendata/'):
            raise ValueError('No distributed PDF in public archive metadata')
        pdf_url = cloud_path.replace('s3://pmc-oa-opendata/', 'https://pmc-oa-opendata.s3.amazonaws.com/', 1)
        result['archive_licence'] = cloud.get('license_code')
        result['archive_metadata'] = cloud
        if not dest.exists():
            response = get(pdf_url)
            if not response.content.startswith(b'%PDF'):
                raise ValueError('OA PDF route did not return a PDF')
            dest.write_bytes(response.content)
        reader = PdfReader(dest)
        result.update(pdf_retrieved=True, pdf_path=str(dest.relative_to(ROOT)),
                      pdf_url=pdf_url, pdf_pages=len(reader.pages),
                      sha256=hashlib.sha256(dest.read_bytes()).hexdigest())
    except Exception as exc:
        result['retrieval_note'] = str(exc)[:250]
    return result


def main():
    records, logs = {}, []
    for n, query in enumerate(QUERIES, 1):
        exact = query + ' AND FIRST_PDATE:[2022-01-01 TO 2026-10-31] AND OPEN_ACCESS:Y'
        limit = 100 if n <= 3 else 25
        cache = OUT / f'query_{n:02d}.json'
        if cache.exists():
            payload = json.loads(cache.read_text(encoding='utf-8'))
        else:
            response = get(API + 'search', {'query': exact, 'format': 'json',
                           'resultType': 'core', 'pageSize': limit})
            payload = response.json()
            cache.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        logs.append({'query': exact, 'api_endpoint': API + 'search', 'page_size': limit,
                     'reported_hits': payload.get('hitCount'),
                     'retrieved': len(payload.get('resultList', {}).get('result', [])),
                     'exhaustive': False})
        for r in payload.get('resultList', {}).get('result', []):
            doi = r.get('doi', '').lower()
            if not doi:
                continue
            if doi not in records:
                ji = r.get('journalInfo', {})
                records[doi] = {'doi': doi, 'title': r.get('title'),
                    'authors': r.get('authorString'), 'journal': ji.get('journal', {}).get('title'),
                    'publication_date': r.get('firstPublicationDate'), 'pmcid': r.get('pmcid'),
                    'pubtypes': r.get('pubTypeList', {}).get('pubType', []),
                    'abstract': re.sub('<[^>]+>', '', r.get('abstractText', '')),
                    'licence_metadata': r.get('license'), 'query_routes': [],
                    'source': 'Europe PMC supplementary bounded OA search'}
            records[doi]['query_routes'].append(n)
    rows = sorted(records.values(), key=lambda r: r['doi'])
    for n, r in enumerate(rows, 1):
        r['record_id'] = f'E{n:03d}'
    (OUT / 'all_records.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'search_manifest.json').write_text(json.dumps({'search_date': '2026-10-31',
        'created_utc': datetime.now(timezone.utc).isoformat(), 'database': 'Europe PMC',
        'queries': logs, 'unique_dois': len(rows), 'raw_records': sum(x['retrieved'] for x in logs),
        'caveat': 'Supplementary top 100 per query; OA biased; not exhaustive; acquisition is not inclusion.'}, indent=2), encoding='utf-8')
    # The capped API corpus is small; keep every returned record for audit.
    # Preliminary title screen only. Full-text inclusion is recorded separately.
    candidate_rows = []
    for r in rows:
        title = r['title'].lower()
        security = re.search(r'intrusion|cyber|security|malware|threat|log anomaly|anomaly detection.*cloud|cloud.*anomaly', title)
        dimension = re.search(r'drift|explain|interpretab|incremental|continual|cloud|log|adaptive|adaptation', title)
        r['preliminary_scope'] = bool(security and dimension)
        if r['preliminary_scope']:
            candidate_rows.append(r)
    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(acquire, r) for r in candidate_rows]):
            results.append(future.result())
            if len(results) % 10 == 0:
                (OUT / 'retrieval_checkpoint.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
                print(f'Assessed retrieval {len(results)}/{len(candidate_rows)}', flush=True)
    results.sort(key=lambda r: r['record_id'])
    (OUT / 'retrieval_register.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'records': len(rows), 'xml_fulltexts': sum(r['fulltext_retrieved'] for r in results),
                      'pdfs': sum(r['pdf_retrieved'] for r in results)}, indent=2), flush=True)


if __name__ == '__main__':
    main()
