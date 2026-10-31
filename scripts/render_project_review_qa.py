"""Rasterise already-rendered document PDFs and check extractable content."""
import json
from pathlib import Path
import re
import pypdfium2 as pdfium
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/review_qa'
reports={}
for name, filename in [('manuscript','review_final.pdf'),('consolidated','summaries_final.pdf')]:
    folder=OUT/name
    pdf=pdfium.PdfDocument(str(folder/filename))
    pages=[]
    for i,page in enumerate(pdf):
        text=page.get_textpage().get_text_range()
        pages.append(text)
        page.render(scale=1.4).to_pil().save(folder/f'page-{i+1:03d}.png')
    alltext='\n'.join(pages)
    report={'pages':len(pdf),'words':len(alltext.split()),
        'empty_pages':[i+1 for i,t in enumerate(pages) if len(t.strip())<45],
        'unresolved_source_markers':bool(re.search(r'\[@|\bturn\d+(?:search|view)',alltext))}
    if name=='consolidated':
        report['study_headings']=len(re.findall(r'Study R\d{3}',alltext))
        report['per_page_studies']=[len(re.findall(r'Study R\d{3}',t)) for t in pages]
    reports[name]=report
    # Four-page sheets retain the original raster dimensions of every page.
    # These are QA artifacts, never manuscript illustrations.
    for start in range(0,len(pdf),4):
        images=[Image.open(folder/f'page-{i+1:03d}.png').convert('RGB')
                for i in range(start,min(start+4,len(pdf)))]
        w,h=images[0].size
        canvas=Image.new('RGB',(2*w+24,2*(h+26)+12),'#d7d7d7')
        draw=ImageDraw.Draw(canvas)
        for j,im in enumerate(images):
            x=(j%2)*(w+12);y=(j//2)*(h+26)
            draw.text((x+8,y+5),f'{name} page {start+j+1}',fill='black')
            canvas.paste(im,(x,y+22))
        canvas.save(folder/f'qa-sheet-{start//4+1:02d}.png')
(OUT/'render_validation.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
print(json.dumps(reports,indent=2))
