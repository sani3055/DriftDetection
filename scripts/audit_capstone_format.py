"""Verify report table visibility and preservation of the supplied template."""
from pathlib import Path
from zipfile import ZipFile
import json
from lxml import etree as ET

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = Path(r"D:\Downloads\BCSE497J Project I Report - Template FINAlL Updated  (2).docx")
REPORT = ROOT / "outputs/BCSE497J_Capstone_Report_Final.docx"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def signature(node):
    return [(n.tag, sorted(n.attrib.items())) for n in node.iter()]


def main():
    with ZipFile(TEMPLATE) as original, ZipFile(REPORT) as report:
        changed = [name for name in original.namelist() if original.read(name) != report.read(name)]
        assert set(changed) == {"word/document.xml", "word/_rels/document.xml.rels", "[Content_Types].xml"}, changed
        source_root = ET.fromstring(original.read("word/document.xml"))
        report_root = ET.fromstring(report.read("word/document.xml"))
        assert [signature(s) for s in source_root.findall(".//" + W + "sectPr")] == [signature(s) for s in report_root.findall(".//" + W + "sectPr")]
        tables = report_root.findall(".//" + W + "tbl")
        bordered = []
        for table in tables:
            borders = table.find(W + "tblPr/" + W + "tblBorders")
            if borders is not None and sum(n.get(W + "val") == "single" for n in borders) == 6:
                bordered.append(table)
        assert len(bordered) == 17, len(bordered)
        for table in bordered:
            assert table.find(W + "tr/" + W + "trPr/" + W + "tblHeader") is not None
            for run in table.findall(".//" + W + "r"):
                assert run.find(W + "rPr/" + W + "sz").get(W + "val") == "24"
                assert run.find(W + "rPr/" + W + "rFonts").get(W + "ascii") == "Times New Roman"
    evidence = json.loads((ROOT / "tmp/capstone_report/page-evidence.json").read_text(encoding="utf-8"))
    assert all(p["words"] > 2 for p in evidence), "Unexpected blank page"
    result = {
        "data_tables_with_printable_borders": len(bordered),
        "data_table_font": "Times New Roman 12 pt",
        "section_geometry_identical": True,
        "styles_theme_numbering_headers_footers_and_logo_identical": True,
        "rendered_pages": len(evidence),
        "blank_pages": 0,
        "intentional_table_changes": "Printable black borders, cell padding and content-appropriate column widths; header plus two initial data rows kept together",
    }
    (ROOT / "tmp/capstone_report/final-format-audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
