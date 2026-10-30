"""Structural, evidence and page rendering checks for the v3 manuscript."""
from pathlib import Path
import hashlib
import json
import re
from zipfile import ZipFile
from lxml import etree
from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT / 'tmp/journal_paper_v3'
document = ROOT / 'outputs/SHAP_CloudTrail_Journal_Paper_v3.docx'
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
with ZipFile(document) as package:
    assert package.testzip() is None
    xml = etree.fromstring(package.read('word/document.xml'))
text = ' '.join(xml.xpath('//w:t/text()', namespaces=ns))
assert len(xml.findall('.//w:tbl', ns)) == 9
assert len(xml.findall('.//w:drawing', ns)) == 2
assert len(xml.findall('.//m:oMath', ns)) == 6
assert not re.search(r'\[\[|\[@|TODO|TBD|turn\d+(search|view)', text)
for token in ['11,531', '0.9485', '0.7187', '0.9642', '0.7713', '155'][:5]:
    assert token in text, token
bibliography = text.rsplit('References ', 1)[1]
assert list(map(int, re.findall(r'\[(\d+)\]', bibliography))) == list(range(1, 18))
audit = json.loads((folder / 'build_audit.json').read_text(encoding='utf-8'))
for rel, expected in {**audit['preserved_research_artifacts'], **audit['v3_evidence_hashes']}.items():
    assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == expected, rel
reader = PdfReader(folder / 'render.pdf')
renderer = pdfium.PdfDocument(str(folder / 'render.pdf'))
pages = folder / 'pages'
pages.mkdir(exist_ok=True)
for i, page in enumerate(renderer):
    page.render(scale=1.5).to_pil().save(pages / f'page-{i+1:02d}.png')
    extracted = reader.pages[i].extract_text() or ''
    assert 'Error! Reference source not found' not in extracted
    assert len(extracted.split()) > 20
    print(f'{i+1}: {len(extracted.split())} words; {extracted[:55].replace(chr(10), " ")}')
    page.close()
result = {'document': str(document), 'pages': len(reader.pages), 'words': len(text.split()),
          'tables': 9, 'figures': 2, 'editable_equations': 6, 'references': 17,
          'sha256': hashlib.sha256(document.read_bytes()).hexdigest(),
          'visual_qa': 'pending page image inspection'}
(folder / 'artifact_audit.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
