"""Verify bibliographic identity and preserve a narrowly scoped reading set.

The selected set is an AI-assisted evidence collection, not a claim that every
eligible article in every database has been screened independently.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import re
import requests

ROOT=Path(__file__).resolve().parents[1]
REC=ROOT/'20106UG03/Review_Records'
CACHE=REC/'Crossref_Metadata'
CACHE.mkdir(exist_ok=True)
EXCLUSIONS={
 'S0008':'Secondary review retained as contextual bibliography, not primary-study evidence',
 'S0022':'Secondary review retained as contextual bibliography, not primary-study evidence',
 'S0023':'Secondary review retained as contextual bibliography, not primary-study evidence',
 'S0027':'Broad secondary AI review rather than primary detection study',
 'S0030':'Secondary review retained as contextual bibliography, not primary-study evidence',
 'S0088':'Secondary review retained as contextual bibliography, not primary-study evidence',
 'S0126':'Secondary review retained as contextual bibliography, not primary-study evidence',
 'S0138':'Secondary review on federated optimization, not primary-study evidence',
 'S0216':'Secondary review retained as contextual bibliography, not primary-study evidence',
 'E333':'Secondary review retained as contextual bibliography, not primary-study evidence',
 'E382':'Secondary review retained as contextual bibliography, not primary-study evidence',
 'E388':'Secondary vehicle-security survey, not primary-study evidence',
 'E409':'Secondary malware survey, not primary-study evidence',
 'E252':'Physical perimeter coverage regression, not cybersecurity intrusion detection',
 'E260':'Physical perimeter coverage regression, not cybersecurity intrusion detection',
 'E276':'Augmented-reality technologies review, outside detection question',
 'S0219':'Standalone phishing-URL classification, outside operational log and intrusion-monitoring focus',
 'E092':'Cryptographic architecture rather than explainable or drift-diagnosing detector',
 'E125':'Encryption and user access mechanism rather than evaluated ML drift or explanation method',
 'E064':'Integrated blockchain/cloud architecture without a direct drift or explanation focus',
 'E060':'Generic network-classifier architecture without a direct drift or explanation focus',
 'E141':'Broad healthcare cloud-security architecture rather than drift or explanation diagnosis',
 'E087':'Vehicular network feature-selection pipeline without a direct drift or explanation focus',
 'S0141':'Operational remediation evaluation without attack-induced evaluation; retained as context only',
 'E150':'Broad cross-domain resilience architecture, retained as operational context only',
 'E384':'Multi-agent defense communication architecture rather than drift or explanation diagnosis',
 'E086':'Ransomware-specific search/defense pipeline outside the log and intrusion-monitoring focus',
}


def one(row):
    rid=row['record_id']; dest=CACHE/f'{rid}.json'
    result={'record_id':rid,'doi':row['doi']}
    try:
        if dest.exists():
            payload=json.loads(dest.read_text(encoding='utf-8'))
        else:
            response=requests.get('https://api.crossref.org/works/'+row['doi'],timeout=30,
                headers={'User-Agent':'Project20106UG03-reference-verification/1.0'})
            response.raise_for_status();payload=response.json()
            dest.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
        m=payload['message']; dates=[]
        for field in ('published-online','published-print','published'):
            parts=(m.get(field,{}).get('date-parts') or [[]])[0]
            if parts:
                dates.append((parts,field))
        parts,field=min(dates,key=lambda x:tuple(x[0])) if dates else ([],None)
        result.update(type=m.get('type'),title=(m.get('title') or [''])[0],
            journal=(m.get('container-title') or [''])[0],date_parts=parts,date_source=field,
            authors=[(' '.join(filter(None,[a.get('given'),a.get('family')])) or a.get('name','')) for a in m.get('author',[])],
            volume=m.get('volume'),issue=m.get('issue'),page=m.get('page'),article_number=m.get('article-number'),
            licences=m.get('license',[]),update_notices=m.get('update-to',[]),crossref_verified=True)
        result['in_period']=bool(parts and 2022<=parts[0]<=2026 and
            not (parts[0]==2026 and len(parts)>1 and parts[1]>10))
    except Exception as exc:
        result.update(crossref_verified=False,error=str(exc)[:220])
    return result


def main():
    rows=json.loads((REC/'available_evidence_cards.json').read_text(encoding='utf-8'))
    verified=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for f in as_completed([pool.submit(one,r) for r in rows]):
            verified.append(f.result())
    by_id={r['record_id']:r for r in verified}
    chosen=[];screening=[]
    for r in rows:
        rid=r['record_id'];v=by_id[rid]
        status='selected_for_evidence_collection'
        reason='Primary study of explanation or adaptation in security detection or system logs'
        if rid in EXCLUSIONS:
            status='context_or_out_of_scope';reason=EXCLUSIONS[rid]
        elif not v.get('crossref_verified') or v.get('type')!='journal-article' or not v.get('in_period'):
            status='metadata_pending';reason='Journal type or eligible date requires resolution'
        screening.append({'record_id':rid,'doi':r['doi'],'status':status,'reason':reason,
             'assessment_stream':'single AI-assisted assessment','independent_human_review':False})
        if status=='selected_for_evidence_collection':
            r['verified_bibliography']=v;chosen.append(r)
    # Initial three IDs and files are retained to preserve earlier notebook links.
    order={'S0196':0,'CORE05':1,'CORE07':2}
    chosen.sort(key=lambda r:(order.get(r['record_id'],3),r['verified_bibliography']['date_parts'],r['doi']))
    for i,r in enumerate(chosen,1):r['review_id']=f'R{i:03d}'
    for name,obj in [('bibliography_verification.json',verified),('evidence_selection_log.json',screening),('selected_evidence_collection.json',chosen)]:
        (REC/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'cards_assessed':len(rows),'selected':len(chosen),
        'metadata_pending':[r for r in screening if r['status']=='metadata_pending'],
        'context_or_out_of_scope':sum(r['status']=='context_or_out_of_scope' for r in screening)},indent=2))


if __name__=='__main__':main()
