"""Archive all hits of a new public-index search; no final inclusion decisions."""
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'review_2022_2026/search_v3'
QUERIES=['explainable intrusion detection','concept drift intrusion detection',
         'cloud audit log anomaly detection','SHAP concept drift cybersecurity']


def abstract(work):
    words=[]
    for word,positions in (work.get('abstract_inverted_index') or {}).items():
        words.extend((position,word) for position in positions)
    return ' '.join(word for _,word in sorted(words))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    logs=[];candidates={}
    for index,query in enumerate(QUERIES):
        params={'search':query,'filter':'from_publication_date:2022-01-01,to_publication_date:2026-10-30,type:article,primary_location.source.type:journal,has_doi:true',
                'per-page':100,'sort':'relevance_score:desc'}
        url='https://api.openalex.org/works?'+urlencode(params)
        cache=OUT/f'query_{index+1:02d}.json'
        try:
            if cache.is_file():payload=json.loads(cache.read_text(encoding='utf-8'))
            else:
                request=Request(url,headers={'User-Agent':'DriftDetection-SystematicSearch/3.0 (https://github.com/sani3055/DriftDetection)'})
                with urlopen(request,timeout=30) as response:payload=json.load(response)
                cache.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
            logs.append({'query':query,'exact_url':url,'reported_total_hits':payload.get('meta',{}).get('count'),
                         'retrieved_records':len(payload.get('results',[])),'limit':100,
                         'search_exhausted':len(payload.get('results',[]))>=payload.get('meta',{}).get('count',10**9)})
            for work in payload.get('results',[]):
                doi=str(work.get('doi') or '').lower().removeprefix('https://doi.org/')
                if not doi:continue
                if doi not in candidates:
                    primary=work.get('primary_location') or {};source=primary.get('source') or {}
                    candidates[doi]={'doi':doi,'title':work.get('title'),'publication_date':work.get('publication_date'),
                        'journal':source.get('display_name'),'source_type':source.get('type'),
                        'authors':'; '.join(item.get('author',{}).get('display_name','') for item in work.get('authorships',[])),
                        'abstract':abstract(work),'is_retracted':work.get('is_retracted'),
                        'is_oa':(work.get('open_access') or {}).get('is_oa'),
                        'locations':work.get('locations',[]),'query_routes':[],
                        'screening_status':'title_abstract_pending','final_inclusion':'pending'}
                candidates[doi]['query_routes'].append(query)
            print(f'Query {index+1}: {len(candidates)} unique DOI candidates',flush=True)
        except Exception as exc:
            logs.append({'query':query,'exact_url':url,'error':str(exc)[:240]})
            print(f'Search stopped: {exc}',flush=True)
            break
    records=sorted(candidates.values(),key=lambda row:row['doi'])
    for i,row in enumerate(records,1):row['record_id']=f'S{i:04d}'
    (OUT/'all_retrieved_candidates.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    manifest={'search_date':'2026-10-30','created_utc':datetime.now(timezone.utc).isoformat(),'database':'OpenAlex',
        'query_logs':logs,'unique_dois_retrieved':len(records),'raw_records_retrieved':sum(row.get('retrieved_records',0) for row in logs),
        'limitation':'Top 100 relevance-ranked hits per query; not an exhaustive database search or completed systematic review. All retrieved hits are retained.',
        'final_included_studies':0}
    (OUT/'search_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'unique_candidates':len(records),'all_queries_completed':len(logs)==len(QUERIES) and all('error' not in row for row in logs)},indent=2))


if __name__=='__main__':main()
