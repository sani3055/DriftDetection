"""Verify the selected slides were replaced without changing the remaining content."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import re
import json
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[1]
TMP=ROOT/'tmp/review_simple_summary'
SOURCE=Path(r'D:\Downloads\Review_3_23BCT0029.pptx')
OUT=ROOT/'outputs/Review_3_23BCT0029_Simplified.pptx'
NS={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main'}

def text_without_footer(root):
    result=[]
    for node in root.findall('.//a:t',NS):
        shapes=node.xpath('ancestor::p:sp',namespaces=NS)
        if shapes:
            off=shapes[0].find('p:spPr/a:xfrm/a:off',NS)
            if off is not None and int(off.get('y','0'))>6190000 and int(off.get('x','0'))>8090000:
                continue
        result.append(node.text or '')
    return result

with ZipFile(SOURCE) as before,ZipFile(OUT) as after:
    assert after.testzip() is None
    slides=[n for n in after.namelist() if re.fullmatch(r'ppt/slides/slide\d+.xml',n)]
    assert len(slides)==17
    for original,target in [(i,i) for i in range(1,14)]+[(17,15),(18,16),(19,17)]:
        assert text_without_footer(E.fromstring(before.read(f'ppt/slides/slide{original}.xml')))==text_without_footer(E.fromstring(after.read(f'ppt/slides/slide{target}.xml'))),(original,target)
    summary=E.fromstring(after.read('ppt/slides/slide14.xml'))
    text=' '.join(summary.xpath('.//a:t/text()',namespaces=NS))
    assert 'What We Learned from the Tests' in text
    assert 'Future unseen data still needs testing.' in text
    assert len(summary.findall('.//a:buChar',NS))==6
    all_text=' '.join(' '.join(E.fromstring(after.read(n)).xpath('.//a:t/text()',namespaces=NS)) for n in slides)
    for old_title in ['Paired Statistical Evidence','Detector and Sample Size Robustness','External Validation']:
        assert old_title not in all_text

pages=TMP/'final_pages'
pages.mkdir(exist_ok=True)
doc=pdfium.PdfDocument(str(TMP/'final.pdf'))
assert len(doc)==17
for i,page in enumerate(doc):
    page.render(scale=1.5).to_pil().save(pages/f'slide-{i+1:02d}.png')
    page.close()
doc.close()
audit={'slides':17,'replacement_slide':14,'removed_source_slides':[14,15,16],
       'remaining_slide_text_preserved_except_numbering':True,'native_summary_bullets':6}
(TMP/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print(json.dumps(audit))
