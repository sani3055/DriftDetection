"""Build the guide-required Word submission documents and numbered project folder."""

from __future__ import annotations

import csv
from pathlib import Path
import shutil

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "review_2022_2026"
PROJECT_NAME = "Project_XX_SHAP_CloudTrail_Drift"
PACKAGE = ROOT / PROJECT_NAME


def shade(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_text(cell, text: str, bold: bool = False, size: int = 8) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(0)
    run = paragraph.add_run(str(text or ""))
    run.bold = bold
    run.font.size = Pt(size)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP


def style_document(document: Document) -> None:
    styles = document.styles
    styles["Normal"].font.name = "Arial"
    styles["Normal"].font.size = Pt(10)
    for name, size, color in [("Title", 24, "17365D"), ("Heading 1", 16, "17365D"), ("Heading 2", 12, "2F5597")]:
        style = styles[name]
        style.font.name = "Arial"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)
    section = document.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)


def add_title(document: Document, title: str, subtitle: str) -> None:
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(title).bold = True
    p.runs[0].font.size = Pt(24)
    p.runs[0].font.color.rgb = RGBColor(23, 54, 93)
    p2 = document.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p2.add_run(subtitle)
    r.font.size = Pt(12)
    r.font.color.rgb = RGBColor(89, 89, 89)
    document.add_paragraph()


def add_bullets(document: Document, items: list[str]) -> None:
    for item in items:
        p = document.add_paragraph(style="List Bullet")
        p.add_run(item)


def add_matrix_table(document: Document, rows: list[dict]) -> None:
    section = document.add_section()
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = section.page_height, section.page_width
    section.left_margin = Inches(0.35)
    section.right_margin = Inches(0.35)
    document.add_heading("Consolidated evidence matrix: 100 records", level=1)
    headers = ["ID", "Year", "Title", "Journal", "DOI", "Topic evidence", "Full-text status"]
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = False
    widths = [0.45, 0.45, 3.0, 1.65, 1.75, 2.5, 1.0]
    for idx, header in enumerate(headers):
        cell = table.rows[0].cells[idx]
        set_cell_text(cell, header, bold=True, size=8)
        shade(cell, "D9EAF7")
        cell.width = Inches(widths[idx])
    for row in rows:
        cells = table.add_row().cells
        values = [
            row.get("paper_id"),
            row.get("publication_year"),
            row.get("title"),
            row.get("journal"),
            row.get("doi"),
            row.get("matched_topic_groups"),
            row.get("full_text_status"),
        ]
        for idx, value in enumerate(values):
            set_cell_text(cells[idx], value, size=7)
            cells[idx].width = Inches(widths[idx])


def build_review(rows: list[dict]) -> Path:
    document = Document()
    style_document(document)
    add_title(document, "Systematic Review Evidence Package", "SHAP-Guided Drift Diagnosis for Adaptive AWS CloudTrail Anomaly Detection")
    document.add_paragraph("Prepared for capstone/IDP journal-outcome review. Project folder placeholder: Project_XX. Replace XX with the assigned project number before submission.")
    document.add_heading("Executive summary", level=1)
    document.add_paragraph("This document consolidates the 100-record 2022–2026 journal-paper evidence set collected for the project. The set was identified through reproducible metadata searches using the logged OpenAlex/Crossref workflow. It is an automated initial screen, not a completed two-reviewer systematic review.")
    document.add_heading("Review question", level=1)
    document.add_paragraph("What methods published from 2022–2026 use machine learning, anomaly detection, explainability, drift detection, or adaptive learning for cloud/audit-log and cybersecurity monitoring, and what evidence supports SHAP-guided drift diagnosis for adaptive CloudTrail anomaly detection?")
    document.add_heading("Search and screening summary", level=1)
    add_bullets(document, [
        "Search source: logged OpenAlex/Crossref workflow with 12 reproducible queries; the current log records the API used for each query.",
        "Publication window: 2022–2026; journal-article records with DOI; retracted records removed.",
        "Records retrieved: 2,400; unique DOI values: 1,898; automated eligible candidate hits: 1,246; retained evidence set: 100.",
        "Open-access PDFs downloaded: 12. Paywalled or unavailable papers are represented by DOI and metadata only.",
        "All 100 records require human title/abstract and full-text confirmation by two reviewers before final PRISMA submission.",
    ])
    document.add_heading("Evidence synthesis themes", level=1)
    add_bullets(document, [
        "Explainable intrusion detection: SHAP, feature importance, counterfactuals, and interpretable deep models.",
        "Drift and adaptation: concept drift detection, incremental learning, dynamic thresholds, and adaptive security monitoring.",
        "Cloud and audit logs: CloudTrail, cloud API traffic, log anomaly detection, and cloud security analytics.",
        "Adjacent methods: IoT, industrial control, network intrusion, and distributed log monitoring that inform the proposed protocol.",
    ])
    document.add_heading("Important status note", level=1)
    document.add_paragraph("The matrix is intentionally transparent about its automated status. It must not be described as PRISMA-complete until two reviewers complete independent screening, full-text eligibility, study-level extraction, risk-of-bias assessment, and final flow counts.")
    add_matrix_table(document, rows)
    document.add_heading("Reference package files", level=1)
    add_bullets(document, [
        "evidence_matrix_100.csv — machine-readable extraction table",
        "screening_log_100.csv — automated screening log requiring human confirmation",
        "PRISMA_protocol.md — eligibility, sources, search, extraction, synthesis, and bias plan",
        "PRISMA_flow.md — auditable automated retrieval counts",
        "Downloaded_Papers — legally retrieved open-access PDFs only",
    ])
    path = PACKAGE / "Final_Consolidated_100_Paper_Summary.docx"
    path.parent.mkdir(parents=True, exist_ok=True)
    document.save(path)
    return path


def build_report() -> Path:
    document = Document()
    style_document(document)
    add_title(document, "Project Report Draft", "SHAP-Guided Drift Diagnosis for Adaptive Anomaly Detection in AWS CloudTrail")
    document.add_paragraph("Project number: XX (replace with assigned number) | Working target: IEEE Transactions on Cloud Computing (Q1 in attached 2023 JCR list)")
    sections = [
        ("1. Abstract", "This project evaluates whether feature-distribution drift and SHAP-attribution drift provide complementary evidence for deciding when an unsupervised AWS CloudTrail anomaly detector should be adapted. The primary corpus contains 1,939,207 unlabeled records across 45 monthly windows. A controlled semi-synthetic benchmark provides labelled benign and security-relevant perturbations. The project includes Isolation Forest detection, SHAP validation, drift monitoring, protected adaptation, detector/window ablations, uncertainty estimates, and detector-only external validation on a separate labelled CloudTrail corpus."),
        ("2. Problem statement", "Cloud audit behavior changes over time because of legitimate service growth, region changes, automation, and identity changes. A detector that never adapts may become stale; indiscriminate retraining can absorb contamination. The project therefore studies attribution-aware drift diagnosis as an adaptation gate."),
        ("3. Objectives", "(i) quantify monthly feature and attribution drift; (ii) compare feature-only, SHAP-only, periodic, static, and dual-signal adaptation; (iii) evaluate controlled benign/security perturbations; (iv) test detector and sample-size robustness; and (v) document a reproducible protocol suitable for journal review."),
        ("4. Methodology", "The pipeline uses chronological train/validation/test partitions, training-only categorical maps, an Isolation Forest baseline, TreeSHAP explanation checks, feature and attribution drift metrics, validation-tuned diagnosis thresholds, protected retraining, paired statistical inference, detector/window ablations, and a separate external detector plus temporal-diagnosis track."),
        ("5. Results", "The controlled diagnosis benchmark achieved validation macro-F1 0.7306. In the adaptation comparison, dual-signal gating reduced false-positive rate relative to static adaptation by a paired mean difference of -0.0885 with Benjamini–Hochberg adjusted q=0.00043; its F1 difference was -0.0028 with a 95% bootstrap interval of [-0.0181, 0.0112]. On the independent labeled CloudTrail corpus, Isolation Forest achieved recall 0.7137, F1 0.4519, and false-positive rate 0.1738. These are protocol-specific results, not claims of production security effectiveness."),
        ("6. Novelty and contribution", "The defensible novelty is the CloudTrail-specific evaluation protocol: real unlabeled monthly observation, controlled labelled perturbations, attribution-aware diagnosis, protected adaptation, and explicit unnecessary-adaptation measurement. The paper must not claim that SHAP drift, Isolation Forest, or drift detection was invented here."),
        ("7. Limitations", "The primary corpus is unlabeled and concentrated in a small number of months/event types. The controlled benchmark is semi-synthetic. Ordinal categorical encoding may impose artificial geometry. The external temporal checkpoint is coarse, scenario-window based, and neutral across policies; full post-adaptation recovery and analyst-confirmed incident validation remain future work."),
        ("8. Journal outcome plan", "Working target: IEEE Transactions on Cloud Computing. Practical alternatives: Journal of Cloud Computing and Journal of Information Security and Applications. IEEE Transactions on Dependable and Secure Computing is a stretch target. Computers & Security is not the default target because its current official scope warns of an AI/ML moratorium. Quartiles are from the attached 2023 JCR workbook and must be rechecked before submission."),
        ("9. Submission readiness", "Technical implementation: ready for demonstration. Research manuscript: strong draft, but requires supervisor review, final human PRISMA screening, full-text extraction, risk-of-bias assessment, current journal verification, and final formatting."),
    ]
    for heading, body in sections:
        document.add_heading(heading, level=1)
        document.add_paragraph(body)
    path = PACKAGE / "Project_Report_Draft.docx"
    path.parent.mkdir(parents=True, exist_ok=True)
    document.save(path)
    return path


def build_package(rows: list[dict]) -> None:
    PACKAGE.mkdir(parents=True, exist_ok=True)
    papers_source = REVIEW / PROJECT_NAME / "Downloaded_Papers"
    papers_target = PACKAGE / "Downloaded_Papers"
    papers_target.mkdir(parents=True, exist_ok=True)
    for source in papers_source.glob("*.pdf"):
        shutil.copy2(source, papers_target / source.name)
    for source_name in ["evidence_matrix_100.csv", "screening_log_100.csv", "automated_quality_audit_100.csv", "search_log.json", "collection_manifest.json", "PRISMA_protocol.md", "PRISMA_flow.md", "screening_instructions.md"]:
        source = REVIEW / source_name
        if source.is_file():
            shutil.copy2(source, PACKAGE / source.name)
    for source in [
        ROOT / "journal_targets.md",
        ROOT / "docs" / "research_gap.md",
        ROOT / "docs" / "literature_review.md",
        ROOT / "docs" / "external_validation.md",
        ROOT / "docs" / "final_validation.md",
        ROOT / "docs" / "next_experiments.md",
        ROOT / "docs" / "cost_sensitivity.md",
        ROOT / "IMPLEMENTATION_PLAN.md",
    ]:
        if source.is_file():
            shutil.copy2(source, PACKAGE / source.name)
    presentation = ROOT / "Project_XX_SHAP_CloudTrail_Drift" / "Presentation" / "Capstone_IDP_Progress_Presentation.pptx"
    if presentation.is_file():
        shutil.copy2(presentation, PACKAGE / presentation.name)
    (PACKAGE / "PACKAGE_README.txt").write_text(
        "Project_XX is a placeholder because the assigned project number was not found in the workspace. Rename this folder before sending.\n"
        "Downloaded_Papers contains legally accessible open-access PDFs only. Twelve PDFs are linked to records in the 100-paper matrix; any supplementary files must be mapped before review claims are made. Do not add paywalled PDFs obtained by bypassing access controls.\n"
        "The 100-paper matrix is an automated initial screen and requires two-reviewer confirmation before being called PRISMA-complete.\n"
        "The external temporal checkpoint is a neutral scenario-window diagnosis result, not full adaptation-recovery validation.\n",
        encoding="utf-8",
    )


def main() -> None:
    with (REVIEW / "evidence_matrix_100.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    build_package(rows)
    review_path = build_review(rows)
    report_path = build_report()
    print(review_path)
    print(report_path)


if __name__ == "__main__":
    main()
