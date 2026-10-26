"""Expand the capstone report while preserving the supplied DOCX package styles.

Only the main document, new drawing relationships and added PNG parts are edited.
The original sections, styles, theme, numbering, headers, footers and VIT logo are
retained. Run with the bundled document-authoring Python runtime.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import re
import zipfile
from pathlib import Path

from lxml import etree as ET
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / "tmp/capstone_report"
TMP.mkdir(parents=True, exist_ok=True)
TEMPLATE = Path(r"D:\Downloads\BCSE497J Project I Report - Template FINAlL Updated  (2).docx")
OUTPUT = ROOT / "outputs/BCSE497J_Capstone_Report_Final.docx"
CONTENT = ROOT / "docs/capstone_report_content.md"
TITLE = "SHAP-GUIDED DRIFT DIAGNOSIS FOR ADAPTIVE ANOMALY DETECTION IN AWS CLOUDTRAIL"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main", "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
W = "{" + NS["w"] + "}"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
XML = "{http://www.w3.org/XML/1998/namespace}"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"


def el(tag, **attrs):
    out = ET.Element(W + tag)
    for k, v in attrs.items():
        out.set(W + k, str(v))
    return out


def text_of(node):
    return "".join(node.itertext()) if node is not None else ""


def visible(node):
    return "".join(node.xpath(".//w:t/text()", namespaces=NS))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def replace_text(p, text):
    """Replace editable content while retaining its paragraph and first run properties."""
    ppr = p.find(W + "pPr")
    first = p.find(W + "r")
    rpr = copy.deepcopy(first.find(W + "rPr")) if first is not None and first.find(W + "rPr") is not None else None
    for child in list(p):
        if child is not ppr:
            p.remove(child)
    r = el("r")
    if rpr is not None:
        r.append(rpr)
    for i, line in enumerate(text.split("\n")):
        if i:
            r.append(el("br"))
        t = el("t")
        t.set(XML + "space", "preserve")
        t.text = line
        r.append(t)
    p.append(r)
    # Yellow marks are authoring instructions in editable slots, not decoration.
    for h in p.xpath(".//w:highlight", namespaces=NS):
        h.getparent().remove(h)
    return p


def font(size):
    # This is the source template's Normal font, not a replacement style scheme.
    rpr = el("rPr")
    rpr.append(el("rFonts", ascii="Times New Roman", hAnsi="Times New Roman", eastAsia="Times New Roman", cs="Times New Roman"))
    rpr.append(el("sz", val=int(size * 2)))
    rpr.append(el("szCs", val=int(size * 2)))
    return rpr


def set_prop(ppr, name, **attrs):
    for old in list(ppr.findall(W + name)):
        ppr.remove(old)
    ppr.append(el(name, **attrs))


def add_bookmark(p, name, ident):
    start = el("bookmarkStart", id=ident, name=name)
    end = el("bookmarkEnd", id=ident)
    p.insert(1 if p.find(W + "pPr") is not None else 0, start)
    p.append(end)


def page_field(p, name):
    for code, value in [("begin", None), (None, f" PAGEREF {name} \\h "), ("separate", None), (None, "0"), ("end", None)]:
        r = el("r")
        r.append(font(12))
        if code:
            r.append(el("fldChar", fldCharType=code))
        else:
            node = el("instrText" if value.startswith(" PAGEREF") else "t")
            node.set(XML + "space", "preserve")
            node.text = value
            r.append(node)
        p.append(r)


def save_diagram(name, kind):
    """Original monochrome engineering diagrams, sized for an A4 report column."""
    width = 1800
    heights = {"architecture": 1060, "dataflow": 1050, "usecase": 900, "components": 1020, "sequence": 1230}
    image = Image.new("RGB", (width, heights[kind]), "white")
    draw = ImageDraw.Draw(image)
    regular = ImageFont.truetype(r"C:\Windows\Fonts\times.ttf", 31)
    bold = ImageFont.truetype(r"C:\Windows\Fonts\timesbd.ttf", 33)
    small = ImageFont.truetype(r"C:\Windows\Fonts\times.ttf", 27)

    def box(rect, title, lines=()):
        draw.rectangle(rect, outline="black", width=3)
        x1, y1, x2, y2 = rect
        all_lines = [title] + list(lines)
        y = (y1 + y2) / 2 - len(all_lines) * 22
        for j, line in enumerate(all_lines):
            f = bold if j == 0 else regular
            draw.text(((x1 + x2) / 2, y), line, font=f, fill="black", anchor="mt")
            y += 46

    def arrow(start, end, label=None):
        import math
        draw.line([start, end], fill="black", width=3)
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        points = [end, (end[0] - 19 * math.cos(angle - .45), end[1] - 19 * math.sin(angle - .45)), (end[0] - 19 * math.cos(angle + .45), end[1] - 19 * math.sin(angle + .45))]
        draw.polygon(points, fill="black")
        if label:
            draw.text(((start[0] + end[0]) / 2 + 10, (start[1] + end[1]) / 2 - 35), label, font=small, fill="black", anchor="mm")

    if kind == "architecture":
        boxes = [(100, 50, 780, 185), (1020, 50, 1700, 185), (100, 305, 780, 440), (1020, 305, 1700, 440), (100, 560, 780, 695), (1020, 560, 1700, 695), (100, 815, 780, 950), (1020, 815, 1700, 950)]
        labels = [("Source audit", ["Read-only CSV and provenance"]), ("Temporal preparation", ["Monthly reference and train-only maps"]), ("Isolation Forest", ["Stable seven-feature input contract"]), ("TreeSHAP", ["Attribution and additivity validation"]), ("Drift monitoring", ["Feature PSI and SHAP distributions"]), ("Coupled diagnosis", ["Magnitude gates and feature alignment"]), ("Protected adaptation", ["Replay plus baseline-normal candidates"]), ("Evaluation and reporting", ["Paired metrics and saved artifacts"])]
        for rect, (title, lines) in zip(boxes, labels): box(rect, title, lines)
        arrow((780, 115), (1020, 115)); arrow((1360, 185), (1360, 250)); arrow((1360, 250), (440, 250)); arrow((440, 250), (440, 305))
        arrow((780, 372), (1020, 372)); arrow((1360, 440), (1360, 505)); arrow((1360, 505), (440, 505)); arrow((440, 505), (440, 560))
        arrow((780, 625), (1020, 625)); arrow((1360, 695), (1360, 760)); arrow((1360, 760), (440, 760)); arrow((440, 760), (440, 815)); arrow((780, 882), (1020, 882))
    elif kind == "dataflow":
        box((100, 70, 750, 220), "Reference sample", ["Training-derived event matrix"])
        box((1050, 70, 1700, 220), "Scenario generator", ["Scenario and seed controls"])
        arrow((750, 145), (1050, 145))
        box((1050, 355, 1700, 510), "Current feature matrix", ["No labels sent to detector"])
        arrow((1375, 220), (1375, 355))
        box((100, 355, 750, 510), "Detector and explainer", ["Scores and SHAP evidence"])
        arrow((1050, 432), (750, 432))
        box((100, 660, 750, 815), "Diagnosis and controller", ["Drift state and selected model"])
        arrow((425, 510), (425, 660))
        box((1050, 660, 1700, 815), "Evaluation only", ["Changed-row mask and labels"])
        arrow((1700, 145), (1760, 145)); arrow((1760, 145), (1760, 735)); arrow((1760, 735), (1700, 735))
        arrow((750, 738), (1050, 738), "Predictions")
        draw.text((900, 940), "Labels enter only after predictions are produced", font=bold, fill="black", anchor="mm")
    elif kind == "usecase":
        draw.ellipse((90, 315, 160, 385), outline="black", width=4); draw.line((125, 385, 125, 515), fill="black", width=4)
        draw.line((55, 420, 195, 420), fill="black", width=4); draw.line((125, 515, 60, 600), fill="black", width=4); draw.line((125, 515, 190, 600), fill="black", width=4)
        draw.text((125, 640), "Researcher", font=bold, fill="black", anchor="mt")
        draw.rectangle((460, 45, 1700, 850), outline="black", width=3)
        draw.text((1080, 70), "Local CloudTrail research prototype", font=bold, fill="black", anchor="mt")
        for j, label in enumerate(["Audit source and temporal split", "Inspect scores and explanations", "Review drift and coupling", "Compare adaptation policies", "Reproduce and explain results"]):
            y = 195 + j * 130
            draw.ellipse((650, y - 40, 1510, y + 55), outline="black", width=3)
            draw.text((1080, y + 5), label, font=regular, fill="black", anchor="mm")
            draw.line((195, 440, 650, y + 8), fill="black", width=2)
    elif kind == "components":
        specs = [("features/event_features.py", ["Category maps", "Encoded event matrix"]), ("explain/shap_explainer.py", ["TreeSHAP values", "Additivity checks"]), ("drift/drift_monitor.py", ["PSI and SHAP distributions", "Feature-attribution alignment"]), ("drift/diagnosis.py", ["Validation thresholds", "Diagnostic state"]), ("adaptation/controller.py", ["Policy trigger", "Filtered replay refit"]), ("evaluation/metrics.py", ["Detection metrics", "Paired result artifacts"])]
        for j, (title, lines) in enumerate(specs):
            col = j % 2; row = j // 2
            box((80 + col * 930, 70 + row * 315, 790 + col * 930, 280 + row * 315), title, lines)
        for row in range(3): arrow((790, 175 + row * 315), (1010, 175 + row * 315))
        arrow((435, 280), (435, 385)); arrow((1365, 280), (1365, 385)); arrow((435, 595), (435, 700)); arrow((1365, 595), (1365, 700))
    else:
        xs = [170, 530, 890, 1250, 1610]
        names = ["Runner", "Detector", "Explainer", "Diagnosis", "Controller"]
        for x, title in zip(xs, names):
            box((x - 150, 30, x + 150, 125), title)
            draw.line((x, 125, x, 1150), fill="#666666", width=2)
        steps = [(0, 1, "Score current matrix"), (1, 0, "Anomaly predictions"), (0, 2, "Explain reference and current"), (2, 0, "SHAP distributions"), (0, 3, "Feature / SHAP drift and coupling"), (3, 0, "Diagnostic state"), (0, 4, "Apply selected policy"), (4, 1, "Optional protected refit"), (1, 0, "Selected-model predictions")]
        for j, (left, right, label) in enumerate(steps):
            y = 220 + 103 * j
            arrow((xs[left], y), (xs[right], y))
            draw.text(((xs[left] + xs[right]) / 2, y - 18), label, font=small, fill="black", anchor="mb")
    path = TMP / f"{name}.png"
    image.save(path)
    return path


TABLES = {
    "literature": ("2.1 Selected literature and relation to the project", ["Source", "Established contribution", "Use and remaining question"], [
        ["Liu et al. [1]", "Isolation Forest", "Unsupervised baseline; does not diagnose drift."],
        ["Lundberg and Lee [2]", "Additive feature attribution", "Explains model output; does not establish attack causality."],
        ["Sethi and Kantardzic [3]", "Unlabelled drift detection", "Motivates distinguishing distribution change from model relevance."],
        ["Kuppa and Le-Khac [5]", "Security drift adaptation", "Motivates cautious updates under security-related change."],
        ["Han et al. [6]", "Normality shift and adaptation", "Prior integrated security work; limits broad novelty claims."],
        ["Li et al. [7]", "Drift-type adaptation", "Supports diagnosis before selection of an update action."],
        ["Lee et al. [8]", "Explanation-based drift", "Closest explanation-monitoring direction; needs CloudTrail-specific evaluation."],
        ["AWS [9], [10]", "Attribution monitoring and audit schema", "Operational definitions; not independent research validation."],
        ["Varma and Ramya [11]", "CloudTrail anomaly explanations", "Application context; does not establish the coupling gate's value."],
    ]),
    "phases": ("2.2 Capstone implementation phases", ["Phase", "Deliverable", "Status"], [
        ["Audit and framing", "Manifest, source limitations and verified literature matrix", "Implemented; separate PRISMA screening remains open"],
        ["Temporal baseline", "Chronological split, feature encoding and model artifact", "Implemented"],
        ["Explanations and drift", "SHAP validation, feature and attribution signals", "Implemented"],
        ["Coupled diagnosis", "Alignment scores, thresholds and diagnostic states", "Implemented and evaluated"],
        ["Adaptation and inference", "Protected refit, paired comparison and sensitivity", "Completed for controlled protocol"],
        ["Independent checks", "External detectors and temporal checkpoint", "Completed within stated limits"],
        ["Final review", "Report, reproducible evidence and live demonstration path", "Prepared for Review–3"],
    ]),
    "functional": ("3.1 Functional requirements", ["ID", "Requirement", "Implementation output"], [
        ["FR1", "Audit the read-only source", "Manifest and SHA-256"], ["FR2", "Preserve temporal ordering", "27 / 9 / 9 partition"],
        ["FR3", "Fit training-only category maps", "Stable seven-column matrix"], ["FR4", "Fit and score the baseline", "Persisted model and score sample"],
        ["FR5", "Compute and verify SHAP", "Attributions and residual check"], ["FR6", "Measure drift and coupling", "Per-feature and window summaries"],
        ["FR7", "Tune on validation scenarios", "Frozen source thresholds"], ["FR8", "Compare update policies", "Triggers, candidates and metrics"],
        ["FR9", "Run independent validation", "External manifest and results"], ["FR10", "Support reproducible review", "Scripts, tests, tables and figures"],
    ]),
    "nonfunctional": ("3.2 Non functional requirements", ["Property", "Design provision"], [
        ["Reproducibility", "Fixed seeds, declared dependencies, persistent artifacts"], ["Temporal integrity", "Training-only maps and ordered calendar split"],
        ["Label separation", "Controlled labels retained for evaluation only"], ["Interpretability", "Per-feature drift and attribution values"],
        ["Source integrity", "Read-only input and provenance checksum"], ["Bounded computation", "Chunked CSV processing and configured samples"],
        ["Auditability", "Scenario/seed identifiers and negative results retained"],
    ]),
    "configuration": ("3.3 Main experimental configuration", ["Setting", "Configured value"], [
        ["Declared Python", "3.11"], ["Primary detector", "Isolation Forest, 100 estimators, contamination 0.05, seed 42"],
        ["CSV chunk size", "100,000 rows"], ["Score sample limit", "1,000 events per window"], ["Controlled sample", "200 rows; main perturbation intensity 0.25"],
        ["Validation / test seeds", "0–4 / 5–14"], ["Adapted detector", "50 estimators, contamination 0.05"],
        ["Update safeguards", "Replay plus baseline-normal candidates; minimum 10 candidates"], ["Periodic interval", "Every third ordered scenario run"],
    ]),
    "features": ("3.4 Detector feature contract", ["Feature", "Meaning and transformation"], [
        ["eventName", "API operation; training-only categorical code"], ["eventSource", "AWS service domain; categorical code"],
        ["awsRegion", "Event region; categorical code"], ["userIdentitytype", "Identity class; categorical code"],
        ["errorCode", "Reported error category; categorical code"], ["requestParametersinstanceType", "Instance-type value where present; categorical code"],
        ["isRoot", "Derived binary flag for userIdentitytype equal to Root"],
    ]),
    "diagnosis": ("4.1 Coupled diagnostic interpretation", ["Feature / SHAP gates", "Alignment", "State"], [
        ["Low / Low", "Any", "stable"], ["High / Low", "Any", "benign_drift"], ["High / High", "High", "security_relevant_drift"],
        ["High / High", "Low", "review_required"], ["Low / High", "Low", "hidden_model_instability"], ["Low / High", "High", "review_required"],
    ]),
    "dataset": ("5.1 Audited primary corpus", ["Property", "Verified value"], [
        ["Records / source columns", "1,939,207 / 18"], ["Observed time span", "February 2017 to October 2020"], ["Windows", "45 monthly windows"],
        ["Attack labels", "Unavailable"], ["Malformed rows observed", "0"], ["File size", "830,904,812 bytes"],
        ["Chronological partition", "27 training, 9 validation and 9 test months"], ["Largest month", "2019-08: 1,347,680 rows (approximately 69.5%)"],
    ]),
    "scenarios": ("5.2 Controlled perturbation definitions", ["Scenario", "Main intervention"], [
        ["stable", "Unmodified reference copy"], ["benign_region", "Set selected awsRegion codes to ap-southeast-1"],
        ["benign_identity", "Set selected identity-type codes to AWSService"], ["benign_service", "Set selected service codes to lambda.amazonaws.com"],
        ["security_privilege", "AttachUserPolicy API; Root identity on another subset"], ["security_defense", "DeleteTrail API; CloudTrail service on another subset"],
        ["security_credential", "AssumeRole API; region change on another subset"],
    ]),
    "tests": ("5.3 Automated test coverage and requirement traceability", ["Test area", "Purpose", "Requirement"], [
        ["Dataset audit", "Check schema and manifest behaviour", "FR1"], ["Temporal protocol", "Check split order and separation", "FR2"],
        ["Event features", "Check mappings, unknowns and feature order", "FR3"], ["Detector", "Check fitted model and predictions", "FR4"],
        ["SHAP explainer", "Check additive reconstruction", "FR5"], ["Drift monitor", "Check distribution metrics and alignment", "FR6"],
        ["Diagnosis", "Check state rules and threshold helpers", "FR7"], ["Adaptation", "Check triggers and filtered retraining", "FR8"],
        ["Inference and integration", "Check paired outputs and artifact consistency", "FR10"],
    ]),
    "demo": ("6.1 Live demonstration sequence", ["Step", "Action", "Evidence to inspect"], [
        ["1", "Confirm input and split", "Manifest, source checksum and temporal_split.json"], ["2", "Inspect detector contract", "Saved feature order and model configuration"],
        ["3", "Show explanation validation", "SHAP sample and additivity residual"], ["4", "Inspect real drift", "Monthly timeline and per-feature PSI"],
        ["5", "Compare two scenarios", "Diagnostic scores, states and seed identifiers"], ["6", "Inspect adaptation", "Trigger, candidate count and resulting metrics"],
        ["7", "Show independent transfer", "Source-coupling failure and target calibration"], ["8", "Verify implementation", "Automated tests and artifact provenance"],
    ]),
    "artifacts": ("A.1 Key implementation artifacts", ["Artifact", "Role"], [
        ["data_manifest/real_cloudtrail_manifest.json", "Source identity and audit"], ["data/processed/temporal_split.json", "Chronological membership"],
        ["models/isolation_forest_event_baseline.joblib", "Estimator and feature contract"], ["data/drift/combined_drift.csv", "Joint real-window monitoring outputs"],
        ["data/benchmark/diagnosis_thresholds.json", "Validation-selected source thresholds"], ["data/benchmark/adaptation_results.csv", "Policy/scenario/seed outcomes"],
        ["results/paired_inference.csv", "Effect sizes and uncertainty"], ["data/external_validation/", "Independent manifests and metrics"],
    ]),
}


def data_tables():
    import csv
    def read(path):
        with (ROOT / path).open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    fmt = lambda v: f"{float(v):.4f}"
    adaptation = read("data/benchmark/adaptation_summary.csv")
    TABLES["adaptation"] = ("7.1 Held-out controlled adaptation policies", ["Policy", "Trigger", "Unnecessary", "Mean F1", "FPR"], [
        [r["policy"].replace("_signal", "").replace("_", " "), fmt(r["trigger_rate"]), fmt(r["unnecessary_adaptation_rate"]), fmt(r["mean_f1"]), fmt(r["mean_false_positive_rate"])] for r in adaptation
    ])
    TABLES["paired"] = ("7.2 Paired dual minus static differences", ["Metric", "Mean difference", "95% bootstrap interval", "BH adjusted q"], [
        [r["metric"].replace("_", " "), f"{float(r['mean_difference']):.6f}", f"[{float(r['ci_low']):.6f}, {float(r['ci_high']):.6f}]", f"{float(r['q_value_bh']):.6f}"] for r in read("results/paired_inference.csv") if r["metric"] in {"f1", "false_positive_rate"}
    ])
    TABLES["robustness"] = ("7.3 Controlled detector robustness protocol", ["Detector", "Security recall", "Security F1", "Benign FPR"], [
        [r["detector"].replace("_", " "), fmt(r["security_recall"]), fmt(r["security_f1"]), fmt(r["benign_false_positive_rate"])] for r in read("data/robustness/detector_ablation_summary.csv")
    ])
    TABLES["externaldetectors"] = ("7.4 Independent labelled detector evaluation", ["Detector", "Precision", "Recall", "F1", "FPR"], [
        [r["detector"].replace("_", " "), fmt(r["precision"]), fmt(r["recall"]), fmt(r["f1"]), fmt(r["false_positive_rate"])] for r in read("data/external_validation/external_detector_metrics.csv")
    ])
    external = json.loads((ROOT / "data/external_validation/external_temporal_diagnosis_metrics.json").read_text())
    TABLES["externaldiagnosis"] = ("7.5 External 12-window diagnosis checkpoint", ["Policy", "Precision", "Recall", "F1", "FPR"], [
        [k.replace("_signal", "").replace("_", " "), fmt(v["precision"]), fmt(v["recall"]), fmt(v["f1"]), fmt(v["false_positive_rate"])] for k, v in external.items()
    ])


def build():
    source_bytes = TEMPLATE.read_bytes()
    with zipfile.ZipFile(TEMPLATE) as z:
        parts = {n: z.read(n) for n in z.namelist()}
    root = ET.fromstring(parts["word/document.xml"])
    body = root.find(W + "body")
    ps = body.findall(W + "p")
    original_sections = [copy.deepcopy(x) for x in root.findall(".//" + W + "sectPr")]
    body_pattern = copy.deepcopy(ps[237])
    chapter_pattern = copy.deepcopy(ps[226])
    heading_pattern = copy.deepcopy(ps[227])
    toc_pattern = copy.deepcopy(body.findall(W + "tbl")[2])
    rels = ET.fromstring(parts["word/_rels/document.xml.rels"])
    types = ET.fromstring(parts["[Content_Types].xml"])
    new_media = {}
    bookmark_id = 7000
    image_id = 8000
    registry = {}
    contents_entries = []
    figures = []
    tables = []

    def p(text, role="body", level=1):
        base = chapter_pattern if role == "chapter" else heading_pattern if role == "heading" else body_pattern
        node = copy.deepcopy(base)
        replace_text(node, text)
        pp = node.find(W + "pPr")
        for name in ["numPr", "tabs", "sectPr"]:
            for old in list(pp.findall(W + name)):
                pp.remove(old)
        if role == "body":
            set_prop(pp, "ind", left=0, right=0, firstLine=0, hanging=0)
            set_prop(pp, "spacing", before=49, after=0, line=276, lineRule="auto")
            set_prop(pp, "jc", val="both")
        elif role == "code":
            set_prop(pp, "ind", left=0, right=0, firstLine=0, hanging=0)
            set_prop(pp, "spacing", before=0, after=0, line=240, lineRule="auto")
            set_prop(pp, "jc", val="left")
        elif role in {"chapter", "heading"}:
            set_prop(pp, "keepNext")
            set_prop(pp, "outlineLvl", val=0 if role == "chapter" else level)
            if role == "heading" and level > 1:
                set_prop(pp, "spacing", before=160, after=80, line=276, lineRule="auto")
        for r in node.findall(W + "r"):
            old = r.find(W + "rPr")
            if old is not None: r.remove(old)
            size = 16 if role == "chapter" else 14 if role == "heading" and level == 1 else 12
            rp = font(size)
            if role in {"chapter", "heading"}: rp.append(el("b"))
            r.insert(0, rp)
        if role == "heading" and level == 0:
            set_prop(pp, "jc", val="center")
        return node

    def bookmark(node, key):
        nonlocal bookmark_id
        bookmark_id += 1
        name = f"capstone_{bookmark_id}"
        add_bookmark(node, name, bookmark_id)
        registry[key] = name
        return name

    def pagebreak():
        node = el("p")
        r = el("r"); r.append(el("br", type="page")); node.append(r)
        return node

    def caption(text, key, is_table=False):
        node = p(("Table " if is_table else "Figure ") + text)
        pp = node.find(W + "pPr")
        set_prop(pp, "jc", val="center")
        set_prop(pp, "spacing", before=100, after=100, line=240, lineRule="auto")
        if is_table: set_prop(pp, "keepNext")
        for r in node.findall(W + "r"):
            old = r.find(W + "rPr")
            r.remove(old); r.insert(0, font(10))
        mark = bookmark(node, key)
        (tables if is_table else figures).append((text, mark))
        return node

    def table(headers, rows, widths=None, navigation=False):
        node = copy.deepcopy(toc_pattern)
        for row in list(node.findall(W + "tr")): node.remove(row)
        total = 8900
        if not navigation:
            # The template's contents table deliberately has no printed borders.
            # Data tables need explicit borders: Word's on-screen gridlines do
            # not print and cannot make those tables visible in exported PDFs.
            tp = node.find(W + "tblPr")
            set_prop(tp, "tblW", w=total, type="dxa")
            set_prop(tp, "tblLayout", type="fixed")
            for old in list(tp.findall(W + "tblBorders")):
                tp.remove(old)
            borders = el("tblBorders")
            for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
                borders.append(el(side, val="single", sz=6, space=0, color="000000"))
            tp.append(borders)
            margins = el("tblCellMar")
            for side, value in (("top", 45), ("left", 80), ("bottom", 45), ("right", 80)):
                margins.append(el(side, w=value, type="dxa"))
            tp.append(margins)
        if widths is None:
            widths = {2:[2600,6300],3:[1800,3100,4000],4:[2900,1850,2250,1900],5:[3000,1475,1475,1475,1475]}.get(len(headers), [total//len(headers)] * len(headers))
        grid = node.find(W + "tblGrid")
        if grid is not None: node.remove(grid)
        grid = el("tblGrid")
        for width in widths: grid.append(el("gridCol", w=width))
        node.insert(1, grid)
        for index, values in enumerate([headers] + rows):
            row = el("tr")
            trpr = el("trPr")
            if index == 0: trpr.append(el("tblHeader"))
            # Let narrative cells wrap; rows remain whole unless larger than a page.
            trpr.append(el("cantSplit")); row.append(trpr)
            for col, value in enumerate(values):
                cell = el("tc"); cp = el("tcPr"); cp.append(el("tcW", w=widths[col], type="dxa")); cell.append(cp)
                paragraph = p("" if isinstance(value, tuple) else str(value))
                pp = paragraph.find(W + "pPr")
                set_prop(pp, "spacing", before=30, after=30, line=276, lineRule="auto")
                set_prop(pp, "jc", val="left")
                if not navigation and index < min(2, len(rows)):
                    # Keep the header and at least two data rows together.
                    # This also keeps a two-row result table on one page.
                    set_prop(pp, "keepNext")
                if isinstance(value, tuple): page_field(paragraph, value[0])
                if index == 0:
                    for rp in paragraph.findall(".//" + W + "rPr"): rp.append(el("b"))
                cell.append(paragraph); row.append(cell)
            node.append(row)
        return node

    def figure(path, title, key, width=5.95):
        nonlocal image_id
        image_id += 1
        rid = f"rCapstone{image_id}"
        media = f"media/capstone_{image_id}.png"
        new_media["word/" + media] = path.read_bytes()
        relationship = ET.SubElement(rels, "{" + REL + "}Relationship")
        relationship.set("Id", rid); relationship.set("Type", NS["r"] + "/image"); relationship.set("Target", media)
        with Image.open(path) as im:
            iw, ih = im.size
        cx = int(width * 914400); cy = int(cx * ih / iw)
        node = p("")
        pp = node.find(W + "pPr"); set_prop(pp, "jc", val="center"); set_prop(pp, "keepNext")
        set_prop(pp, "spacing", before=100, after=0, line=240, lineRule="auto")
        run = node.find(W + "r")
        drawing = ET.SubElement(run, W + "drawing")
        inline = ET.SubElement(drawing, "{" + WP + "}inline", distT="0", distB="0", distL="0", distR="0")
        ET.SubElement(inline, "{" + WP + "}extent", cx=str(cx), cy=str(cy))
        ET.SubElement(inline, "{" + WP + "}docPr", id=str(image_id), name=key, descr=title)
        graphic = ET.SubElement(inline, "{" + A + "}graphic")
        data = ET.SubElement(graphic, "{" + A + "}graphicData", uri=PIC)
        pic = ET.SubElement(data, "{" + PIC + "}pic")
        nv = ET.SubElement(pic, "{" + PIC + "}nvPicPr")
        ET.SubElement(nv, "{" + PIC + "}cNvPr", id="0", name=key)
        ET.SubElement(nv, "{" + PIC + "}cNvPicPr")
        fill = ET.SubElement(pic, "{" + PIC + "}blipFill")
        ET.SubElement(fill, "{" + A + "}blip", {"{" + NS["r"] + "}embed": rid})
        stretch = ET.SubElement(fill, "{" + A + "}stretch"); ET.SubElement(stretch, "{" + A + "}fillRect")
        shape = ET.SubElement(pic, "{" + PIC + "}spPr")
        xfrm = ET.SubElement(shape, "{" + A + "}xfrm")
        ET.SubElement(xfrm, "{" + A + "}off", x="0", y="0")
        ET.SubElement(xfrm, "{" + A + "}ext", cx=str(cx), cy=str(cy))
        geom = ET.SubElement(shape, "{" + A + "}prstGeom", prst="rect"); ET.SubElement(geom, "{" + A + "}avLst")
        return [node, caption(title, key)]

    # Build front matter from the actual template elements, including the VIT logo.
    for i, text in {2: TITLE, 12: "Computer Science and Engineering\nSpecialization in IoT", 27: f'I hereby declare that the project entitled “{TITLE}” submitted by me, for the award of the degree of Bachelor of Technology in Computer Science and Engineering to VIT, is a record of bonafide work carried out by me under the supervision of Dr. Badrinath N.', 47: f'This is to certify that the project entitled “{TITLE}” submitted by SANIDHYA BHANDARI (23BCT0029), School of Computer Science and Engineering, VIT, for the award of the degree of Bachelor of Technology in Computer Science and Engineering, is a record of bonafide work carried out by him under my supervision during Fall Semester 2026–2027, as per the VIT code of academic and research ethics.', 79: 'I thank Vellore Institute of Technology for the academic resources and infrastructure that supported this capstone project. The work brought together data engineering, machine learning, software testing and research evaluation in a single implementation.', 81: 'I am grateful to my project guide, Dr. Badrinath N, for his guidance and feedback during the development of the project. His input helped me refine the scope and focus the report on what the available data and experiments can support.', 83: 'I also thank the faculty and project coordinators of the School of Computer Science and Engineering for organising the reviews and providing feedback on the work. The review process helped connect the implementation with a clearer research question and a reproducible evaluation.', 85: 'I acknowledge the developers of the open-source libraries and the maintainers of the independent cloud-log dataset used in the experiments. Their tools and documentation made it possible to test the framework and examine its limitations.', 87: 'Finally, I thank my family and friends for their support during the project.', 91: 'SANIDHYA BHANDARI\n23BCT0029'}.items():
        replace_text(ps[i], text)
    # Keep title spacing explicitly stated in the source's instructions.
    set_prop(ps[2].find(W + "pPr"), "spacing", before=57, line=360, lineRule="auto")
    for i in [3, 16, 43, 69, 73, 74]:
        node = ps[i]; node.getparent().remove(node)
    source_tables = body.findall(W + "tbl")
    student_table = source_tables[0]
    rows = student_table.findall(W + "tr")
    for row in rows[1:]: student_table.remove(row)
    for cell, value in zip(rows[0].findall(W + "tc"), ["23BCT0029", "SANIDHYA BHANDARI"]): replace_text(cell.find(W + "p"), value)
    guide_cells = source_tables[1].findall(".//" + W + "tc")
    replace_text(guide_cells[0].find(W + "p"), "Dr. Badrinath N")
    replace_text(guide_cells[1].find(W + "p"), "")
    start = list(body).index(ps[93])
    for node in list(body)[start:]: body.remove(node)
    front = list(body)
    # Build the report body and collect bookmark targets before making its lists.
    text = CONTENT.read_text(encoding="utf-8")
    abstract_text, main = text.split("# 1 INTRODUCTION", 1)
    abstract_text = abstract_text.replace("# Abstract", "").strip()
    main = "# 1 INTRODUCTION" + main
    main_nodes = []
    current_chapter = ""
    data_tables()
    figure_defs = {
        "architecture": (save_diagram("architecture", "architecture"), "4.1 Overall architecture of the implemented framework"),
        "dataflow": (save_diagram("dataflow", "dataflow"), "4.2 Data flow and separation of evaluation labels"),
        "usecase": (save_diagram("usecase", "usecase"), "4.3 Researcher and analyst use cases"),
        "components": (save_diagram("components", "components"), "4.4 Implemented modules and their responsibilities"),
        "sequence": (save_diagram("sequence", "sequence"), "4.5 Sequence of one controlled policy experiment"),
        "monthly": (ROOT / "figures/monthly_drift_signals.png", "7.1 Observed feature and attribution drift across monthly windows"),
        "confusion": (ROOT / "figures/diagnosis_confusion_matrix.png", "7.2 Held-out controlled diagnosis confusion matrix"),
        "policies": (ROOT / "figures/adaptation_policy_comparison.png", "7.3 Controlled adaptation policy comparison"),
    }

    def excerpt(file, func):
        code = (ROOT / file).read_text(encoding="utf-8")
        tree = ast.parse(code)
        n = next(n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == func)
        lines = code.splitlines()[n.lineno-1:n.end_lineno]
        return lines

    code_defs = {
        "diagnosis": excerpt("src/drift/diagnosis.py", "diagnose_coupled"),
        "calibration": excerpt("src/drift/diagnosis.py", "largest_gap_threshold"),
        "retrain": excerpt("src/adaptation/controller.py", "protected_retrain"),
        "commands": ["python scripts/run_all.py", "python scripts/run_robustness_experiments.py", "python scripts/run_external_validation.py", "python scripts/run_external_temporal_diagnosis.py", "python scripts/run_cost_sensitivity.py", "python -m pytest tests -q"],
    }
    for block in re.split(r"\n\s*\n", main.strip()):
        block = block.strip()
        if block.startswith("# "):
            title = block[2:]
            needs_page_break = bool(main_nodes) and current_chapter != "1"
            if main_nodes:
                if current_chapter == "1":
                    main_nodes.append(copy.deepcopy(ps[230]))
            current_chapter = title.split()[0]
            if current_chapter.isdigit():
                node = p("CHAPTER " + current_chapter, "chapter")
                if needs_page_break:
                    set_prop(node.find(W + "pPr"), "pageBreakBefore")
                # Only the numbered chapter heading belongs in the TOC.
                set_prop(node.find(W + "pPr"), "outlineLvl", val=9)
                main_nodes.append(node)
            node = p(title, "heading", 1)
            if needs_page_break and not current_chapter.isdigit():
                set_prop(node.find(W + "pPr"), "pageBreakBefore")
            mark = bookmark(node, title)
            contents_entries.append((title, mark, 0))
            main_nodes.append(node)
        elif block.startswith("##"):
            level = len(block) - len(block.lstrip("#"))
            title = block[level+1:]
            node = p(title, "heading", level)
            if title.startswith("A.5 "):
                set_prop(node.find(W + "pPr"), "pageBreakBefore")
            mark = bookmark(node, title)
            if level == 2: contents_entries.append((title, mark, 1))
            main_nodes.append(node)
        elif block.startswith("@table "):
            key = block.split()[1]
            title, headers, rows = TABLES[key]
            main_nodes.append(caption(title, "table_" + key, True))
            column_widths = {
                "functional": [700, 3900, 4300],
                "features": [3500, 5400],
                "tests": [2300, 4500, 2100],
                "diagnosis": [2400, 1700, 4800],
                "artifacts": [5800, 3100],
            }
            main_nodes.append(table(headers, rows, column_widths.get(key)))
        elif block.startswith("@figure "):
            key = block.split()[1]
            path, title = figure_defs[key]
            main_nodes.extend(figure(path, title, key, 5.0 if key == "confusion" else 5.95))
        elif block.startswith("@code "):
            key = block.split()[1]
            for line in code_defs[key]:
                main_nodes.append(p(line, "code"))
        else:
            # Inline backticks are markup only; text is native Word text.
            main_nodes.append(p(block.replace("`", "")))
    abstract_heading = p("ABSTRACT", "chapter")
    set_prop(abstract_heading.find(W + "pPr"), "outlineLvl", val=9)
    abstract_mark = bookmark(abstract_heading, "ABSTRACT")
    contents_entries.insert(0, ("ABSTRACT", abstract_mark, 0))
    toc_title = copy.deepcopy(ps[93]); replace_text(toc_title, "TABLE OF CONTENTS")
    body.append(toc_title)
    toc_rows = []
    for title, mark, level in contents_entries:
        prefix = "    " if level else ""
        toc_rows.append([prefix + title, (mark,)])
    body.append(table(["Contents", "Page No."], toc_rows, [7700,1200], True))
    body.append(pagebreak())
    for source_index, name, entries in [(99, "List of Figures", figures), (107, "List of Tables", tables)]:
        node = copy.deepcopy(ps[source_index]); replace_text(node, name); body.append(node)
        body.append(table(["Title", "Page No."], [[title, (mark,)] for title, mark in entries], [7700,1200], True))
        body.append(pagebreak())
    node = copy.deepcopy(ps[112]); replace_text(node, "List of Abbreviations"); body.append(node)
    abbreviations = [("API", "Application Programming Interface"), ("AWS", "Amazon Web Services"), ("BH", "Benjamini–Hochberg"), ("CI", "Confidence Interval"), ("CSV", "Comma-Separated Values"), ("FPR", "False-Positive Rate"), ("IAM", "Identity and Access Management"), ("IF", "Isolation Forest"), ("JS", "Jensen–Shannon Divergence"), ("LOF", "Local Outlier Factor"), ("PRISMA", "Preferred Reporting Items for Systematic Reviews and Meta-Analyses"), ("PSI", "Population Stability Index"), ("SHAP", "SHapley Additive exPlanations"), ("SVM", "Support Vector Machine")]
    for name, meaning in abbreviations:
        if name == "PRISMA":
            meaning = "Preferred Reporting Items for Systematic\n\tReviews and Meta-Analyses"
        node = copy.deepcopy(ps[114]); replace_text(node, f"{name}\t{meaning}"); body.append(node)
    body.append(pagebreak())
    node = copy.deepcopy(ps[130]); replace_text(node, "Symbols and Notations"); body.append(node)
    for symbol, meaning in [("x", "An event represented by the seven-feature input contract"), ("φj", "SHAP contribution of feature j to the explained output"), ("d", "Vector of shared-feature PSI values"), ("a", "Vector of mean absolute attribution displacement"), ("C", "Cosine coupling between d and a"), ("r", "Pearson correlation used for centred alignment"), ("τ", "A configured decision threshold"), ("TP / FP", "True positives / false positives"), ("TN / FN", "True negatives / false negatives")]:
        node = p(f"{symbol}\t{meaning}")
        set_prop(node.find(W + "pPr"), "jc", val="left")
        body.append(node)
    body.append(pagebreak())
    body.append(abstract_heading)
    for block in abstract_text.split("\n\n"): body.append(p(block))
    body.append(copy.deepcopy(ps[225]))
    for node in main_nodes: body.append(node)
    body.append(copy.deepcopy(original_sections[-1]))
    # Register the new diagram media without altering existing content types.
    if not any(x.get("Extension") == "png" for x in types):
        ET.SubElement(types, "{http://schemas.openxmlformats.org/package/2006/content-types}Default", Extension="png", ContentType="image/png")
    def xml_bytes(x): return ET.tostring(x, encoding="UTF-8", xml_declaration=True, standalone=True)
    parts["word/document.xml"] = xml_bytes(root)
    parts["word/_rels/document.xml.rels"] = xml_bytes(rels)
    parts["[Content_Types].xml"] = xml_bytes(types)
    # Field refresh is done by native Word, without changing source styles.
    OUTPUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in parts.items(): z.writestr(name, data)
        for name, data in new_media.items(): z.writestr(name, data)
    with zipfile.ZipFile(TEMPLATE) as baseline, zipfile.ZipFile(OUTPUT) as final:
        changed = [n for n in baseline.namelist() if baseline.read(n) != final.read(n)]
        assert set(changed) <= {"word/document.xml", "word/_rels/document.xml.rels", "[Content_Types].xml"}, changed
    sections = root.findall(".//" + W + "sectPr")
    assert len(sections) == len(original_sections) == 4
    def structural_signature(node):
        return [(x.tag, sorted(x.attrib.items()), (x.text or "").strip()) for x in node.iter()]
    assert all(structural_signature(a) == structural_signature(b) for a,b in zip(sections, original_sections))
    report_text = " ".join(root.xpath(".//w:t/text()", namespaces=NS))
    assert "<<" not in report_text and "<Contents" not in report_text
    audit = {"template_sha256": sha(source_bytes), "output_sha256": sha(OUTPUT.read_bytes()), "template_unmodified": sha(TEMPLATE.read_bytes()) == sha(source_bytes), "preserved_source_parts": len(parts) - len(changed), "changed_source_parts": changed, "sections_identical": True, "word_count_source_markdown": len(text.split()), "abstract_words": len(abstract_text.split()), "figure_count": len(figures), "content_table_count": len(tables), "chapter_count": 9, "output": str(OUTPUT)}
    assert 300 <= audit["abstract_words"] <= 500
    (TMP / "fidelity.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    (TMP / "bookmarks.json").write_text(json.dumps(registry, indent=2), encoding="utf-8")
    (TMP / "before_word_refresh.docx").write_bytes(OUTPUT.read_bytes())
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    build()
