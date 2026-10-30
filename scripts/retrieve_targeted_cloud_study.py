"""Acquire one open, author-hosted paper discovered outside the bounded search."""
import hashlib
import json
from pathlib import Path
from urllib.request import Request,urlopen
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'review_2022_2026/targeted_v4'
out.mkdir(parents=True,exist_ok=True)
pdf=out/'CORE07_Adediran_2026_CloudTrail_RAG.pdf'
manifest=out/'CORE07_manifest.json'
if manifest.exists():raise FileExistsError('Preserve earlier targeted source record')
url='https://www.open-access.bcu.ac.uk/16916/1/TSP_CMC_77606.pdf'
with urlopen(Request(url,headers={'User-Agent':'DriftDetection-LiteratureResearch/4.0'}),timeout=40) as response:
    payload=response.read(15_000_001)
if len(payload)>15_000_000 or not payload.startswith(b'%PDF'):raise ValueError('Invalid or over-cap PDF')
pdf.write_bytes(payload)
reader=PdfReader(pdf)
opening='\n'.join(page.extract_text() or '' for page in reader.pages[:2])
if '10.32604/cmc.2026.077606' not in opening:raise ValueError('Opening DOI does not match')
meta={'paper_id':'CORE07','doi':'10.32604/cmc.2026.077606',
      'title':'Retrieval-Augmented Large Language Model for AWS Cloud Threat Detection and Modelling: Cloudtrail Mitre ATT&CK Mapping',
      'authors':['Goodness Adediran','Kenny Awuson-David','Yussuf Ahmed'],
      'journal':'Computers, Materials & Continua','year':2026,'volume':'87','issue':'2','article':'100',
      'publisher_source':'https://www.techscience.com/cmc/v87n2/66657',
      'source_url':url,'licence':'CC BY 4.0 as stated by publisher','pdf_sha256':hashlib.sha256(payload).hexdigest(),
      'pdf_pages':len(reader.pages),'opening_doi_verified':True,'dataset_access':'available upon reasonable request',
      'discovery':'targeted source discovery outside bounded OpenAlex search; preserve separately in PRISMA accounting',
      'full_text_eligibility_complete':False,'independent_human_review':False,'final_included':False}
manifest.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
print(json.dumps(meta,indent=2))
