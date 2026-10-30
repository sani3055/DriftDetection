"""Reproducible assisted metadata screening followed by lawful OA retrieval.

Retained means full-text assessment required, not final study inclusion. All
records, including exclusions and uncertain cases, remain in the screening log.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import scripts.enrich_review_oa as retrieval


def screen(row):
    text=(str(row.get('title') or '')+' '+str(row.get('abstract') or '')).lower()
    title=str(row.get('title') or '').lower()
    security=bool(re.search(r'\b(intrusion|cyber.?security|malware|ransomware|ddos|ids|cyber.?attack|threat detection|network security|cloud security|cloud audit|cloudtrail|security monitoring)\b',text))
    cloud=bool(re.search(r'\b(cloudtrail|aws|cloud audit|audit logs?|cloud logs?|cloud security|cloud api)\b',text))
    log=bool(re.search(r'\blog.?based anomaly|\blog anomaly|\bsystem logs?\b',text))
    explanation=bool(re.search(r'\bshap\b|\bshapley\b|explainab|interpretabil|feature attribution',text))
    drift=bool(re.search(r'\bdrift\b|adaptiv|adaptation|incremental|continual|online learning|evolving',text))
    survey=bool(re.search(r'\bsurvey\b|\breview\b|bibliometric',title))
    journal=str(row.get('journal') or '').lower()
    reason=''
    if row.get('is_retracted'):
        status,reason='exclude_metadata','Retraction flag in source metadata'
    elif any(word in journal for word in ['procedia','conference series','proceedings']):
        status,reason='exclude_metadata','Conference/proceedings-series venue requires exclusion from journal-only corpus'
    elif re.match(r'\s*(correction|retraction|erratum|editorial)\b',title):
        status,reason='exclude_metadata','Nonresearch notice'
    elif (security and (cloud or explanation or drift)) or (log and (explanation or drift)):
        status,reason='retain_for_fulltext','Security/cloud/log scope plus a declared method dimension'
    elif not row.get('abstract'):
        status,reason='uncertain_fulltext','Abstract unavailable; title alone insufficient for exclusion'
    else:
        status,reason='exclude_metadata','No supported connection to the declared cybersecurity/cloud/log review question'
    return {'assisted_screening':status,'reason':reason,'security_signal':security,'cloud_signal':cloud,
            'log_signal':log,'explanation_signal':explanation,'drift_signal':drift,
            'study_role_pending_fulltext':'secondary_review' if survey else 'primary_or_other_research',
            'independent_human_screened':False,'final_inclusion':'pending'}


def main():
    root=ROOT/'review_2022_2026/search_v3'
    records=json.loads((root/'all_retrieved_candidates.json').read_text(encoding='utf-8'))
    for row in records:row.update(screen(row))
    (root/'assisted_screening.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    prior=json.loads((ROOT/'review_2022_2026/submission_audit/verified_candidates.json').read_text(encoding='utf-8'))
    original={row['doi'].lower():row for row in prior}
    previous=json.loads((ROOT/'review_2022_2026/retrieval_v3/retrieval_register.json').read_text(encoding='utf-8'))
    available={row['doi'].lower():row for row in previous if row.get('path')}
    retrieval.OUT=root/'retrieval'
    for path in [retrieval.OUT,retrieval.OUT/'Downloaded_Papers',retrieval.OUT/'extracted_text']:
        path.mkdir(parents=True,exist_ok=True)
    selected=[row for row in records if row['assisted_screening'] in {'retain_for_fulltext','uncertain_fulltext'}]
    results=[]
    def fetch(row):
        old=available.get(row['doi'],{})
        compatible={'paper_id':row['record_id'],'doi':row['doi'],'verified_title':row['title'],
                    'verified_pdf_path':old.get('path','')}
        work={'locations':row.get('locations',[]),'is_retracted':row.get('is_retracted')}
        result=retrieval.resolve_one(compatible,work)
        result['metadata_screening']=row['assisted_screening']
        result['original_candidate_id']=original.get(row['doi'],{}).get('paper_id','')
        return result
    print(f'{len(selected)} full-text candidates from {len(records)} records',flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for task in as_completed([pool.submit(fetch,row) for row in selected]):
            try:results.append(task.result())
            except Exception as exc:results.append({'status':'verification_error','error':str(exc)[:200]})
            if len(results)%10==0:print(f'Checked {len(results)}/{len(selected)} full-text candidates',flush=True)
    results.sort(key=lambda row:row.get('paper_id',''))
    (retrieval.OUT/'register.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    manifest={'search_date':'2026-10-30','retrieved_metadata':len(records),
        'retained_for_fulltext':sum(row['assisted_screening']=='retain_for_fulltext' for row in records),
        'uncertain_fulltext':sum(row['assisted_screening']=='uncertain_fulltext' for row in records),
        'excluded_metadata':sum(row['assisted_screening']=='exclude_metadata' for row in records),
        'readable_fulltexts':sum(bool(row.get('path')) for row in results),
        'opening_doi_found':sum(row.get('doi_on_opening_pages',False) for row in results),
        'critical_appraisal_completed_by_script':0,'final_included_studies':0,
        'caveat':'Single assisted metadata screen, not independent human screening. Retrieval does not complete critical appraisal.'}
    (root/'screening_retrieval_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,indent=2),flush=True)


if __name__=='__main__':main()
