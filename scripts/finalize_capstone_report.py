"""Copy only Word-computed PAGEREF display values into the untouched-style package.

Word's save rewrites unrelated style and header parts. Keeping only the field
cache values preserves the original template's package parts byte-for-byte.
"""
from __future__ import annotations

import json
import hashlib
import re
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from lxml import etree as ET

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / "tmp/capstone_report"
OUT = ROOT / "outputs/BCSE497J_Capstone_Report_Expanded.docx"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NS = {"w": W[1:-1]}


def main():
    with ZipFile(OUT) as z:
        refreshed = ET.fromstring(z.read("word/document.xml"))
    cache = {}
    for paragraph in refreshed.findall(".//" + W + "p"):
        runs = list(paragraph.iter(W + "r"))
        active = None
        collecting = False
        result = []
        for run in runs:
            instruction = "".join(run.xpath("./w:instrText/text()", namespaces=NS))
            match = re.search(r"PAGEREF\s+(capstone_\d+)", instruction)
            if match:
                active = match.group(1)
                result = []
            fld = run.find(W + "fldChar")
            if fld is not None:
                kind = fld.get(W + "fldCharType")
                if kind == "separate" and active:
                    collecting = True
                elif kind == "end" and active:
                    cache[active] = "".join(result)
                    collecting = False
                    active = None
            elif collecting:
                result.extend(run.xpath(".//w:t/text()", namespaces=NS))
    with ZipFile(TMP / "before_word_refresh.docx") as z:
        parts = {name: z.read(name) for name in z.namelist()}
    original = ET.fromstring(parts["word/document.xml"])
    count = 0
    for instruction in original.findall(".//" + W + "instrText"):
        match = re.search(r"PAGEREF\s+(capstone_\d+)", instruction.text or "")
        if not match:
            continue
        name = match.group(1)
        assert name in cache and cache[name] and "Error" not in cache[name], (name, cache.get(name))
        run = instruction.getparent()
        result = run.getnext().getnext().find(W + "t")
        assert result is not None
        result.text = cache[name]
        count += 1
    parts["word/document.xml"] = ET.tostring(original, encoding="UTF-8", xml_declaration=True, standalone=True)
    with ZipFile(OUT, "w", ZIP_DEFLATED) as z:
        for name, data in parts.items():
            z.writestr(name, data)
    audit = json.loads((TMP / "fidelity.json").read_text())
    audit["page_reference_fields_refreshed"] = count
    audit["output_sha256"] = hashlib.sha256(OUT.read_bytes()).hexdigest()
    audit["preserve_only_parts_after_word_refresh"] = "restored byte-for-byte; only computed field display values retained"
    (TMP / "fidelity.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print("Refreshed", count, "page references while preserving original template package styles.")


if __name__ == "__main__":
    main()
