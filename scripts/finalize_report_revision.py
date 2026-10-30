"""Targeted final-review edits; preserve every package part except document.xml.

Native Word is used only on a disposable copy to calculate PAGEREF results.
Its package rewrites are not propagated into the final template-derived file.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile, ZIP_DEFLATED

from lxml import etree as E

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r'D:\Downloads\BCSE497J_Capstone_Report_Final_fixed.docx')
OUT = ROOT / 'outputs/BCSE497J_Capstone_Report_Submission_Ready.docx'
TMP = ROOT / 'tmp/report_final_revision'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
NS = {'w': W[1:-1]}
XML = '{http://www.w3.org/XML/1998/namespace}'


def el(name, **attrs):
    return E.Element(W + name, {W+k: str(v) for k, v in attrs.items()})


def txt(node):
    return ''.join(node.xpath('.//w:t/text()', namespaces=NS))


def prop(parent, name, **attrs):
    found = parent.find(W+name)
    if found is None:
        found = el(name)
        parent.append(found)
    for key, val in attrs.items():
        found.set(W+key, str(val))
    return found


def replace_text(p, value, *, bold=None):
    """Keep paragraph, bookmark, section and first-run formatting intact."""
    old = p.find('.//'+W+'rPr')
    rp = deepcopy(old) if old is not None else el('rPr')
    # Empty template placeholders sometimes have no explicit font.
    prop(rp, 'rFonts', ascii='Times New Roman', hAnsi='Times New Roman', cs='Times New Roman')
    for tag in ['highlight', 'shd']:
        for node in rp.findall(W+tag): rp.remove(node)
    if bold is not None: prop(rp, 'b', val='1' if bold else '0')
    for node in list(p):
        if node.tag not in {W+'pPr', W+'bookmarkStart', W+'bookmarkEnd'}:
            p.remove(node)
    for index, line in enumerate(value.split('\n')):
        r = el('r'); r.append(deepcopy(rp))
        if index: r.append(el('br'))
        t=el('t'); t.set(XML+'space','preserve'); t.text=line; r.append(t); p.append(r)


def append_text(p, value):
    r=el('r')
    rp=p.find('.//'+W+'rPr')
    if rp is not None: r.append(deepcopy(rp))
    t=el('t');t.set(XML+'space','preserve');t.text=value;r.append(t);p.append(r)


def page_field(p, bookmark):
    for name,value in [('begin',None),(None,' PAGEREF '+bookmark+' \\h '),('separate',None),(None,'0'),('end',None)]:
        r=el('r'); rp=el('rPr')
        rp.append(el('rFonts',ascii='Times New Roman',hAnsi='Times New Roman'))
        rp.append(el('sz',val=24));r.append(rp)
        if name: r.append(el('fldChar',fldCharType=name))
        else:
            t=el('instrText' if value.startswith(' PAGEREF') else 't')
            t.set(XML+'space','preserve');t.text=value;r.append(t)
        p.append(r)


def nav_table(existing, headers, rows, widths):
    table=deepcopy(existing)
    sample=deepcopy(table.find(W+'tr').find(W+'tc').find(W+'p'))
    for node in list(table):
        if node.tag in {W+'tr',W+'tblGrid'}:table.remove(node)
    grid=el('tblGrid')
    for width in widths:grid.append(el('gridCol',w=width))
    table.insert(1,grid)
    prop(table.find(W+'tblPr'),'tblW',w=sum(widths),type='dxa')
    prop(table.find(W+'tblPr'),'tblLayout',type='fixed')
    for i,values in enumerate([headers]+rows):
        row=el('tr');rpr=el('trPr');rpr.append(el('cantSplit'))
        if i==0:rpr.append(el('tblHeader'))
        row.append(rpr)
        for j,value in enumerate(values):
            cell=el('tc');cp=el('tcPr');cp.append(el('tcW',w=widths[j],type='dxa'));cell.append(cp)
            p=deepcopy(sample);replace_text(p,'' if isinstance(value,tuple) else str(value),bold=(i==0 or (len(values)>1 and re.fullmatch(r'\d+\.',str(values[0])) is not None)))
            pp=p.find(W+'pPr')
            for node in pp.findall(W+'keepNext'):pp.remove(node)
            prop(pp,'jc',val='center' if j in {0,len(values)-1} else 'left')
            # Match the template's 12-point, 1.5-line contents typography.
            prop(pp,'spacing',before=0,after=0,line=360,lineRule='auto')
            if j==1 and isinstance(value,str) and re.match(r'\d+\.\d+\.\d+',value):
                prop(pp,'ind',left=360,right=0,firstLine=0,hanging=0)
            if isinstance(value,tuple):page_field(p,value[0])
            cell.append(p);row.append(cell)
        table.append(row)
    return table


# Publisher-verified author lists and bibliographic fields, keyed by OLD ID.
REFERENCES={
1: ('F. T. Liu, K. M. Ting and Z.-H. Zhou, “Isolation Forest,” Proceedings of the IEEE International Conference on Data Mining, 2008, pp. 413–422. doi:10.1109/ICDM.2008.17.', 'Proceedings of the IEEE International Conference on Data Mining'),
2: ('S. M. Lundberg and S.-I. Lee, “A Unified Approach to Interpreting Model Predictions,” Advances in Neural Information Processing Systems, vol. 30, 2017.', 'Advances in Neural Information Processing Systems'),
3: ('T. S. Sethi and M. M. Kantardzic, “On the Reliable Detection of Concept Drift from Streaming Unlabeled Data,” Expert Systems with Applications, vol. 82, pp. 77–99, 2017. doi:10.1016/j.eswa.2017.04.008.', 'Expert Systems with Applications'),
4: ('F. Maggi, W. Robertson, C. Kruegel and G. Vigna, “Protecting a Moving Target: Addressing Web Application Concept Drift,” Recent Advances in Intrusion Detection, LNCS, vol. 5758, pp. 21–40, 2009. doi:10.1007/978-3-642-04342-0_2.', 'Recent Advances in Intrusion Detection'),
5: ('Aditya Kuppa and Nhien-An Le-Khac, “Learn to Adapt: Robust Drift Detection in Security Domain,” Computers and Electrical Engineering, vol. 102, article 108239, 2022. doi:10.1016/j.compeleceng.2022.108239.', 'Computers and Electrical Engineering'),
6: ('Dongqi Han, Zhiliang Wang, Wenqi Chen, Kai Wang, Rui Yu, Su Wang, Han Zhang, Zhihua Wang, Minghui Jin, Jiahai Yang, Xingang Shi and Xia Yin, “Anomaly Detection in the Open World: Normality Shift Detection, Explanation, and Adaptation,” Network and Distributed System Security Symposium (NDSS), 2023. doi:10.14722/ndss.2023.24830.', 'Network and Distributed System Security Symposium (NDSS)'),
7: ('Jinpeng Li, Hang Yu, Zhenyu Zhang, Xiangfeng Luo and Shaorong Xie, “Concept Drift Adaptation by Exploiting Drift Type,” ACM Transactions on Knowledge Discovery from Data, vol. 18, no. 4, article 96, pp. 1–22, 2024. doi:10.1145/3638777.', 'ACM Transactions on Knowledge Discovery from Data'),
8: ('Yongsoo Lee, Yeeun Lee, Eungyu Lee and Taejin Lee, “Explainable Artificial Intelligence-Based Model Drift Detection Applicable to Unsupervised Environments,” Computers, Materials & Continua, vol. 76, no. 2, pp. 1701–1719, 2023. doi:10.32604/cmc.2023.040235.', 'Computers, Materials & Continua'),
9: ('Amazon Web Services, “Feature Attribution Drift for Models in Production,” Amazon SageMaker documentation. https://docs.aws.amazon.com/sagemaker/latest/dg/clarify-model-monitor-feature-attribution-drift.html. Accessed: 27 October 2026.', None),
10: ('Amazon Web Services, “Understanding CloudTrail Events,” AWS CloudTrail documentation. https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-events.html. Accessed: 27 October 2026.', None),
11: ('Surya Karthikeya Varma.I and Ramya K, “An Explainable Machine Learning and Large Language Model Framework for Anomaly Detection in AWS CloudTrail Logs,” 2025 International Conference on Intelligent Computing and Next Generation Networks (ICNGN), pp. 1–5, 2025. doi:10.1109/ICNGN67480.2025.11413642.', '2025 International Conference on Intelligent Computing and Next Generation Networks (ICNGN)'),
12: ('Shruti Arora, Rinkle Rani and Nitin Saxena, “A Systematic Review on Detection and Adaptation of Concept Drift in Streaming Data Using Machine Learning Techniques,” WIREs Data Mining and Knowledge Discovery, vol. 14, no. 4, article e1536, 2024. doi:10.1002/widm.1536.', 'WIREs Data Mining and Knowledge Discovery'),
13: ('PRISMA Statement, “PRISMA 2020 Statement and Checklist.” https://www.prisma-statement.org/. Accessed: 27 October 2026.', None),
14: ('ArielCyber, “Cloud Log Sampling,” public dataset and code repository. https://github.com/ArielCyber/cloud_log_sampling. Accessed: 27 October 2026.', None),
15: ('Scikit-learn developers, “IsolationForest,” scikit-learn API documentation. https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html. Accessed: 27 October 2026.', None),
16: ('SHAP developers, “shap.TreeExplainer,” SHAP API documentation. https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html. Accessed: 27 October 2026.', None),
}


def write_package(parts,path):
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        for name,data in parts.items():z.writestr(name,data)


def main():
    TMP.mkdir(parents=True,exist_ok=True)
    original_sha=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    with ZipFile(SOURCE) as z:parts={name:z.read(name) for name in z.namelist()}
    root=E.fromstring(parts['word/document.xml']);body=root.find(W+'body')
    baseline_nodes=list(body)
    # Fill only verified/user-supplied personal information.
    replace_text(body[18].findall('.//'+W+'tc')[1].find(W+'p'),'Associate Professor')
    # The original template reserves these paragraphs for the HoD and programme.
    replace_text(body[68],'Prof. J. Saira Banu, PhD',bold=True)
    replace_text(body[69],'Professor & Head (BCT & MIC), Department of IoT\nB.Tech. CSE (Specialization in IoT)',bold=False)
    for i in [68,69]:
        pp=body[i].find(W+'pPr');prop(pp,'jc',val='left');prop(pp,'ind',left=0,right=0,firstLine=0,hanging=0)
        prop(pp,'spacing',before=0,after=0,line=240,lineRule='auto')
        for rp in body[i].findall('.//'+W+'rPr'):prop(rp,'sz',val=24)
    dean=next(p for p in body if txt(p).startswith('My sincere thanks to Dr. Jaisankar'))
    replace_text(dean,'I thank Dr. Jaisankar N, Dean in-charge of the School of Computer Science and Engineering (SCOPE), for supporting the academic environment and resources available for this project.')
    # Use the existing acknowledgement paragraph pattern and avoid invented feedback.
    hod=deepcopy(dean)
    replace_text(hod,'I also thank Prof. J. Saira Banu, PhD, Professor & Head (BCT & MIC), Department of IoT, for the departmental support and academic facilities that enabled this capstone work.')
    dean.addnext(hod)
    acknowledgement_gap=deepcopy(dean.getprevious())
    assert not txt(acknowledgement_gap).strip()
    dean.addnext(acknowledgement_gap)
    # Remove a redundant closing sentence that otherwise creates a two-line page.
    project_plan_end=next(p for p in body if txt(p).startswith('The current Review–3 outcome'))
    replace_text(project_plan_end,'Review–3 delivers a working research prototype and a documented experimental package. Journal submission still requires stronger independent temporal recovery experiments and completion of literature screening.')
    # Add the four genuinely relevant missing citations, before renumbering.
    lit=next(p for p in body if txt(p).startswith('The literature was organised'))
    append_text(lit,' Arora, Rani and Saxena provide a broader review of drift detection and adaptation in streaming data [12].')
    heading=next(p for p in body if txt(p).startswith('5.3 Baseline Detector'))
    p=heading.getnext();append_text(p,' The estimator is implemented through scikit-learn’s IsolationForest API [15].')
    p=p.getnext();append_text(p,' TreeSHAP values are obtained through the SHAP TreeExplainer API [16].')
    heading=next(p for p in body if txt(p).startswith('7.6 Independent Detector'))
    p=heading.getnext()
    # The first item is a table caption; put the dataset citation in the first prose paragraph.
    while p is not None and (p.tag!=W+'p' or txt(p).startswith(('Table ','Figure ')) or not txt(p).strip()):p=p.getnext()
    append_text(p,' The independent corpus is distributed through the ArielCyber cloud_log_sampling repository [14].')
    # First-appearance order through Chapters 1–8, including table cells.
    start=next(i for i,p in enumerate(body) if txt(p)=='1 INTRODUCTION')
    stop=next(i for i,p in enumerate(body) if txt(p)=='9 REFERENCES')
    order=[]
    for node in list(body)[start:stop]:
        for match in re.finditer(r'\[(\d+)\]',txt(node)):
            ref=int(match.group(1))
            if ref in REFERENCES and ref not in order:order.append(ref)
    assert set(order)==set(REFERENCES),('Uncited references',set(REFERENCES)-set(order))
    mapping={old:i+1 for i,old in enumerate(order)}
    for node in list(body)[start:stop]:
        for t in node.findall('.//'+W+'t'):
            if t.text:t.text=re.sub(r'\[(\d+)\]',lambda m:'['+str(mapping.get(int(m.group(1)),int(m.group(1))))+']',t.text)
        for p in node.iter(W+'p'):
            if txt(p)=='AWS [9], [1]':replace_text(p,'AWS [1], [9]')
    refs=[p for p in body if re.match(r'^\[\d+\]',txt(p))]
    assert len(refs)==16
    for p,old in zip(refs,order):
        value,italic=REFERENCES[old];replace_text(p,f'[{mapping[old]}] '+value,bold=False)
        pp=p.find(W+'pPr');prop(pp,'jc',val='left');prop(pp,'ind',left=480,hanging=480,right=0)
        prop(pp,'keepLines')
        # Split only the venue text into a true italic run.
        if italic:
            r=p.find(W+'r');rp=deepcopy(r.find(W+'rPr'));before,after=txt(p).split(italic,1)
            p.remove(r)
            for value,is_italic in [(before,False),(italic,True),(after,False)]:
                r=el('r');pr=deepcopy(rp);prop(pr,'i',val='1' if is_italic else '0');r.append(pr)
                t=el('t');t.set(XML+'space','preserve');t.text=value;r.append(t);p.append(r)
    # Rebuild all three template navigation tables with live PAGEREF fields.
    old_nav=[baseline_nodes[i] for i in [92,95,98]]
    toc=[];figures=[];tables=[]
    for p in body:
        mark=p.find(W+'bookmarkStart')
        if mark is None:continue
        title=txt(p);target=(mark.get(W+'name'),)
        levels=p.xpath('./w:pPr/w:outlineLvl/@w:val',namespaces=NS)
        if title=='ABSTRACT':toc.append(['','ABSTRACT',target])
        elif levels and int(levels[0]) in {1,2,3}:
            match=re.match(r'^(\d+) (.+)$',title)
            toc.append([match.group(1)+'.' if match else '',match.group(2) if match else title,target])
        elif title.startswith('Figure '):
            number,caption=title[7:].split(' ',1);figures.append([number,caption,target])
        elif title.startswith('Table '):
            number,caption=title[6:].split(' ',1);tables.append([number,caption,target])
    for existing,headers,rows,widths in [
        (old_nav[0],['Sl.No','Contents','Page No.'],toc,[950,6750,1200]),
        (old_nav[1],['Figure No.','Title','Page No.'],figures,[1300,6400,1200]),
        (old_nav[2],['Table No.','Title','Page No.'],tables,[1300,6400,1200]),
    ]:body.replace(existing,nav_table(existing,headers,rows,widths))
    # Keep existing table borders/typography; repeat headers and keep rows intact.
    for table in body.findall(W+'tbl')[5:]:
        for index,row in enumerate(table.findall(W+'tr')):
            rp=row.find(W+'trPr')
            if rp is None:rp=el('trPr');row.insert(0,rp)
            prop(rp,'cantSplit')
            if index==0:prop(rp,'tblHeader')
    appendix_heading=next(p for p in body if txt(p)=='A.3 Protected Retraining')
    prop(appendix_heading.find(W+'pPr'),'keepNext')
    prop(appendix_heading.getnext().find(W+'pPr'),'keepLines')
    # Preserve the template's existing section geometry and all opaque package parts.
    before_geometry=[E.tostring(e) for e in E.fromstring(parts['word/document.xml']).findall('.//'+W+'sectPr')]
    assert before_geometry==[E.tostring(e) for e in root.findall('.//'+W+'sectPr')]
    parts['word/document.xml']=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
    write_package(parts,OUT)
    write_package(parts,TMP/'before_word_refresh.docx')
    audit={'source_sha256':original_sha,'citation_old_to_new':mapping,'contents_entries':len(toc),'figures':len(figures),'tables':len(tables),'preserved_package_parts':[p for p in parts if p!='word/document.xml'],'source':str(SOURCE),'output':str(OUT)}
    (TMP/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==original_sha
    print(json.dumps({k:v for k,v in audit.items() if k!='preserved_package_parts'},indent=2))


def restore_field_caches(refreshed_path):
    """Retain Word's calculated values, not its unrelated formatting rewrites."""
    with ZipFile(refreshed_path) as z: refreshed=E.fromstring(z.read('word/document.xml'))
    cache={}
    for p in refreshed.findall('.//'+W+'p'):
        active=None;collect=False;values=[]
        for r in p.findall(W+'r'):
            instruction=''.join(r.xpath('./w:instrText/text()',namespaces=NS))
            match=re.search(r'PAGEREF\s+(capstone_\d+)',instruction)
            if match:active=match.group(1);values=[]
            field=r.find(W+'fldChar')
            if field is not None:
                kind=field.get(W+'fldCharType')
                if kind=='separate' and active:collect=True
                elif kind=='end' and active:
                    cache[active]=''.join(values);collect=False;active=None
            elif collect:values.extend(r.xpath('.//w:t/text()',namespaces=NS))
    with ZipFile(TMP/'before_word_refresh.docx') as z:parts={p:z.read(p) for p in z.namelist()}
    root=E.fromstring(parts['word/document.xml']);count=0
    for instruction in root.findall('.//'+W+'instrText'):
        match=re.search(r'PAGEREF\s+(capstone_\d+)',instruction.text or '')
        if not match:continue
        name=match.group(1)
        assert name in cache and cache[name] and 'Error' not in cache[name],(name,cache.get(name))
        instruction.getparent().getnext().getnext().find(W+'t').text=cache[name];count+=1
    parts['word/document.xml']=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
    write_package(parts,OUT)
    audit=json.loads((TMP/'audit.json').read_text())
    with ZipFile(SOURCE) as original:
        assert all(parts[name]==original.read(name) for name in parts if name!='word/document.xml')
    audit.update({'refreshed_page_fields':count,'page_cache':cache,'output_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'preserve_only_parts_unchanged':True})
    (TMP/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    print('Restored',count,'Word-calculated page references; all other package parts preserved.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--restore-caches',type=Path);args=parser.parse_args()
    if args.restore_caches:restore_field_caches(args.restore_caches)
    else:main()
