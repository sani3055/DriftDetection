"""Check source preservation and render the local review deck for visual QA."""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import re
from lxml import etree as E
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r'D:\Downloads\Review_3_Capstone_Formatted.pptx')
OUT = ROOT / 'outputs/Review_3_Capstone_Formatted_Checked.pptx'
TMP = ROOT / 'tmp/formatted_review_check'
NS = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}

with ZipFile(SOURCE) as before, ZipFile(OUT) as after:
    assert after.testzip() is None
    slide_names = [n for n in after.namelist() if re.fullmatch(r'ppt/slides/slide\d+.xml', n)]
    assert len(slide_names) == 19
    tables = 0
    for number in range(1, 20):
        name = f'ppt/slides/slide{number}.xml'
        old = E.fromstring(before.read(name))
        new = E.fromstring(after.read(name))
        assert old.xpath('.//a:t/text()', namespaces=NS) == new.xpath('.//a:t/text()', namespaces=NS), number
        tables += len(new.findall('.//a:tbl', NS))
        note = f'ppt/notesSlides/notesSlide{number}.xml'
        assert E.fromstring(before.read(note)).xpath('.//a:t/text()', namespaces=NS) == E.fromstring(after.read(note)).xpath('.//a:t/text()', namespaces=NS), ('notes', number)
    assert tables == 11

pages = TMP / 'final_pages'
pages.mkdir(exist_ok=True)
pdf = pdfium.PdfDocument(str(TMP / 'final.pdf'))
assert len(pdf) == 19
for i, page in enumerate(pdf):
    page.render(scale=1.5).to_pil().save(pages / f'slide-{i + 1:02d}.png')
    page.close()
pdf.close()
audit = {'slides': 19, 'native_tables': tables, 'all_slide_text_preserved': True,
         'speaker_notes_preserved': True,
         'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
         'output_sha256': hashlib.sha256(OUT.read_bytes()).hexdigest()}
(TMP / 'audit.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
print(json.dumps(audit, indent=2))
