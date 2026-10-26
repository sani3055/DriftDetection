"""Render report pages and summarize print-layout evidence for internal QA."""
from pathlib import Path
import json
import sys
import pymupdf as fitz
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
TMP = ROOT / "tmp/capstone_report"
pdf = fitz.open(TMP / "expanded-final.pdf")
dest = TMP / "pages"
dest.mkdir(exist_ok=True)
evidence = []
for i, page in enumerate(pdf):
    pix = page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2), alpha=False)
    pix.save(dest / f"page-{i+1:02}.png")
    txt = page.get_text()
    blocks = [b for b in page.get_text("blocks") if b[6] == 0 and b[4].strip()]
    evidence.append({"page": i+1, "words": len(txt.split()), "first": txt[:125].replace("\n", " / "), "last": txt[-90:].replace("\n", " / "), "rightmost": max((b[2] for b in blocks), default=0), "bottommost": max((b[3] for b in blocks), default=0)})
for start in range(0, len(pdf), 6):
    montage = Image.new("RGB", (1420, 3060), "#cccccc")
    draw = ImageDraw.Draw(montage)
    for j in range(6):
        i = start + j
        if i >= len(pdf):
            break
        with Image.open(dest / f"page-{i+1:02}.png") as im:
            im.thumbnail((700, 990))
            x = (j % 2) * 710
            y = (j // 2) * 1020
            montage.paste(im, (x, y+25))
            draw.text((x+10, y+5), f"Page {i+1}", fill="black")
    montage.save(TMP / f"review-{start+1:02}-{min(start+6,len(pdf)):02}.png")
(TMP / "page-evidence.json").write_text(json.dumps(evidence, indent=2))
print("Pages", len(pdf), "PDF words", sum(x["words"] for x in evidence))
for row in evidence:
    print(row)
text = "\n".join(p.get_text() for p in pdf)
print("Errors", {bad:text.count(bad) for bad in ["Error!", "Reference source not found", "<<", "<Contents", "2024-2025"]})
