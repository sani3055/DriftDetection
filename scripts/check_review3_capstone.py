"""Read-only final-slide render and package checks for the Review-3 deck."""
from pathlib import Path
from zipfile import ZipFile
import json
import re

from lxml import etree as E
import pypdfium2 as pdfium
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
TMP=ROOT/'tmp/review3_capstone_final'
OUT=ROOT/'outputs/Review_3_Capstone_Final.pptx'
PAGES=TMP/'pages'
PAGES.mkdir(exist_ok=True)
pdf=pdfium.PdfDocument(str(TMP/'final.pdf'))
reader=PdfReader(TMP/'final.pdf')
assert len(pdf)==15
for i,page in enumerate(pdf):
    page.render(scale=1.5).to_pil().save(PAGES/f'slide-{i+1:02d}.png')
    text=reader.pages[i].extract_text()
    print(i+1, text.splitlines()[0], 'words', len(text.split()))
    page.close()
pdf.close()
ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
with ZipFile(OUT) as z:
    assert z.testzip() is None
    note_parts=[p for p in z.namelist() if re.fullmatch(r'ppt/notesSlides/notesSlide\d+.xml',p)]
    slide_parts=[p for p in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+.xml',p)]
    native_tables=sum(len(E.fromstring(z.read(p)).findall('.//a:tbl',ns)) for p in slide_parts)
    assert native_tables==7
    assert len(note_parts)==15
    for p in slide_parts:
        text=' '.join(E.fromstring(z.read(p)).xpath('//a:t/text()',namespaces=ns))
        assert not any(token in text for token in ['<<Name>>','<<Project Title>>','<To …>'])
    print('AUDIT PASS:',len(slide_parts),'slides,',native_tables,'native tables,',len(note_parts),'speaker-note parts')
