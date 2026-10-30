from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import json
import urllib.request

NS = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{'+NS['w']+'}'
def text(e): return ''.join(e.xpath('.//w:t/text()',namespaces=NS))
for path in [Path(r'D:\Downloads\BCSE497J_Capstone_Report_Final_fixed.docx'), Path(r'D:\Downloads\BCSE497J Project I Report - Template FINAlL Updated  (2).docx')]:
    print('\nFILE',path.name)
    with ZipFile(path) as z: root = E.fromstring(z.read('word/document.xml'))
    body=root.find(W+'body')
    if 'fixed' in path.name:
        print('FRONT',[(i,text(body[i]),E.tostring(body[i].find(W+'pPr'),encoding='unicode').split('>')[-2:] if body[i].find(W+'pPr') is not None else '') for i in range(57,66)])
        print('GUIDE CELLS',[(i,text(c)) for i,c in enumerate(body[18].findall('.//'+W+'tc'))])
        print('HEADINGS',[(i,text(p),p.xpath('./w:pPr/w:outlineLvl/@w:val',namespaces=NS),p.xpath('./w:pPr/w:pStyle/@w:val',namespaces=NS)) for i,p in enumerate(body) if p.find(W+'bookmarkStart') is not None])
    else:
        print('FRONT',[(i,text(p)) for i,p in enumerate(body) if i<110])
        print('TABLES',[[[text(c) for c in row.findall(W+'tc')] for row in tbl.findall(W+'tr')][:5] for tbl in body.findall(W+'tbl')][:5])
    print('GEOMETRY',[dict(e.attrib) for e in root.xpath('//w:sectPr/w:pgSz|//w:sectPr/w:pgMar|//w:sectPr/w:pgNumType',namespaces=NS)])

for doi in ['10.1109/ICNGN67480.2025.11413642','10.1145/3638777','10.1002/widm.1536','10.1016/j.compeleceng.2022.108239']:
    try:
        req=urllib.request.Request('https://api.crossref.org/works/'+doi,headers={'User-Agent':'CapstoneBibliographyCheck/1.0'})
        with urllib.request.urlopen(req,timeout=25) as res: record=json.load(res)['message']
        print('METADATA',doi,json.dumps({k:record.get(k) for k in ['title','author','container-title','volume','issue','page','article-number','published']},ensure_ascii=False))
    except Exception as exc: print('METADATA ERROR',doi,str(exc))
