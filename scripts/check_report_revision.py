"""Render every final PDF page and audit report citations/navigation."""
from pathlib import Path
import argparse
import json
import re
from zipfile import ZipFile
from lxml import etree as E
import pypdfium2 as pdfium
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--report',type=Path,default=ROOT/'outputs/BCSE497J_Capstone_Report_Submission_Ready.docx')
parser.add_argument('--qa-dir',type=Path,default=ROOT/'tmp/report_final_revision')
parser.add_argument('--pdf',type=Path,help='Use a fresh native export when a previous PDF is open.')
args=parser.parse_args()
TMP=args.qa_dir
OUT=args.report
PAGES=TMP/'pages'
PAGES.mkdir(exist_ok=True)
pdf_path=args.pdf or TMP/'final.pdf'
pdf=pdfium.PdfDocument(str(pdf_path))
reader=PdfReader(pdf_path)
inventory=[]
for i,page in enumerate(pdf):
    image=page.render(scale=1.5).to_pil()
    image.save(PAGES/f'page-{i+1:02d}.png')
    text=reader.pages[i].extract_text()
    lines=[s.strip() for s in text.splitlines() if s.strip()]
    inventory.append({'physical_page':i+1,'first_lines':lines[:3],'last_lines':lines[-3:],'characters':len(text)})
    print(i+1,' | '.join(lines[:2]),' ... ',' | '.join(lines[-2:]))
    page.close()
pdf.close()
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(OUT) as z:root=E.fromstring(z.read('word/document.xml'))
body=root.find('w:body',ns)
text=lambda e:''.join(e.xpath('.//w:t/text()',namespaces=ns))
chapter=next(i for i,e in enumerate(body) if text(e)=='1 INTRODUCTION')
refheading=next(i for i,e in enumerate(body) if text(e)=='9 REFERENCES')
sequence=[]
for e in list(body)[chapter:refheading]:
    for match in re.finditer(r'\[(\d+)\]',text(e)):
        value=int(match.group(1))
        if value not in sequence:sequence.append(value)
assert sequence==list(range(1,17)),sequence
references=[text(e) for e in body if re.match(r'^\[\d+\]',text(e))]
assert len(references)==16
assert not any('Error!' in p.extract_text() for p in reader.pages)
assert not any('<<' in text(e) or 'Designation>' in text(e) for e in body)
audit=json.loads((TMP/'audit.json').read_text())
audit.update({'rendered_pages':len(reader.pages),'citation_first_appearance':sequence,'all_16_references_cited':True,'pdf_pages':inventory})
(TMP/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print('AUDIT PASSED:',len(reader.pages),'pages;',len(references),'cited references')
