"""Audit and rasterise the latest native Word render of the journal manuscript."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from pypdf import PdfReader
import pypdfium2 as pdfium
import hashlib
import json
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
TMP=ROOT/'tmp/journal_paper'
OUT=ROOT/'outputs/SHAP_CloudTrail_Journal_Paper.docx'
PDF=Path(sys.argv[1]) if len(sys.argv)>1 else TMP/'render_final.pdf'
PAGES=TMP/('pages_'+PDF.stem)
PAGES.mkdir(exist_ok=True)
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}

with ZipFile(OUT) as z:
    assert z.testzip() is None
    root=E.fromstring(z.read('word/document.xml'))
    text=' '.join(root.xpath('//w:t/text()',namespaces=NS))
    assert len(root.findall('.//w:tbl',NS))==8
    assert len(root.findall('.//m:oMath',NS))==6
    assert len(root.findall('.//w:drawing',NS))==2
    assert not re.search(r'\[\[|\[@|TODO|TBD|turn\d+(?:search|view)',text)
    for token in ['0.4282','0.3397','0.7306','0.499080','251,613','1,939,207','44 tests']:
        assert token in text,token
    bibliography=text.split('References ')[-1]
    refs=[int(v) for v in re.findall(r'\[(\d+)\]',bibliography)]
    assert refs==list(range(1,21)),refs
    cited=set()
    before=text.split('References ')[0]
    for group in re.findall(r'\[([\d, ]+)\]',before):
        cited.update(map(int,group.split(',')))
    assert cited==set(range(1,21)),cited
    for node in root.findall('.//w:trPr',NS):
        assert node.find('w:trHeight',NS) is None

reader=PdfReader(PDF)
pdf=pdfium.PdfDocument(str(PDF))
assert len(pdf)==len(reader.pages)
for i,page in enumerate(pdf):
    page.render(scale=1.5).to_pil().save(PAGES/f'page-{i+1:02d}.png')
    extracted=reader.pages[i].extract_text() or ''
    assert 'Error! Reference source not found' not in extracted
    print(i+1,'words',len(extracted.split()),'start',extracted[:95].replace('\n',' '))
    page.close()
pdf.close()
audit={'pages':len(reader.pages),'tables':8,'native_equations':6,'figures':2,'references':20,
       'document_words':len(text.split()),'docx_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),
       'pdf':str(PDF),'page_images':str(PAGES)}
(TMP/'latest_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print(json.dumps(audit))
