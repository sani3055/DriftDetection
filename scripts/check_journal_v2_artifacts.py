"""Verify paper artifacts, native result invariants and rasterise final renders."""
from pathlib import Path
import hashlib
import json
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')
from zipfile import ZipFile

from lxml import etree as E
from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[1]
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}


def main():
    kind=sys.argv[1]
    if kind=='research':
        document=ROOT/'outputs/SHAP_CloudTrail_Journal_Paper_v2.docx'
        pdf=ROOT/'tmp/journal_paper_v2/render.pdf'
        expected_tables, expected_figures, expected_equations=10,3,6
    else:
        document=ROOT/'outputs/CloudTrail_PRISMA_Review_Working_Draft.docx'
        pdf=ROOT/'tmp/review_paper_draft/render.pdf'
        expected_tables, expected_figures, expected_equations=3,0,0
    out=pdf.parent/'pages'
    out.mkdir(parents=True,exist_ok=True)
    with ZipFile(document) as archive:
        assert archive.testzip() is None
        root=E.fromstring(archive.read('word/document.xml'))
        text=' '.join(root.xpath('//w:t/text()',namespaces=NS))
        assert len(root.findall('.//w:tbl',NS))==expected_tables
        assert len(root.findall('.//w:drawing',NS))==expected_figures
        assert len(root.findall('.//m:oMath',NS))==expected_equations
        assert not re.search(r'\[\[|\[@|TODO|TBD|turn\d+(search|view)',text)
        if kind=='research':
            for token in ['0.9485','0.7187','0.7735','0.4343','11,531','59 tests']:
                assert token in text,token
            bibliography=text.split('References ')[-1]
            assert [int(x) for x in re.findall(r'\[(\d+)\]',bibliography)]==list(range(1,22))
            audit=json.loads((ROOT/'tmp/journal_paper_v2/build_audit.json').read_text())
            for rel,old_hash in audit['preserved_research_artifacts'].items():
                assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==old_hash
        else:
            assert 'final systematic synthesis remains unfinished' in text
            assert '106' in text
            assert len(re.findall(r'CORE\d\d  ',text))==6
            assert len(re.findall(r'P\d\d\d  ',text))==100
    reader=PdfReader(pdf)
    renderer=pdfium.PdfDocument(str(pdf))
    for i,page in enumerate(renderer):
        page.render(scale=1.5).to_pil().save(out/f'page-{i+1:02d}.png')
        extracted=reader.pages[i].extract_text() or ''
        assert 'Error! Reference source not found' not in extracted
        print(f'{i+1}: {len(extracted.split())} words; {extracted[:65].replace(chr(10)," ")}')
        page.close()
    result={'document':str(document),'pages':len(reader.pages),'words':len(text.split()),
            'tables':expected_tables,'figures':expected_figures,'equations':expected_equations,
            'sha256':hashlib.sha256(document.read_bytes()).hexdigest()}
    (pdf.parent/'artifact_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
