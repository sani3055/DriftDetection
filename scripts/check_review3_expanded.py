"""Check source-slide preservation and render the expanded Review-3 deck."""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import re

from lxml import etree as E
from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[1]
TMP=ROOT/'tmp/review3_capstone_expanded19'
SOURCE=ROOT/'outputs/Review_3_Capstone_Final.pptx'
OUT=ROOT/'outputs/Review_3_Capstone_Expanded_19_Slides.pptx'
NS={'p':'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
POSITIONS=[1,2,3,4,5,6,7,8,9,10,12,16,17,18,19]

def content(root):
    values=[]
    for t in root.findall('.//a:t',NS):
        ancestors=t.xpath('ancestor::p:sp',namespaces=NS)
        if ancestors:
            off=ancestors[0].find('p:spPr/a:xfrm/a:off',NS)
            if off is not None and int(off.get('y','0'))>6200000 and int(off.get('x','0'))>8000000:
                continue
        values.append(t.text or '')
    return values

with ZipFile(SOURCE) as old,ZipFile(OUT) as new:
    assert new.testzip() is None
    slides=[n for n in new.namelist() if re.fullmatch(r'ppt/slides/slide\d+.xml',n)]
    notes=[n for n in new.namelist() if re.fullmatch(r'ppt/notesSlides/notesSlide\d+.xml',n)]
    assert len(slides)==19
    assert len(notes)==19
    count=sum(len(E.fromstring(new.read(n)).findall('.//a:tbl',NS)) for n in slides)
    assert count==11,count
    for original,target in enumerate(POSITIONS,1):
        before=E.fromstring(old.read(f'ppt/slides/slide{original}.xml'))
        after=E.fromstring(new.read(f'ppt/slides/slide{target}.xml'))
        assert content(before)==content(after),(original,target)
    all_text=' '.join(t for n in slides for t in E.fromstring(new.read(n)).xpath('.//a:t/text()',namespaces=NS))
    for token in ['0.7306','0.2873','−0.088478','−0.127232','−0.056106','0.0004344','0.943392','0.8080','0.7917','0.1301']:
        assert token in all_text,token
    assert 'Guide approval email: copy not attached' in all_text

pages=TMP/'pages'
pages.mkdir(exist_ok=True)
pdf=pdfium.PdfDocument(str(TMP/'final.pdf'))
reader=PdfReader(TMP/'final.pdf')
assert len(pdf)==19
for i,page in enumerate(pdf):
    page.render(scale=1.5).to_pil().save(pages/f'slide-{i+1:02d}.png')
    text=reader.pages[i].extract_text()
    print(i+1,text.splitlines()[0],'words',len(text.split()))
    page.close()
pdf.close()
audit={'slides':19,'native_tables':11,'notes':19,'all_original_slide_text_preserved_except_page_numbers':True,
       'original_slide_positions':POSITIONS,'added_slides':[11,13,14,15],
       'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
       'output_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest()}
(TMP/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print('AUDIT PASS',json.dumps(audit))
