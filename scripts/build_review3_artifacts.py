"""Build the Review 3 report and presentation from the supplied VIT templates.

The source report and deck are used as structural/style references. Only verified
facts from the current repository are inserted into the new artifacts.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from pptx import Presentation
from pptx.dml.color import RGBColor as PptRGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches as PptInches, Pt as PptPt


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs"
OUTPUT.mkdir(exist_ok=True)
REPORT_TEMPLATE = Path(r"D:\Downloads\BCSE497J Project I Report - Template FINAlL Updated  (2).docx")
PPT_TEMPLATE = Path(r"D:\Downloads\Review 3- 28-10- 2026.pptx")
REPORT_OUT = OUTPUT / "BCSE497J_Project_I_Report_SHAP_CloudTrail.docx"
PPT_OUT = OUTPUT / "Review_3_SHAP_CloudTrail_Drift.pptx"

TITLE = "SHAP-GUIDED DRIFT DIAGNOSIS FOR ADAPTIVE ANOMALY DETECTION IN AWS CLOUDTRAIL"
SHORT_TITLE = "SHAP-Guided CloudTrail Drift Diagnosis"
STUDENT = "SANIDHYA BHANDARI"
REG_NO = "23BCT0029"
GUIDE = "Dr. Badrinath N"
PROGRAMME = "B.Tech. in Computer Science and Engineering (IoT)"
DATE = "October 2026"


def set_cell_text(cell, text: str, bold: bool = False, size: int = 10) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(0)
    run = paragraph.add_run(str(text))
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.bold = bold
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP


def shade_cell(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_cell_width(cell, width_inches: float) -> None:
    cell.width = Inches(width_inches)
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.first_child_found_in("w:tcW")
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(int(width_inches * 1440)))
    tc_w.set(qn("w:type"), "dxa")


def style_doc(document: Document) -> None:
    for name in ["Normal", "Body Text", "List Paragraph"]:
        if name in document.styles:
            style = document.styles[name]
            style.font.name = "Times New Roman"
            style.font.size = Pt(12)
            style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
            style.paragraph_format.line_spacing = 1.15
            style.paragraph_format.space_after = Pt(6)
    for name, size in [("Heading 1", 16), ("Heading 2", 14), ("Heading 3", 12)]:
        if name in document.styles:
            style = document.styles[name]
            style.font.name = "Times New Roman"
            style.font.size = Pt(size)
            style.font.bold = True
            style.font.color.rgb = RGBColor(0, 51, 102)
            style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
            style.paragraph_format.space_before = Pt(10)
            style.paragraph_format.space_after = Pt(5)
    for section in document.sections:
        section.top_margin = Inches(0.85)
        section.bottom_margin = Inches(0.65)
        section.left_margin = Inches(0.95)
        section.right_margin = Inches(0.85)
        section.header_distance = Inches(0.35)
        section.footer_distance = Inches(0.35)


def clear_body(document: Document) -> None:
    body = document._element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)


def add_page_number(paragraph) -> None:
    run = paragraph.add_run()
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char1)
    run._r.append(instr)
    run._r.append(fld_char2)


def add_para(document, text: str = "", style: str = "Normal", bold: bool = False,
             align=None, size: int | None = None, italic: bool = False,
             space_after: int | None = None):
    paragraph = document.add_paragraph(style=style)
    if align is not None:
        paragraph.alignment = align
    if space_after is not None:
        paragraph.paragraph_format.space_after = Pt(space_after)
    run = paragraph.add_run(text)
    run.font.name = "Times New Roman"
    run.bold = bold
    run.italic = italic
    if size:
        run.font.size = Pt(size)
    return paragraph


def add_bullet(document, text: str, level: int = 0):
    paragraph = document.add_paragraph(style="List Paragraph")
    paragraph.paragraph_format.left_indent = Inches(0.25 + level * 0.25)
    paragraph.paragraph_format.first_line_indent = Inches(-0.15)
    paragraph.paragraph_format.space_after = Pt(3)
    run = paragraph.add_run("• " + text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(12)
    return paragraph


def add_numbered(document, text: str):
    paragraph = document.add_paragraph(style="List Paragraph")
    paragraph.paragraph_format.space_after = Pt(3)
    run = paragraph.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(12)
    return paragraph


def add_heading(document, text: str, level: int = 1):
    return add_para(document, text, f"Heading {level}", bold=True)


def add_table(document, headers: list[str], rows: list[list[str]], widths: list[float] | None = None):
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = False
    header = table.rows[0]
    set_repeat_table_header(header)
    for i, text in enumerate(headers):
        set_cell_text(header.cells[i], text, bold=True, size=9)
        shade_cell(header.cells[i], "D9EAF7")
        if widths:
            set_cell_width(header.cells[i], widths[i])
    for row_values in rows:
        row = table.add_row()
        for i, text in enumerate(row_values):
            set_cell_text(row.cells[i], text, size=9)
            if widths:
                set_cell_width(row.cells[i], widths[i])
    document.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_caption(document, text: str):
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(10)
    r.italic = True
    return p


def add_figure(document, path: Path, caption: str, width: float = 6.3):
    if path.is_file():
        p = document.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(path), width=Inches(width))
        add_caption(document, caption)


def add_toc_field(document):
    p = document.add_paragraph()
    run = p.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = ' TOC \\o "1-3" \\h \\z \\u '
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "Update this table in Word: right-click and choose Update Field."
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.extend([fld_begin, instr, fld_sep, text, fld_end])


def build_report() -> Path:
    document = Document(str(REPORT_TEMPLATE))
    style_doc(document)
    clear_body(document)
    section = document.sections[0]
    section.header.paragraphs[0].text = ""
    hp = section.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hr = hp.add_run(SHORT_TITLE)
    hr.font.name = "Times New Roman"
    hr.font.size = Pt(9)
    hr.font.color.rgb = RGBColor(100, 100, 100)
    fp = section.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.text = "BCSE497J - Project I  |  Page "
    for run in fp.runs:
        run.font.name = "Times New Roman"
        run.font.size = Pt(9)
    add_page_number(fp)

    # Cover page
    add_para(document, "B.Tech. BCSE497J - Project-I", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=14, space_after=22)
    add_para(document, TITLE, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=18, space_after=20)
    add_para(document, "Submitted in partial fulfillment of the requirements for the degree of", align=WD_ALIGN_PARAGRAPH.CENTER, size=12)
    add_para(document, "Bachelor of Technology", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=13)
    add_para(document, "in", align=WD_ALIGN_PARAGRAPH.CENTER, size=12)
    add_para(document, PROGRAMME, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=12)
    add_para(document, "by", align=WD_ALIGN_PARAGRAPH.CENTER, size=12)
    add_para(document, f"{STUDENT}\n({REG_NO})", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=12)
    add_para(document, "Under the Supervision of", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, space_after=3)
    add_para(document, GUIDE, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=12)
    add_para(document, "School of Computer Science and Engineering (SCOPE)", align=WD_ALIGN_PARAGRAPH.CENTER, size=12)
    add_para(document, DATE, align=WD_ALIGN_PARAGRAPH.CENTER, size=12, space_after=0)
    document.add_page_break()

    # Declaration
    add_heading(document, "DECLARATION", 1)
    add_para(document, f"I hereby declare that the project entitled \"{TITLE}\" submitted by me for the award of the degree of Bachelor of Technology in Computer Science and Engineering at VIT is a record of bonafide work carried out under the supervision of {GUIDE}.")
    add_para(document, "The work presented in this report has been prepared for the current project direction. It uses a real but unlabeled CloudTrail-style corpus and controlled perturbations for evaluation. The distinction between observational evidence and controlled labelled evidence is stated wherever it affects interpretation.")
    add_para(document, "I further declare that this report has not been submitted, either in part or in full, for the award of any other degree or diploma at this or any other institution.")
    add_para(document, "Place: Vellore\nDate: October 2026\n\nSignature of the Candidate", align=WD_ALIGN_PARAGRAPH.RIGHT)
    document.add_page_break()

    # Certificate
    add_heading(document, "CERTIFICATE", 1)
    add_para(document, f"This is to certify that the project entitled \"{TITLE}\" submitted by {STUDENT} ({REG_NO}), School of Computer Science and Engineering, VIT, for the award of the degree of Bachelor of Technology in Computer Science and Engineering, is a record of bonafide work carried out under the supervision of {GUIDE} during the Fall Semester 2026.")
    add_para(document, "The work reported in this document has been reviewed as a project implementation and research prototype. The report records the current limitations of the dataset, validation protocol, and external transfer results instead of presenting unsupported production claims.")
    add_para(document, "Place: Vellore\nDate: October 2026\n\n\nSignature of the Guide", align=WD_ALIGN_PARAGRAPH.RIGHT)
    document.add_page_break()

    # Acknowledgement
    add_heading(document, "ACKNOWLEDGEMENTS", 1)
    add_para(document, "I would like to express my sincere gratitude to Vellore Institute of Technology for providing the academic environment and computing facilities needed to carry out this project.")
    add_para(document, f"I am especially thankful to my project guide, {GUIDE}, for the guidance, feedback, and encouragement that helped me refine the project from a broad cloud-security system into a focused study of drift diagnosis and explainable anomaly detection.")
    add_para(document, "I also thank the faculty members and reviewers of the School of Computer Science and Engineering for their questions and suggestions. Their feedback helped me state the dataset limitations clearly, separate real-data observations from controlled evaluation, and improve the reproducibility of the implementation.")
    add_para(document, "Finally, I acknowledge the open-source Python, scikit-learn, SHAP, pandas, and testing tools used to implement and validate the research prototype.")
    add_para(document, f"\n{STUDENT}\n{REG_NO}", align=WD_ALIGN_PARAGRAPH.RIGHT)
    document.add_page_break()

    # Contents and lists
    add_heading(document, "TABLE OF CONTENTS", 1)
    add_toc_field(document)
    add_para(document, "If the table is not populated automatically, open the document in Microsoft Word, select the table, and choose Update Field.", italic=True, size=10)
    document.add_page_break()
    add_heading(document, "LIST OF FIGURES", 1)
    for item in [
        "Figure 4.1  Research pipeline for drift diagnosis and protected adaptation",
        "Figure 5.1  Monthly feature and SHAP drift signals",
        "Figure 5.2  Held-out controlled diagnosis confusion matrix",
        "Figure 5.3  Adaptation-policy comparison",
    ]:
        add_para(document, item)
    add_heading(document, "LIST OF TABLES", 1)
    for item in [
        "Table 2.1  Selected literature and relevance to the project",
        "Table 3.1  Functional and research requirements",
        "Table 3.2  Non-functional requirements and safeguards",
        "Table 5.1  Primary dataset and temporal protocol",
        "Table 5.2  Controlled adaptation results",
        "Table 5.3  Independent external validation",
    ]:
        add_para(document, item)
    add_heading(document, "LIST OF ABBREVIATIONS", 1)
    add_table(document, ["Abbreviation", "Meaning"], [
        ["AWS", "Amazon Web Services"], ["API", "Application Programming Interface"],
        ["FPR", "False-positive rate"], ["IF", "Isolation Forest"],
        ["JS", "Jensen-Shannon divergence"], ["PSI", "Population Stability Index"],
        ["SHAP", "SHapley Additive exPlanations"], ["XAI", "Explainable Artificial Intelligence"],
    ], [1.5, 5.8])
    document.add_page_break()

    # Abstract
    add_heading(document, "ABSTRACT", 1)
    abstract = ("Cloud audit behaviour changes over time. New services, regions, identity types, and legitimate automation can alter the distribution of AWS CloudTrail events even when there is no security incident. For an unsupervised anomaly detector, this creates a practical question: when should the model be adapted, and when should a drift alarm be treated as an observation rather than a reason to retrain? This project develops and evaluates a reproducible SHAP-guided drift-diagnosis protocol for that question. The primary corpus contains 1,939,207 CloudTrail-style records across 45 monthly windows and has no attack labels. It is therefore used for observational drift analysis only. A controlled semi-synthetic benchmark injects reproducible benign and security-relevant changes into real-data samples so that diagnosis and adaptation can be evaluated without pretending that the original records are labelled incidents. An Isolation Forest is used as the primary detector, and TreeSHAP is used to measure how the detector's attribution profile changes over time. Feature drift, attribution drift, and their alignment are compared through static, periodic, feature-only, SHAP-only, dual-signal, and coupling-based policies. The validation-tuned diagnosis achieved a macro-F1 of 0.7306 under the controlled protocol. Dual-signal gating reduced the false-positive rate relative to static adaptation by 0.0885, while its paired F1 difference was -0.0028 and not statistically distinguishable from zero. The proposed attribution-feature coupling score was neutral in the controlled benchmark. On a separate labelled CloudTrail corpus, a source-tuned coupling threshold transferred conservatively, while a label-free largest-gap calibration recovered all attack scenario windows in a small 12-window checkpoint. This result is exploratory and requires multi-period validation. The final contribution is a transparent CloudTrail-specific evaluation protocol that combines explainability, drift diagnosis, protected retraining, uncertainty reporting, and explicit limitations.")
    add_para(document, abstract, size=12)
    add_para(document, "Keywords: AWS CloudTrail; anomaly detection; concept drift; SHAP; explainable cybersecurity; adaptive retraining; unsupervised learning.", italic=True, size=11)
    document.add_page_break()

    # Chapter 1
    add_para(document, "CHAPTER 1", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=16)
    add_heading(document, "1. INTRODUCTION", 1)
    add_heading(document, "1.1 Background", 2)
    add_para(document, "AWS CloudTrail records management activity across services, regions, identities, and API operations. This audit trail is valuable for security monitoring, but a log collection system is not automatically an anomaly detector. The behaviour of a cloud account changes as teams deploy new workloads, enable services, rotate identities, or change automation. A detector trained only on earlier behaviour can therefore become stale or generate alerts for legitimate changes.")
    add_para(document, "The challenge is more subtle for unsupervised detection. In many real environments, attack labels are incomplete or unavailable, so a model learns a representation of normal activity rather than a conventional attack-versus-benign classifier. When the observed distribution changes, a feature-only drift alarm cannot tell us whether the detector's decision logic has become security-relevant. Retraining every time a feature changes can also absorb contaminated records and create unnecessary model versions.")
    add_heading(document, "1.2 Motivation", 2)
    add_para(document, "This project is motivated by the need for a cautious adaptation decision. Feature-distribution drift tells us that the observed records changed. SHAP-attribution drift tells us that the detector is relying on different feature contributions. If the same features that changed in the data also become more important to the detector, the change may deserve stronger attention than a distribution shift that has little effect on the model's explanations.")
    add_heading(document, "1.3 Scope of the Project", 2)
    add_bullet(document, "Observational analysis of a real, unlabeled CloudTrail-style corpus at monthly resolution.")
    add_bullet(document, "Isolation Forest anomaly detection with TreeSHAP attribution validation.")
    add_bullet(document, "Feature drift, SHAP drift, and attribution-feature coupling for diagnosis.")
    add_bullet(document, "Controlled benign and security-relevant perturbations for labelled evaluation.")
    add_bullet(document, "Protected retraining using replay data and baseline-normal candidates.")
    add_bullet(document, "Independent detector validation and a small external temporal diagnosis checkpoint.")
    add_bullet(document, "Out of scope: production AWS enforcement, real incident attribution, and claims of attack recall on the unlabeled primary corpus.")
    document.add_page_break()

    # Chapter 2
    add_para(document, "CHAPTER 2", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=16)
    add_heading(document, "2. PROJECT DESCRIPTION AND GOALS", 1)
    add_heading(document, "2.1 Literature Review", 2)
    add_para(document, "The literature review was organized around five connected areas: unsupervised anomaly detection, explainable feature attribution, unlabeled drift detection, selective adaptation, and CloudTrail or cloud-security monitoring. The review shows that the individual building blocks are established. Isolation Forest is a baseline rather than a new contribution, and SHAP provides model attribution rather than causal proof of malicious intent. The research opportunity lies in evaluating how these signals should be combined for a CloudTrail-specific adaptation decision.")
    literature_rows = [
        ["Liu, Ting and Zhou (2008)", "Isolation Forest", "Unsupervised anomaly-scoring baseline; not a drift or CloudTrail method."],
        ["Lundberg and Lee (2017)", "SHAP", "Additive feature attribution used to monitor detector explanations."],
        ["Sethi and Kantardzic (2017)", "Unlabeled drift detection", "Shows why input change can produce false alarms without labels."],
        ["Kuppa and Le-Khac (2022)", "Security-domain drift adaptation", "Motivates robust adaptation and caution around drift."],
        ["Han et al. (2023)", "OWAD", "Connects normality shift, explanation, and adaptation in security."],
        ["Lee et al. (2023)", "Explainable unsupervised drift", "Closest evidence that SHAP drift is already an active direction."],
        ["Li et al. (2024)", "Drift-type-aware adaptation", "Supports diagnosis before choosing a retraining action."],
        ["Varma and Ramya (2025)", "CloudTrail XAI", "CloudTrail explanation pipeline, but no attribution-conditioned drift gate."],
        ["AWS SageMaker documentation", "Feature attribution drift", "Confirms operational use of attribution monitoring."],
    ]
    add_table(document, ["Source", "Focus", "Relevance to this project"], literature_rows, [1.8, 1.75, 3.75])
    add_caption(document, "Table 2.1  Selected literature and relevance to the project")
    add_heading(document, "2.2 Research Gap", 2)
    add_para(document, "Existing research establishes anomaly detection, explanation, drift monitoring, and adaptive retraining as separate topics. However, a change in CloudTrail feature distributions is not automatically a change that should trigger adaptation. The defensible gap addressed here is a reproducible CloudTrail-specific evaluation of whether model-attribution drift adds decision-relevant information beyond feature-distribution drift when controlling adaptation of an unlabeled anomaly detector.")
    add_para(document, "The project does not claim to be the first use of SHAP drift or the first use of explanations in security monitoring. Its contribution is the combination of a real CloudTrail audit, an explicit observational-versus-controlled evidence split, an interpretable feature-attribution coupling score, protected retraining, independent transfer checks, and transparent falsification results.")
    add_heading(document, "2.3 Objectives", 2)
    for objective in [
        "Audit the primary CloudTrail-style corpus and establish its schema, temporal resolution, concentration, and lack of attack labels.",
        "Construct chronological train, validation, and held-out test windows without leaking future information.",
        "Train and validate an Isolation Forest detector and TreeSHAP explanations using a fixed feature contract.",
        "Measure feature drift, attribution drift, and feature-attribution coupling across monthly windows.",
        "Evaluate feature-only, SHAP-only, dual, coupling, static, and periodic adaptation policies on controlled perturbations.",
        "Report robustness, uncertainty, external transfer, and limitations in a form suitable for review.",
    ]:
        add_numbered(document, objective)
    add_heading(document, "2.4 Problem Statement", 2)
    add_para(document, "How can an unsupervised AWS CloudTrail anomaly detector distinguish ordinary behavioural change from model-relevant drift, so that adaptation is triggered selectively and explanations remain auditable? The problem is constrained by the absence of attack labels in the primary corpus and by the fact that its main export records month-level timestamps rather than complete event sequences.")
    add_heading(document, "2.5 Project Plan", 2)
    add_table(document, ["Phase", "Work", "Current status"], [
        ["1. Audit and literature", "Dataset manifest, literature matrix, research gap", "Completed; PRISMA human screening remains open"],
        ["2. Temporal protocol", "Monthly windows and 27/9/9 chronological split", "Completed"],
        ["3. Detector and SHAP", "Isolation Forest, attribution validation, saved artifacts", "Completed"],
        ["4. Drift diagnosis", "Feature, SHAP, coupling, and threshold tuning", "Completed"],
        ["5. Adaptation evaluation", "Protected retraining, policy comparison, cost analysis", "Completed for controlled protocol"],
        ["6. Transfer and reporting", "External checks, manuscript, report, and presentation", "Current Review 3 deliverable"],
    ], [1.35, 3.75, 2.2])
    document.add_page_break()

    # Chapter 3
    add_para(document, "CHAPTER 3", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=16)
    add_heading(document, "3. TECHNICAL SPECIFICATION", 1)
    add_heading(document, "3.1 Requirements", 2)
    add_heading(document, "3.1.1 Functional Requirements", 3)
    functional = [
        ["FR1", "Read the read-only CloudTrail-style CSV and generate a provenance manifest."],
        ["FR2", "Build train, validation, and test partitions chronologically by month."],
        ["FR3", "Encode event attributes using mappings learned from training data only."],
        ["FR4", "Train Isolation Forest and score event-level samples."],
        ["FR5", "Validate TreeSHAP additivity and produce per-feature attribution summaries."],
        ["FR6", "Compute feature drift, attribution drift, and attribution-feature coupling."],
        ["FR7", "Tune thresholds on validation scenarios and evaluate held-out scenarios."],
        ["FR8", "Compare protected adaptation policies and save reproducible CSV/JSON outputs."],
        ["FR9", "Run detector-only and temporal diagnosis checks on an independent corpus."],
    ]
    add_table(document, ["ID", "Requirement"], functional, [0.7, 6.6])
    add_heading(document, "3.1.2 Non-Functional Requirements", 3)
    add_table(document, ["Property", "Requirement / safeguard", "Evidence"], [
        ["Reproducibility", "Fixed seeds, pinned dependencies, saved artifacts", "28 automated tests and deterministic outputs"],
        ["Temporal integrity", "No random split for drift experiments", "27 train, 9 validation, 9 test months"],
        ["Label integrity", "No attack labels used by detector or controller", "Labels restricted to controlled evaluation"],
        ["Interpretability", "Report changed features and attribution alignment", "SHAP additivity residual 2.66e-14"],
        ["Safety", "No production AWS enforcement or automatic IAM action", "Offline protected-retraining prototype"],
        ["Auditability", "Record limitations and negative results", "Manuscript and validation documents"],
    ], [1.25, 3.5, 2.55])
    add_heading(document, "3.2 Feasibility Study", 2)
    add_para(document, "Technical feasibility is supported by mature Python libraries and a CPU-based workflow. Isolation Forest and TreeSHAP are available in the project environment, and the primary computations are reproducible without dedicated GPU hardware. Economic feasibility is also favourable because the project reuses an existing dataset and open-source tools. The main cost is computational time for SHAP and repeated controlled experiments. Social and operational feasibility depend on transparent limitations: the system is a research prototype, not an autonomous security-enforcement service.")
    add_heading(document, "3.3 System Specification", 2)
    add_table(document, ["Component", "Specification"], [
        ["Dataset", "1,939,207 records; 18 columns; 45 monthly windows; no attack labels"],
        ["Representation", "eventName, eventSource, awsRegion, userIdentitytype, errorCode, requestParametersinstanceType, isRoot"],
        ["Primary model", "Isolation Forest; 100 estimators; contamination 0.05; random state 42"],
        ["Explanation", "TreeSHAP on the fitted tree ensemble with additivity checks"],
        ["Drift signals", "PSI/JS-style feature drift, Wasserstein/top-k SHAP drift, coupling metrics"],
        ["Software", "Python 3.11, pandas, NumPy, scikit-learn, SHAP, SciPy, joblib, pytest"],
        ["Execution", "Local reproducible scripts; external source files remain read-only"],
    ], [1.65, 5.65])
    document.add_page_break()

    # Chapter 4
    add_para(document, "CHAPTER 4", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=16)
    add_heading(document, "4. DESIGN APPROACH AND DETAILS", 1)
    add_heading(document, "4.1 System Architecture", 2)
    add_para(document, "The architecture is intentionally organized as an offline research pipeline rather than an automated AWS enforcement system. The data flow is: source audit -> temporal feature construction -> train-only encoding -> Isolation Forest scoring -> TreeSHAP explanation -> feature and attribution drift monitoring -> coupling diagnosis -> protected adaptation simulation -> statistical evaluation and reporting.")
    add_table(document, ["Stage", "Input", "Output"], [
        ["Audit", "Read-only source CSV", "Manifest, checksum, schema, concentration findings"],
        ["Temporal preparation", "eventTime and event attributes", "Monthly features, distributions, 27/9/9 split"],
        ["Detection", "Encoded event matrix", "Anomaly scores and fitted model artifact"],
        ["Explanation", "Fitted Isolation Forest", "SHAP values and attribution summaries"],
        ["Diagnosis", "Feature drift + SHAP drift", "Stable, benign, security-relevant, or review-required state"],
        ["Adaptation", "Diagnosis + current sample", "Protected retraining policy outcome and metrics"],
    ], [1.55, 2.7, 3.05])
    add_caption(document, "Figure 4.1  Research pipeline for drift diagnosis and protected adaptation")
    add_heading(document, "4.2 Design: Data Flow and Decision Logic", 2)
    add_para(document, "The data-flow design keeps evaluation labels outside the detection path. For the controlled benchmark, a perturbation generator creates a current sample and retains the hidden changed-row mask only for evaluation. The detector receives only the sample. The diagnosis layer receives feature drift, SHAP drift, and coupling values. The controller receives the diagnosis and can retrain only on replay data plus records classified as normal by the baseline model.")
    add_para(document, "The dual rule maps low feature and low attribution drift to stable, high feature drift with low attribution drift to likely benign drift, and high values for both signals to security-relevant drift. The coupling extension compares a per-feature PSI vector with a per-feature absolute SHAP-displacement vector. A conservative score is the minimum of cosine alignment and centered alignment. Conflicting signals remain review-required rather than being forced into a binary security decision.")
    add_heading(document, "4.3 Use Case", 2)
    add_para(document, "The primary actor is a security analyst or researcher who reviews drift evidence and decides whether a model update is acceptable. The automated components prepare scores, explanations, drift summaries, and protected-retraining results. The project does not attach IAM policies, modify AWS resources, or claim to identify the causal source of an incident. This boundary is important because the current evidence is observational and controlled, not an operational incident-response evaluation.")
    add_heading(document, "4.4 Research Protocol", 2)
    add_bullet(document, "Train-only mappings and chronological partitions prevent future information from entering the baseline.")
    add_bullet(document, "Validation scenarios are used for threshold tuning; held-out seeds are used for final controlled comparison.")
    add_bullet(document, "Bootstrap intervals, paired tests, detector ablations, sample-size ablations, and cost sensitivity are reported.")
    add_bullet(document, "The independent corpus is evaluated separately because it does not share the primary monthly protocol.")
    document.add_page_break()

    # Chapter 5
    add_para(document, "CHAPTER 5", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=16)
    add_heading(document, "5. IMPLEMENTATION STATUS AND PRELIMINARY RESULTS", 1)
    add_para(document, "This chapter reports the current Review 3 implementation. Results are taken from saved repository artifacts. The primary data is real but unlabeled; controlled labels are used only for the semi-synthetic benchmark and external evaluation after diagnosis.")
    add_heading(document, "5.1 Dataset and Temporal Protocol", 2)
    add_table(document, ["Property", "Verified value"], [
        ["Rows", "1,939,207"], ["Columns", "18"], ["Temporal windows", "45 monthly windows"],
        ["Primary labels", "None"], ["Chronological split", "27 train / 9 validation / 9 held-out test months"],
        ["SHA-256", "b3aa4fcf28747f4f84457d2d3b76f4c27901bd2e6289bf6d6288cb9587d20589"],
        ["Important limitation", "Month-level eventTime in the primary export; no event-order claims"],
    ], [2.1, 5.2])
    add_caption(document, "Table 5.1  Primary dataset and temporal protocol")
    add_heading(document, "5.2 Observational Drift Analysis", 2)
    add_para(document, "The monthly analysis measures how CloudTrail behaviour and detector explanations change relative to the training reference months. The timeline is descriptive. It does not provide attack recall because the source corpus has no attack labels.")
    add_figure(document, ROOT / "figures" / "monthly_drift_signals.png", "Figure 5.1  Monthly feature and SHAP drift signals", width=6.4)
    add_heading(document, "5.3 Controlled Diagnosis", 2)
    add_para(document, "The controlled benchmark uses stable, benign-region, benign-identity, benign-service, security-privilege, security-defense, and security-credential perturbations. Five validation seeds tune thresholds and ten held-out seeds support the final comparison. The validation-tuned diagnosis achieved macro-F1 0.7306. This result measures the defined perturbation protocol, not naturally occurring attack detection.")
    add_figure(document, ROOT / "figures" / "diagnosis_confusion_matrix.png", "Figure 5.2  Held-out controlled diagnosis confusion matrix", width=4.7)
    add_heading(document, "5.4 Selective Adaptation", 2)
    add_table(document, ["Policy", "Trigger rate", "Unnecessary adaptation", "Mean F1", "FPR"], [
        ["Static", "0.0000", "0.0000", "0.2901", "0.4282"],
        ["Periodic", "0.3429", "0.2000", "0.2888", "0.3160"],
        ["Feature-only", "0.7571", "0.3286", "0.2734", "0.1825"],
        ["Dual-signal", "0.2429", "0.0000", "0.2873", "0.3397"],
        ["Coupled / conservative", "0.2429", "0.0000", "0.2873", "0.3397"],
    ], [1.8, 1.25, 1.55, 1.25, 1.0])
    add_caption(document, "Table 5.2  Controlled adaptation results")
    add_figure(document, ROOT / "figures" / "adaptation_policy_comparison.png", "Figure 5.3  Adaptation-policy comparison", width=6.4)
    add_para(document, "Relative to static adaptation, the dual policy reduced FPR by 0.0885 with a 95% bootstrap interval of [-0.1272, -0.0561] and Benjamini-Hochberg adjusted q=0.000434. Its paired F1 difference was -0.0028 with a 95% interval of [-0.0181, 0.0112]. The coupling policy matched the dual policy in this controlled benchmark, so it is reported as a neutral diagnostic ablation rather than a universal improvement.")
    add_heading(document, "5.5 Robustness and External Validation", 2)
    add_para(document, "Detector choice matters on the independent Cloud Log Sampling Dataset. Isolation Forest achieved precision 0.3306, recall 0.7137, F1 0.4519, and FPR 0.1738. Local Outlier Factor achieved F1 0.5334 with higher recall and FPR, while One-Class SVM achieved F1 0.0015. These results support portability of the feature contract but not a claim that one detector is universally best.")
    add_table(document, ["External policy", "Precision", "Recall", "F1", "FPR"], [
        ["Feature-only", "0.9091", "1.0000", "0.9524", "0.5000"],
        ["SHAP-only", "0.9091", "1.0000", "0.9524", "0.5000"],
        ["Dual-signal", "0.9091", "1.0000", "0.9524", "0.5000"],
        ["Source-tuned coupling", "1.0000", "0.1000", "0.1818", "0.0000"],
        ["Unsupervised largest-gap coupling", "1.0000", "1.0000", "1.0000", "0.0000"],
    ], [2.45, 1.15, 1.05, 1.05, 1.05])
    add_caption(document, "Table 5.3  Independent external temporal diagnosis checkpoint")
    add_para(document, "The successful largest-gap result is based on 12 scenario windows and estimates a coupling threshold from the unlabeled target-score distribution. It is an encouraging transfer checkpoint, not production evidence. Broader multi-period validation is required.")
    add_heading(document, "5.6 Novelty and Current Status", 2)
    add_para(document, "The novelty is methodological and empirical. The project connects CloudTrail-specific drift monitoring with model-attribution change, protected adaptation, and a label-free transfer-calibration experiment. It does not claim novelty for Isolation Forest, SHAP, cosine similarity, or drift detection in isolation. The current implementation is complete as a capstone research prototype, while human PRISMA screening, supervisor review, venue verification, and stronger independent post-adaptation validation remain before journal submission.")
    add_heading(document, "5.7 Limitations", 2)
    for limitation in [
        "The primary corpus has no attack ground truth, so real-data results are observational.",
        "Controlled perturbations are reproducible but semi-synthetic and do not replace incident evidence.",
        "Month-level timestamps limit event-order and session-level conclusions.",
        "Ordinal encoding of categorical attributes may impose artificial geometry.",
        "The target-window calibration is based on a small external checkpoint and may be unstable with few or contaminated windows.",
        "The adaptation controller is an offline research prototype and does not enforce AWS IAM changes.",
    ]:
        add_bullet(document, limitation)
    document.add_page_break()

    # References and appendix
    add_para(document, "CHAPTER 6", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=16)
    add_heading(document, "6. REFERENCES", 1)
    references = [
        '[1] F. T. Liu, K. M. Ting, and Z.-H. Zhou, "Isolation Forest," in Proc. IEEE International Conference on Data Mining, 2008, pp. 413-422. doi:10.1109/ICDM.2008.17.',
        '[2] S. M. Lundberg and S.-I. Lee, "A unified approach to interpreting model predictions," in Advances in Neural Information Processing Systems, vol. 30, 2017.',
        '[3] F. Maggi, W. Robertson, C. Kruegel, and G. Vigna, "Protecting a moving target: Addressing web application concept drift," in RAID, 2009. doi:10.1007/978-3-642-04342-0_2.',
        '[4] R. Sethi and M. Kantardzic, "On the reliable detection of concept drift from streaming unlabeled data," Expert Systems with Applications, 2017. doi:10.1016/j.eswa.2017.04.008.',
        '[5] R. Kuppa and A. H. M. Le-Khac, "Learn to adapt: Robust drift detection in security domain," Computers and Electrical Engineering, 2022. doi:10.1016/j.compeleceng.2022.108239.',
        '[6] S. Han et al., "Anomaly detection in the open world: Normality shift detection, explanation and adaptation," NDSS, 2023. doi:10.14722/ndss.2023.24830.',
        '[7] X. Li, Y. Yu, Y. Zhang, Y. Luo, and X. Xie, "Concept drift adaptation by exploiting drift type," ACM TKDD, 2024. doi:10.1145/3638777.',
        '[8] S. Lee, J. Lee, J. Lee, and J. Lee, "Explainable artificial intelligence-based model drift detection applicable to unsupervised environments," Computers, Materials & Continua, 2023. doi:10.32604/cmc.2023.040235.',
        '[9] A. Varma and P. Ramya, "An explainable machine learning and large language model framework for anomaly detection in AWS CloudTrail logs," ICNGN, 2025. doi:10.1109/ICNGN67480.2025.11413642.',
        '[10] Amazon Web Services, "Feature attribution drift for models in production," Amazon SageMaker Clarify documentation, accessed 2026.',
        '[11] Amazon Web Services, "Understanding CloudTrail events," AWS CloudTrail documentation, accessed 2026.',
        '[12] G. Arora et al., "A systematic review on detection and adaptation of concept drift in streaming data using machine learning techniques," WIREs Data Mining and Knowledge Discovery, 2024. doi:10.1002/WIDM.1536.',
        '[13] Scikit-learn developers, "IsolationForest documentation," scikit-learn User Guide, accessed 2026.',
        '[14] S. Lundberg et al., "TreeExplainer documentation," SHAP documentation, accessed 2026.',
        '[15] PRISMA Statement, "PRISMA 2020 statement and checklist," prisma-statement.org, accessed 2026.',
    ]
    for ref in references:
        p = document.add_paragraph(style="List Paragraph")
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.first_line_indent = Inches(-0.25)
        p.paragraph_format.space_after = Pt(5)
        r = p.add_run(ref)
        r.font.name = "Times New Roman"
        r.font.size = Pt(10.5)
    document.add_page_break()
    add_para(document, "APPENDIX A - SAMPLE CODE", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=16)
    add_para(document, "The following excerpt summarizes the core diagnosis rule. The complete implementation is maintained in the project repository.", italic=True, size=11)
    code = (
        "feature_high = feature_score >= feature_threshold\n"
        "shap_high = shap_score >= shap_threshold\n"
        "coupling_high = coupling_score >= coupling_threshold\n\n"
        "if not feature_high and not shap_high:\n"
        "    state = 'stable'\n"
        "elif feature_high and not shap_high:\n"
        "    state = 'benign_drift'\n"
        "elif feature_high and shap_high and coupling_high:\n"
        "    state = 'security_relevant_drift'\n"
        "else:\n"
        "    state = 'review_required'"
    )
    p = document.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.35)
    p.paragraph_format.right_indent = Inches(0.35)
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run(code)
    r.font.name = "Consolas"
    r.font.size = Pt(10)
    add_para(document, "Reproduction commands:\npython scripts/run_all.py\npython scripts/run_robustness_experiments.py\npython scripts/run_external_temporal_diagnosis.py\npython -m pytest tests -q", size=11)
    document.settings.element.append(OxmlElement("w:updateFields"))
    document.settings.element[-1].set(qn("w:val"), "true")
    document.save(str(REPORT_OUT))
    return REPORT_OUT


# ---- PowerPoint template editing fallback ----
PPT_NAVY = PptRGBColor(0x17, 0x36, 0x5D)
PPT_BLUE = PptRGBColor(0x2F, 0x6A, 0xB8)
PPT_TEAL = PptRGBColor(0x26, 0x7C, 0xA4)
PPT_DARK = PptRGBColor(0x37, 0x29, 0x1F)
PPT_MUTED = PptRGBColor(0x70, 0x68, 0x66)


def shape_by_id(slide, shape_id: int):
    return next(shape for shape in slide.shapes if shape.shape_id == shape_id)


def remove_shape(shape) -> None:
    shape._element.getparent().remove(shape._element)


def set_shape_text(shape, text: str, size: int = 20, color=PPT_DARK, bold=False, align=PP_ALIGN.LEFT):
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = PptInches(0.08)
    tf.margin_right = PptInches(0.08)
    tf.margin_top = PptInches(0.05)
    tf.margin_bottom = PptInches(0.05)
    lines = text.split("\n")
    for index, line in enumerate(lines):
        p = tf.paragraphs[0] if index == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = 1.05
        p.space_after = PptPt(4)
        run = p.add_run()
        run.text = line
        run.font.name = "Arial"
        run.font.size = PptPt(size)
        run.font.color.rgb = color
        run.font.bold = bold


def add_ppt_text(slide, text: str, x: float, y: float, w: float, h: float, size: int = 17, color=PPT_DARK, bold=False):
    box = slide.shapes.add_textbox(PptInches(x), PptInches(y), PptInches(w), PptInches(h))
    set_shape_text(box, text, size=size, color=color, bold=bold)
    return box


def add_ppt_picture(slide, path: Path, x: float, y: float, w: float, h: float):
    if path.is_file():
        slide.shapes.add_picture(str(path), PptInches(x), PptInches(y), PptInches(w), PptInches(h))


def build_presentation() -> Path:
    prs = Presentation(str(PPT_TEMPLATE))
    date_shapes = {2: 4, 3: 7, 4: 2, 5: 8, 6: 2, 7: 2, 8: 2, 9: 2, 10: 2, 11: 2, 12: 2, 13: 4, 14: 5}
    footer_shapes = {2: 5, 3: 8, 4: 5, 5: 9, 6: 5, 7: 5, 8: 5, 9: 5, 10: 5, 11: 5, 12: 5, 13: 5, 14: 6}
    number_shapes = {2: 6, 3: 9, 4: 6, 5: 10, 6: 6, 7: 6, 8: 6, 9: 6, 10: 6, 11: 6, 12: 6, 13: 6, 14: 7}
    for slide_number, slide in enumerate(prs.slides, 1):
        if slide_number in date_shapes:
            set_shape_text(shape_by_id(slide, date_shapes[slide_number]), "28/10/26", 10, PPT_MUTED)
        if slide_number in footer_shapes:
            set_shape_text(shape_by_id(slide, footer_shapes[slide_number]), "SCOPE", 10, PPT_MUTED, align=PP_ALIGN.CENTER)
        if slide_number in number_shapes:
            set_shape_text(shape_by_id(slide, number_shapes[slide_number]), str(slide_number), 10, PPT_MUTED, align=PP_ALIGN.RIGHT)

    set_shape_text(shape_by_id(prs.slides[0], 7), f"B.Tech. BCSE497J - Project-I\n{TITLE}", 24, PPT_NAVY, True, PP_ALIGN.CENTER)
    set_shape_text(shape_by_id(prs.slides[0], 9), f"Team member:\n{STUDENT} ({REG_NO})\n\nFaculty guide:\n{GUIDE}\n\nReview 3 | 28 October 2026", 18, PPT_DARK, False, PP_ALIGN.CENTER)

    titles = {
        2: "Project Direction and Current Scope", 3: "Aim", 4: "Abstract", 5: "Literature Review",
        6: "Research Gap", 7: "Objectives and Expected Outcome", 8: "Framework / Architecture",
        9: "Functional Requirements", 10: "Modules", 11: "Experiments and Results",
        12: "Conclusion and Future Work", 13: "Outcome Achieved", 14: "References",
    }
    title_shape_ids = {2: 2, 3: 4, 4: 4, 5: 4, 6: 4, 7: 4, 8: 4, 9: 4, 10: 4, 11: 4, 12: 4, 13: 2, 14: 4}
    for n, title in titles.items():
        set_shape_text(shape_by_id(prs.slides[n - 1], title_shape_ids[n]), title, 22, PPT_NAVY, True)

    set_shape_text(shape_by_id(prs.slides[1], 2), "Project Direction and Current Scope", 24, PPT_NAVY, True)
    set_shape_text(shape_by_id(prs.slides[1], 3), "The project direction has been narrowed from general cloud remediation to a reproducible research study.\n\nScope now includes:\n- real CloudTrail drift observation\n- SHAP-guided diagnosis\n- protected adaptation evaluation\n- external transfer checking\n\nThe primary corpus is unlabeled, so real-data results are observational.", 17)

    set_shape_text(shape_by_id(prs.slides[2], 3), "To develop and evaluate a label-free drift diagnosis protocol that combines feature-distribution drift with SHAP-attribution drift, so an unsupervised AWS CloudTrail detector can adapt selectively without treating every behavioural change as a security incident.", 20)

    set_shape_text(shape_by_id(prs.slides[3], 3), "Cloud behaviour changes over time because of new services, regions, identities, and automation.\n\nThis project studies whether feature drift and SHAP-attribution drift provide complementary evidence for deciding when adaptation is justified.\n\nDataset: 1,939,207 records | 45 monthly windows | no attack labels\n\nEvaluation: controlled semi-synthetic benchmark plus independent temporal checkpoint.", 18)

    set_shape_text(shape_by_id(prs.slides[4], 4), "Literature Review", 22, PPT_NAVY, True)
    # Slide 5 has no content placeholder in the source, so use the open body area.
    add_ppt_text(prs.slides[4], "Established building blocks\n\n• Isolation Forest for unsupervised anomaly scoring\n• SHAP for model-level feature attribution\n• Unlabeled drift detection and normality shift\n• Drift-type-aware and selective adaptation\n• CloudTrail and security monitoring\n\nClosest gap\nExisting work does not establish a CloudTrail-specific evaluation of whether changed features are also driving changed detector attributions before adaptation.", 0.95, 1.65, 11.2, 4.8, 18)

    set_shape_text(shape_by_id(prs.slides[5], 3), "A feature alarm only tells us that the observed distribution changed. It does not tell us whether the detector's decision logic changed in a security-relevant way.\n\nContribution:\n1. CloudTrail-specific real-data drift protocol\n2. Explicit separation of observational and controlled evidence\n3. Attribution-feature coupling score\n4. Protected adaptation and unnecessary-adaptation measurement\n5. Label-free transfer calibration, reported separately from source-tuned thresholds", 17)

    set_shape_text(shape_by_id(prs.slides[6], 3), "1. Audit the real corpus and its temporal limitations.\n2. Build a chronological 27 / 9 / 9 train-validation-test protocol.\n3. Validate Isolation Forest and TreeSHAP behaviour.\n4. Measure feature drift, SHAP drift, and coupling.\n5. Compare static, periodic, feature-only, SHAP-only, dual, and coupled policies.\n6. Report robustness, uncertainty, external transfer, and limitations.\n\nSDG relevance: SDG 9 (resilient digital infrastructure) and SDG 16 (secure institutions).\nOutcome: capstone research prototype, report, reproducible code, and journal-ready evidence package.", 16)

    set_shape_text(shape_by_id(prs.slides[7], 3), "Source audit\n      ↓\nMonthly windows and train-only encoding\n      ↓\nIsolation Forest anomaly scores\n      ↓\nTreeSHAP attribution distributions\n      ↓\nFeature drift + SHAP drift + coupling\n      ↓\nDiagnosis: stable / benign / security-relevant / review\n      ↓\nProtected adaptation simulation\n      ↓\nMetrics, uncertainty, and reporting", 18)

    set_shape_text(shape_by_id(prs.slides[8], 3), "Functional\n• Read-only dataset audit and manifest\n• Chronological temporal split\n• Train-only feature encoding\n• Isolation Forest scoring\n• SHAP additivity validation\n• Feature, SHAP, and coupling drift\n• Validation-only threshold tuning\n• Protected retraining comparison\n\nSafety and research constraints\n• No attack labels used by the detector\n• No production AWS/IAM enforcement\n• Real-data claims remain observational", 16)

    set_shape_text(shape_by_id(prs.slides[9], 3), "1. Dataset audit and temporal protocol\n2. Event feature representation\n3. Isolation Forest baseline\n4. SHAP explanation validation\n5. Feature and attribution drift monitoring\n6. Attribution-feature coupling\n7. Controlled diagnosis benchmark\n8. Protected adaptation controller\n9. Robustness and cost sensitivity\n10. Independent external validation\n11. Reproducible reports and artifacts", 18)

    body = shape_by_id(prs.slides[10], 3)
    body.text_frame.clear()
    body.left = PptInches(0.55)
    body.top = PptInches(1.85)
    body.width = PptInches(6.8)
    body.height = PptInches(4.45)
    add_ppt_picture(prs.slides[10], ROOT / "figures" / "adaptation_policy_comparison.png", 0.7, 1.95, 6.1, 3.75)
    add_ppt_text(prs.slides[10], "Verified results\n\nControlled diagnosis macro-F1: 0.7306\nDual vs static FPR difference: -0.0885\nDual vs static F1 difference: -0.0028\nUnnecessary adaptation: 0.0000\n\nCoupling was neutral in the controlled benchmark. Source-tuned external coupling had F1 0.1818; label-free largest-gap calibration reached F1 1.0000 on the small 12-window checkpoint.", 7.15, 1.85, 5.45, 4.5, 15)

    set_shape_text(shape_by_id(prs.slides[11], 3), "Conclusion\nThe project demonstrates a reproducible way to separate real-data drift observation from controlled diagnosis and adaptation evidence. Feature and attribution signals reduce unnecessary retraining in the defined benchmark, but the coupling extension is not universally superior.\n\nFuture work\n• Multi-period external temporal validation\n• Larger and more diverse perturbation families\n• Independent post-adaptation recovery evaluation\n• Human completion of PRISMA screening and risk-of-bias assessment\n• Supervisor review and venue-specific formatting", 17)

    set_shape_text(shape_by_id(prs.slides[12], 2), "Outcome Achieved", 24, PPT_NAVY, True)
    set_shape_text(shape_by_id(prs.slides[12], 3), "Completed technical outcome\n• Reproducible CloudTrail drift-diagnosis pipeline\n• Isolation Forest + TreeSHAP validation\n• Attribution-feature coupling implementation\n• Controlled benchmark and adaptation comparison\n• Independent detector and temporal transfer checks\n• 28 automated tests passing\n• Research report, literature matrix, and GitHub repository\n\nJournal outcome status\nA research prototype and manuscript-ready evidence package are complete. Q1/Q2 acceptance is not guaranteed; human PRISMA review and stronger independent validation remain.", 17)

    set_shape_text(shape_by_id(prs.slides[13], 2), "[1] Liu, Ting and Zhou, \"Isolation Forest,\" IEEE ICDM, 2008.\n[2] Lundberg and Lee, \"A unified approach to interpreting model predictions,\" NeurIPS, 2017.\n[3] Sethi and Kantardzic, \"Reliable detection of concept drift from streaming unlabeled data,\" ESWA, 2017.\n[4] Kuppa and Le-Khac, \"Learn to adapt: Robust drift detection in security domain,\" CEE, 2022.\n[5] Han et al., \"Anomaly detection in the open world: Normality shift detection, explanation and adaptation,\" NDSS, 2023.\n[6] Lee et al., \"Explainable AI-based model drift detection,\" CMC, 2023.\n[7] Varma and Ramya, \"Explainable ML for AWS CloudTrail logs,\" ICNGN, 2025.\n[8] AWS, CloudTrail and feature attribution drift documentation.\n\nFull references and verification links are included in the report and repository.", 15)

    # Remove inherited content placeholders after copying their edited text
    # into ordinary text boxes. This prevents default layout text from
    # resurfacing during PowerPoint PDF export.
    for n in [2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13]:
        slide = prs.slides[n - 1]
        body = next((s for s in slide.shapes if s.shape_id == 3), None)
        if body is None:
            continue
        text = body.text
        x, y, w, h = body.left, body.top, body.width, body.height
        remove_shape(body)
        box = slide.shapes.add_textbox(x, y, w, h)
        set_shape_text(box, text, 17 if n not in {3, 4} else 18)
    old_sdg = next((s for s in prs.slides[6].shapes if s.shape_id == 7), None)
    if old_sdg is not None:
        remove_shape(old_sdg)
    for slide_index, shape_id in [(1, 7), (4, 7)]:
        old_picture = next((s for s in prs.slides[slide_index].shapes if s.shape_id == shape_id), None)
        if old_picture is not None:
            remove_shape(old_picture)

    prs.save(str(PPT_OUT))
    return PPT_OUT


if __name__ == "__main__":
    print(build_report())
    print(build_presentation())
