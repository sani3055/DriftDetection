"""Resolve manuscript DOI links against Crossref metadata for review."""
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher
from html import unescape
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from docx import Document

ROOT=Path(__file__).resolve().parents[1]
doc=Document(ROOT/'outputs/CloudTrail_Journal_Manuscript_Guide_Review_Final.docx')
refs=[p.text for p in doc.paragraphs if re.match(r'^\[\d+\]',p.text)]
items=[]
for ref in refs:
    found=re.search(r'https://doi\.org/(10\.\d{4,9}/[^\s]+)',ref,re.I)
    if found:items.append((int(re.match(r'^\[(\d+)\]',ref).group(1)),found.group(1).rstrip('.,;'),ref))

def resolve(item):
    number,doi,ref=item
    try:
        req=Request('https://api.crossref.org/works/'+quote(doi,safe=''),headers={'User-Agent':'ResearchReferenceAudit/1.0'})
        with urlopen(req,timeout=20) as response: data=json.load(response)['message']
        title=unescape(data.get('title',[''])[0])
        def norm(s):return re.sub(r'[^a-z0-9]+','',s.lower())
        # Substring is robust to author/venue text without assuming exact punctuation.
        in_ref=norm(title) in norm(ref)
        return {'number':number,'doi':doi,'status':'resolved','crossref_title':title,
                'title_in_reference':in_ref,'year':(data.get('published') or {}).get('date-parts')}
    except (HTTPError,URLError,TimeoutError,KeyError,ValueError) as exc:
        return {'number':number,'doi':doi,'status':'unresolved','reason':str(exc)}

with ThreadPoolExecutor(max_workers=4) as pool: results=list(pool.map(resolve,items))
out=ROOT/'tmp/journal_guide_review/reference_audit.json'
out.write_text(json.dumps({'doi_references':len(items),'results':results},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'doi_references':len(items),'resolved':sum(r['status']=='resolved' for r in results),
                  'title_matches':sum(r.get('title_in_reference',False) for r in results),
                  'attention':[r for r in results if r['status']!='resolved' or not r.get('title_in_reference')]},indent=2))
