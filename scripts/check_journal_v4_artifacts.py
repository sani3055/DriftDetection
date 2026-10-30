"""Check manuscript structure, cited evidence hashes, and render page images."""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import re

from lxml import etree
from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT / 'tmp/journal_paper_v4'
document = ROOT / 'outputs/SHAP_CloudTrail_Journal_Paper_v4.docx'
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
with ZipFile(document) as package:
    assert package.testzip() is None
    xml = etree.fromstring(package.read('word/document.xml'))
text = ' '.join(xml.xpath('//w:t/text()', namespaces=ns))
assert len(xml.findall('.//w:tbl', ns)) == 10
assert len(xml.findall('.//w:drawing', ns)) == 1
assert len(xml.findall('.//m:oMath', ns)) == 6
assert not re.search(r'\[\[|\[@|TODO|TBD|turn\d+(search|view)', text)
for token in ['11,531', '42,513', '8,816', '93', '0.9485', '0.7187']:
    assert token in text, token
audit = json.loads((folder / 'build_audit.json').read_text(encoding='utf-8'))
for rel, expected in {**audit['preserved_research_artifacts'], **audit['v4_evidence_hashes']}.items():
    assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == expected, rel
assert hashlib.sha256(document.read_bytes()).hexdigest() == audit['output_sha256']
reader = PdfReader(folder / 'render.pdf')
renderer = pdfium.PdfDocument(str(folder / 'render.pdf'))
pages = folder / 'pages'
pages.mkdir(exist_ok=True)
for i, page in enumerate(renderer):
    page.render(scale=1.5).to_pil().save(pages / f'page-{i+1:02d}.png')
    extracted = reader.pages[i].extract_text() or ''
    assert 'Error! Reference source not found' not in extracted
    assert len(extracted.split()) > 20
    print(f'{i+1}: {len(extracted.split())} words')
    page.close()
result = {'document': str(document), 'pages': len(reader.pages), 'words': len(text.split()),
          'tables': 10, 'figures': 1, 'editable_equations': 6,
          'references': len(audit['references_in_citation_order']),
          'sha256': audit['output_sha256'], 'visual_qa': 'pending page image inspection'}
(folder / 'artifact_audit.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
