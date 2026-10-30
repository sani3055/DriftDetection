"""Lawful OA-location retrieval, with public metadata and persistent provenance.

No paid access, authentication, CAPTCHA solving, bypasses or invented full-text
review status. Run with the bundled Python for pypdf support.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'review_2022_2026/retrieval_v3'
AGENT={'User-Agent':'DriftDetection-LiteratureResearch/3.0 (https://github.com/sani3055/DriftDetection)'}


def get_json(url):
    with urlopen(Request(url,headers=AGENT),timeout=30) as response:
        return json.load(response)


class PdfMeta(HTMLParser):
    def __init__(self): super().__init__();self.urls=[]
    def handle_starttag(self,tag,attributes):
        values=dict(attributes)
        if tag.lower()=='meta' and values.get('name','').lower()=='citation_pdf_url':
            if values.get('content'):self.urls.append(values['content'])


def inspect_pdf(path,doi):
    reader=PdfReader(path)
    text='\n\n'.join(page.extract_text() or '' for page in reader.pages)
    first='\n'.join(page.extract_text() or '' for page in reader.pages[:2])
    if len(reader.pages)==0 or len(first.strip())<40:raise ValueError('PDF has no readable opening text')
    return {'pages':len(reader.pages),'doi_on_opening_pages':doi.lower() in first.lower(),
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()},text


def resolve_one(record,work):
    doi=record['doi'].lower()
    paper_id=record['paper_id']
    digest=hashlib.sha256(doi.encode()).hexdigest()[:20]
    target=OUT/'Downloaded_Papers'/f'{paper_id}_{digest}.pdf'
    provenance=target.with_suffix('.provenance.json')
    result={'paper_id':paper_id,'doi':doi,'title':record['verified_title'],
            'full_text_reviewed':False,'attempts':[],'status':'not_retrieved'}
    old=ROOT/record.get('verified_pdf_path','__missing__')
    if old.is_file():
        meta,text=inspect_pdf(old,doi)
        result.update({'status':'existing_readable_pdf','path':str(old.relative_to(ROOT)),**meta})
        (OUT/'extracted_text'/f'{paper_id}.txt').write_text(text,encoding='utf-8')
        return result
    if target.exists():
        meta,text=inspect_pdf(target,doi)
        result.update({'status':'downloaded_oa','path':str(target.relative_to(ROOT)),**meta})
        if provenance.exists():result['provenance']=json.loads(provenance.read_text(encoding='utf-8'))
        (OUT/'extracted_text'/f'{paper_id}.txt').write_text(text,encoding='utf-8')
        return result
    locations=[]
    for location in work.get('locations',[]):
        if location.get('is_oa'):
            if location.get('pdf_url'):
                locations.append((location['pdf_url'],location,'pdf'))
            elif location.get('landing_page_url'):
                locations.append((location['landing_page_url'],location,'landing'))
    # A public author-hosted copy surfaced through the university research group.
    if doi=='10.1007/s10207-025-01118-9':
        locations.insert(0,('https://www.nics.uma.es/wp-content/papers/Lara2025.pdf',
                            {'version':'author-hosted copy','source':{'display_name':'University of Malaga NICS Lab'}},'pdf'))
    unique=set()
    for url,location,kind in locations[:4]:
        if url in unique:continue
        unique.add(url)
        try:
            with urlopen(Request(url,headers=AGENT),timeout=20) as response:
                payload=response.read(30_000_001)
                landed=response.geturl()
            if not payload.startswith(b'%PDF') and kind=='landing':
                parser=PdfMeta();parser.feed(payload[:1_000_000].decode('utf-8',errors='replace'))
                if not parser.urls:raise ValueError('OA landing page has no citation_pdf_url')
                pdf_url=urljoin(landed,parser.urls[0])
                with urlopen(Request(pdf_url,headers=AGENT),timeout=20) as response:
                    payload=response.read(30_000_001);landed=response.geturl()
            if len(payload)>30_000_000 or not payload.startswith(b'%PDF'):
                raise ValueError('Not a PDF or file exceeds 30 MB')
            target.write_bytes(payload)
            meta,text=inspect_pdf(target,doi)
            source={'requested_url':url,'final_url':landed,'location_metadata':location,
                    'retrieved_utc':datetime.now(timezone.utc).isoformat(),'doi':doi,**meta}
            provenance.write_text(json.dumps(source,ensure_ascii=False,indent=2),encoding='utf-8')
            (OUT/'extracted_text'/f'{paper_id}.txt').write_text(text,encoding='utf-8')
            result.update({'status':'downloaded_oa','path':str(target.relative_to(ROOT)),
                           'provenance':source,**meta})
            break
        except Exception as exc:
            result['attempts'].append({'url':url,'error':str(exc)[:200]})
    result['metadata_is_retracted']=work.get('is_retracted')
    return result


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    for part in [OUT,OUT/'metadata',OUT/'Downloaded_Papers',OUT/'extracted_text']:
        part.mkdir(parents=True,exist_ok=True)
    records=json.loads((ROOT/'review_2022_2026/submission_audit/verified_candidates.json').read_text(encoding='utf-8'))
    by_doi={}
    logs=[]
    for start in range(0,len(records),40):
        batch=records[start:start+40]
        query={'filter':'doi:'+'|'.join(row['doi'] for row in batch),'per-page':40}
        url='https://api.openalex.org/works?'+urlencode(query)
        cache=OUT/'metadata'/f'openalex_{start:03d}.json'
        try:
            if cache.exists():payload=json.loads(cache.read_text(encoding='utf-8'))
            else:
                payload=get_json(url)
                cache.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
            for work in payload.get('results',[]):
                key=str(work.get('doi','')).lower().removeprefix('https://doi.org/')
                by_doi[key]=work
            logs.append({'url':url,'returned':len(payload.get('results',[]))})
            print(f'OA metadata: {len(by_doi)} records',flush=True)
        except Exception as exc:
            logs.append({'url':url,'error':str(exc)[:240]})
            print(f'OA metadata unavailable: {exc}',flush=True)
            break  # Do not hammer a rate-limit or authentication barrier.
    results=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs=[pool.submit(resolve_one,row,by_doi.get(row['doi'].lower(),{})) for row in records]
        for job in as_completed(jobs):
            try:results.append(job.result())
            except Exception as exc:results.append({'status':'verification_error','error':str(exc)[:200]})
            if len(results)%10==0:print(f'OA retrieval checked {len(results)}/{len(records)}',flush=True)
    results.sort(key=lambda row:row.get('paper_id',''))
    (OUT/'retrieval_register.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    manifest={'search_date':'2026-10-30','created_utc':datetime.now(timezone.utc).isoformat(),
              'metadata_logs':logs,'candidates':len(records),'openalex_matches':len(by_doi),
              'readable_pdfs':sum(row['status'] in {'downloaded_oa','existing_readable_pdf'} for row in results),
              'new_oa_pdfs':sum(row['status']=='downloaded_oa' for row in results),
              'doi_on_opening_pages':sum(row.get('doi_on_opening_pages',False) for row in results),
              'full_text_reviews_completed_by_script':0,'final_included_studies':0}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,indent=2),flush=True)


if __name__=='__main__':main()
