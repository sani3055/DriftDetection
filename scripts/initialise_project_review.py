"""Create the project-numbered review workspace without inventing inclusions."""
from pathlib import Path
import hashlib
import json
import shutil

from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'20106UG03'
RECORDS=OUT/'Review_Records'
PAPERS=OUT/'Downloaded_Papers_20106UG03'
for folder in (OUT,RECORDS,PAPERS,RECORDS/'Fulltext_Extraction'):
    folder.mkdir(parents=True,exist_ok=True)
identity=json.loads((ROOT/'review_2022_2026/search_v3/pdf_identity_audit.json').read_text(encoding='utf-8'))
metadata={r['doi'].lower():r for r in json.loads((ROOT/'review_2022_2026/search_v3/all_retrieved_candidates.json').read_text(encoding='utf-8'))}
verified={r['doi'].lower():r for r in json.loads((ROOT/'review_2022_2026/submission_audit/verified_candidates.json').read_text(encoding='utf-8'))}
seen={}; queue=[]; duplicates=[]
for row in identity:
    path=ROOT/row['path']
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest!=row['sha256']:raise ValueError('Prior PDF identity changed')
    if digest in seen:
        duplicates.append({'doi':row['doi'],'same_pdf_as_doi':seen[digest],'sha256':digest});continue
    seen[digest]=row['doi']
    doi=row['doi'].lower();m=metadata.get(doi,{});v=verified.get(doi,{})
    queue.append({'record_id':row['paper_id'],'doi':doi,'title':row['title'],
        'journal':v.get('verified_journal') or m.get('journal'),
        'publication_date':v.get('verified_first_publication_date') or m.get('publication_date'),
        'source_type':v.get('verified_type') or m.get('source_type'),
        'path':str(path.relative_to(ROOT)),'sha256':digest,'pdf_pages':row['pages'],
        'automated_identity':row['automated_identity'],
        'status':'awaiting_fulltext_screening','final_included':False,
        'fulltext_assessment_complete':False,'summary_complete':False})
targeted=ROOT/'review_2022_2026/targeted_v4/CORE07_Adediran_2026_CloudTrail_RAG.pdf'
digest=hashlib.sha256(targeted.read_bytes()).hexdigest()
if digest not in seen:
    queue.append({'record_id':'CORE07','doi':'10.32604/cmc.2026.077606',
        'title':'Retrieval-Augmented Large Language Model for AWS Cloud Threat Detection and Modelling: Cloudtrail Mitre ATT&CK Mapping',
        'journal':'Computers, Materials & Continua','publication_date':'2026-02-28','source_type':'journal-article',
        'path':str(targeted.relative_to(ROOT)),'sha256':digest,'pdf_pages':len(PdfReader(targeted).pages),
        'automated_identity':'targeted_previous_source_check','status':'awaiting_fulltext_screening',
        'final_included':False,'fulltext_assessment_complete':False,'summary_complete':False,
        'discovery':'additional targeted discovery; not one of the original 392 bounded-search records'})

selected=[('R001','review_2022_2026/retrieval_v3/Downloaded_Papers/CORE03_b65937b4e64ace3787dd.pdf'),
          ('R002','review_2022_2026/submission_audit/Downloaded_Papers/CORE05_c104141fd5c3ba61e552.pdf'),
          ('R003','review_2022_2026/targeted_v4/CORE07_Adediran_2026_CloudTrail_RAG.pdf')]
batch=[]
for record_id,relative in selected:
    source=ROOT/relative;reader=PdfReader(source)
    pages=[p.extract_text() or '' for p in reader.pages]
    # The licence statement has been inspected in each of these three papers.
    if 'Creative Commons' not in '\n'.join(pages):raise ValueError('Expected explicit reuse licence')
    dest=PAPERS/(record_id+'_'+source.name)
    if dest.exists() and dest.read_bytes()!=source.read_bytes():raise FileExistsError(dest)
    if not dest.exists():shutil.copy2(source,dest)
    (RECORDS/'Fulltext_Extraction'/(record_id+'.json')).write_text(json.dumps(
        {'record_id':record_id,'source':relative,'pdf_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
         'pages':[{'pdf_page':i+1,'text':t} for i,t in enumerate(pages)]},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    batch.append({'record_id':record_id,'file':str(dest.relative_to(ROOT)),
                  'source':relative,'pages':len(pages),'licence':'CC BY 4.0 statement in full text',
                  'status':'assessment_in_progress_not_finally_included'})
(RECORDS/'fulltext_screening_queue.json').write_text(json.dumps(queue,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(RECORDS/'duplicate_file_records.json').write_text(json.dumps(duplicates,indent=2)+'\n',encoding='utf-8')
(RECORDS/'initial_batch.json').write_text(json.dumps(batch,indent=2)+'\n',encoding='utf-8')
counts={'project_number':'20106UG03','unique_readable_candidate_pdf_files':len(queue),
        'original_identity_records':len(identity),'exact_duplicate_records_not_recounted':len(duplicates),
        'papers_copied_to_project_folder':len(batch),'final_inclusions':0,'completed_critical_appraisals':0,
        'target_journal_papers':100,'date_cutoff':'2026-10-31',
        'caveat':'Candidate PDF count is not an eligible-study count; targeted source tracked separately'}
(RECORDS/'starting_inventory.json').write_text(json.dumps(counts,indent=2)+'\n',encoding='utf-8')
print(json.dumps(counts,indent=2))
