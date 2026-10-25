"""Build the project progress presentation without requiring PowerPoint COM."""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "Project_XX_SHAP_CloudTrail_Drift" / "Presentation"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / "Capstone_IDP_Progress_Presentation.pptx"

NAVY = RGBColor(0x17, 0x36, 0x5D)
BLUE = RGBColor(0x2F, 0x6A, 0xB8)
TEAL = RGBColor(0x26, 0x7C, 0xA4)
LIGHT = RGBColor(0xFC, 0xF9, 0xF7)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK = RGBColor(0x37, 0x29, 0x1F)
MUTED = RGBColor(0x70, 0x68, 0x66)
PALE_BLUE = RGBColor(0xF8, 0xF1, 0xE8)
PALE_TEAL = RGBColor(0xF4, 0xF6, 0xEA)
PALE_AMBER = RGBColor(0xE5, 0xF4, 0xFF)
LINE = RGBColor(0xEC, 0xE2, 0xD9)


def add_text(slide, text, x, y, w, h, size=18, bold=False, color=DARK,
             align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(0.05)
    tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = MSO_ANCHOR.TOP
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = 1.05
    runs = text.split("\n")
    for index, line in enumerate(runs):
        if index:
            p = tf.add_paragraph()
            p.alignment = align
            p.line_spacing = 1.05
        run = p.add_run()
        run.text = line
        run.font.name = "Arial"
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color
    return box


def add_rect(slide, x, y, w, h, fill, line=LINE, rounded=True):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = line
    shape.line.width = Pt(0.8)
    return shape


def add_footer(slide, text="Source: project artifacts | Status: research prototype and submission package"):
    add_text(slide, text, 0.5, 7.11, 9.0, 0.2, 8, False, MUTED)


def add_title(slide, title, eyebrow="SHAP-GUIDED CLOUDTRAIL DRIFT DIAGNOSIS"):
    add_text(slide, eyebrow, 0.5, 0.25, 9.0, 0.25, 10, True, TEAL)
    add_text(slide, title, 0.5, 0.62, 9.0, 0.55, 25, True, NAVY)


def add_image(slide, path, x, y, w, h):
    if path.exists():
        slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))


def new_slide(prs, background):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = background
    return slide


def main():
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    # 1. Title
    slide = new_slide(prs, LIGHT)
    add_rect(slide, 0, 0, 0.18, 7.5, TEAL, TEAL, False)
    add_text(slide, "CAPSTONE / IDP JOURNAL OUTCOME", 0.75, 1.05, 8.5, 0.3, 13, True, TEAL)
    add_text(slide, "SHAP-Guided Drift Diagnosis\nfor Adaptive AWS CloudTrail Anomaly Detection", 0.75, 1.72, 8.4, 1.45, 30, True, NAVY)
    add_text(slide, "Research implementation, PRISMA evidence package, and Q1/Q2 journal plan", 0.77, 3.8, 8, 0.5, 17, False, MUTED)
    add_text(slide, "Project folder placeholder: Project_XX - replace XX with assigned number", 0.77, 5.45, 7.8, 0.3, 11, False, DARK)
    add_footer(slide, "Prepared for supervisor progress review | 21 October 2026")

    # 2. Problem
    slide = new_slide(prs, WHITE)
    add_title(slide, "The research problem is deciding when to adapt")
    add_text(slide, "Cloud activity changes for legitimate reasons: new services, regions, identities, and automation. A feature alarm alone cannot tell us whether the detector should be retrained.", 0.6, 1.82, 4.9, 1.0, 17)
    for y, fill, line, heading, body, color in [
        (1.75, PALE_BLUE, RGBColor(0xE0, 0xD4, 0xC8), "Feature drift", "The observed records changed", NAVY),
        (3.1, PALE_TEAL, RGBColor(0xD8, 0xE4, 0xD2), "Attribution drift", "The detector relies differently", TEAL),
        (4.45, PALE_AMBER, RGBColor(0xD4, 0xE2, 0xF0), "Adaptation gate", "Retrain only with evidence", BLUE),
    ]:
        add_rect(slide, 6.15, y, 3.05, 0.98, fill, line)
        add_text(slide, heading, 6.35, y + 0.18, 2.6, 0.3, 18, True, color)
        add_text(slide, body, 6.35, y + 0.56, 2.6, 0.25, 12, False, MUTED)
    add_text(slide, "Research question: does combining feature drift with SHAP-attribution drift reduce unnecessary adaptation without losing controlled security sensitivity?", 0.6, 4.7, 5.0, 1.0, 17, True, NAVY)
    add_footer(slide)

    # 3. Study design
    slide = new_slide(prs, LIGHT)
    add_title(slide, "The study separates observation from labelled evaluation")
    add_rect(slide, 0.6, 1.85, 4.0, 3.45, PALE_BLUE)
    add_text(slide, "TRACK A - REAL CORPUS", 0.85, 2.15, 3.5, 0.3, 15, True, NAVY)
    add_text(slide, "- 1,939,207 CloudTrail-style records\n- 45 chronological monthly windows\n- feature and SHAP drift timelines\n- no attack labels -> observational claims only", 0.85, 2.7, 3.45, 1.9, 16)
    add_rect(slide, 5.4, 1.85, 4.0, 3.45, PALE_TEAL)
    add_text(slide, "TRACK B - CONTROLLED BENCHMARK", 5.65, 2.15, 3.5, 0.3, 15, True, TEAL)
    add_text(slide, "- semantic benign/security perturbations\n- validation-tuned thresholds\n- held-out seeds and scenarios\n- diagnosis and adaptation metrics", 5.65, 2.7, 3.45, 1.9, 16)
    add_footer(slide, "Source: data_manifest/real_cloudtrail_manifest.json; data/benchmark/*")

    # 4. Data and method
    slide = new_slide(prs, WHITE)
    add_title(slide, "The real corpus is large, but the protocol respects its limits")
    metrics = [("1.94M", "records"), ("45", "months"), ("18", "columns"), ("0", "attack labels")]
    for i, (value, label) in enumerate(metrics):
        x = 0.6 + i * 2.17
        add_rect(slide, x, 1.8, 1.88, 1.4, LIGHT)
        add_text(slide, value, x, 2.05, 1.88, 0.42, 22, True, NAVY, PP_ALIGN.CENTER)
        add_text(slide, label, x, 2.55, 1.88, 0.25, 12, False, MUTED, PP_ALIGN.CENTER)
    add_text(slide, "Chronological protocol", 0.6, 4.0, 3.0, 0.3, 17, True, TEAL)
    add_text(slide, "27 train months  ->  9 validation months  ->  9 held-out test months", 0.6, 4.55, 8.4, 0.4, 17)
    add_text(slide, "The richer raw export confirms day/hour timestamps exist, but it is the same underlying corpus - not independent validation.", 0.6, 5.45, 8.4, 0.6, 13, False, MUTED)
    add_footer(slide)

    # 5. Pipeline
    slide = new_slide(prs, LIGHT)
    add_title(slide, "Dual-signal diagnosis gates protected adaptation")
    steps = [("1", "Encode", "Train-only category maps"), ("2", "Detect", "Isolation Forest anomaly score"), ("3", "Explain", "TreeSHAP attribution vectors"), ("4", "Monitor", "Feature + attribution drift"), ("5", "Adapt", "Replay + normal-candidate retraining")]
    for i, (number, heading, body) in enumerate(steps):
        x = 0.42 + i * 1.89
        add_rect(slide, x, 2.3, 1.66, 1.95, WHITE)
        add_text(slide, number, x + 0.13, 2.5, 0.35, 0.35, 20, True, TEAL)
        add_text(slide, heading, x + 0.13, 3.0, 1.4, 0.3, 16, True, NAVY)
        add_text(slide, body, x + 0.13, 3.55, 1.38, 0.55, 11, False, MUTED)
    add_text(slide, "Stable -> benign drift -> security-relevant drift -> review required", 0.85, 5.45, 8.3, 0.35, 18, True, BLUE, PP_ALIGN.CENTER)
    add_footer(slide)

    # 6. Results
    slide = new_slide(prs, WHITE)
    add_title(slide, "The benchmark shows lower unnecessary adaptation, not universal F1 gains")
    add_image(slide, ROOT / "figures" / "adaptation_policy_comparison.png", 0.55, 1.8, 5.5, 3.35)
    add_rect(slide, 6.5, 1.95, 3.0, 2.95, LIGHT)
    add_text(slide, "Measured result", 6.75, 2.25, 2.5, 0.3, 16, True, TEAL)
    add_text(slide, "Dual-signal vs static:\n\nF1 difference\n-0.0028\n\nFalse-positive-rate difference\n-0.0885\n\nBH-adjusted q = 0.00043", 6.75, 2.75, 2.4, 1.8, 15)
    add_footer(slide, "Source: results/paired_inference.csv; semi-synthetic benchmark only")

    # 7. Robustness
    slide = new_slide(prs, LIGHT)
    add_title(slide, "Ablations expose detector and window-size sensitivity")
    add_text(slide, "Independent labelled CloudTrail validation", 0.6, 1.8, 4.5, 0.3, 17, True, NAVY)
    add_text(slide, "Isolation Forest: recall 0.7137 | F1 0.4519 | FPR 0.1738\nLOF: recall 0.9954 | F1 0.5334 | FPR 0.2088\nOne-Class SVM: recall 0.0008 | F1 0.0015 | FPR 0.0042\nExternal temporal checkpoint: all policies F1 0.9524; FPR 0.5000", 0.6, 2.35, 5.1, 1.65, 13)
    add_text(slide, "Window-size ablation", 0.6, 4.45, 3.0, 0.3, 17, True, TEAL)
    add_text(slide, "Security recall: 100 rows = 0.0884\n200 rows = 0.4918\n500 rows = 0.4152", 0.6, 5.0, 3.7, 1.0, 14)
    add_image(slide, ROOT / "figures" / "diagnosis_confusion_matrix.png", 6.25, 1.9, 3.0, 3.2)
    add_footer(slide, "Source: data/robustness/*; data/external_validation/*")

    # 8. Submission package
    slide = new_slide(prs, WHITE)
    add_title(slide, "The submission package is prepared; four actions remain")
    add_rect(slide, 0.6, 1.8, 4.1, 3.5, PALE_TEAL)
    add_text(slide, "READY NOW", 0.88, 2.12, 3.3, 0.3, 16, True, TEAL)
    add_text(slide, "[OK] Working implementation and results\n[OK] 100-record 2022-2026 evidence set\n[OK] PRISMA protocol and flow accounting\n[OK] Consolidated Word review\n[OK] Project report draft\n[OK] Presentation and journal shortlist", 0.88, 2.65, 3.5, 2.25, 14)
    add_rect(slide, 5.4, 1.8, 4.0, 3.5, PALE_AMBER)
    add_text(slide, "MANUAL BEFORE SENDING", 5.68, 2.12, 3.4, 0.3, 16, True, BLUE)
    add_text(slide, "1. Replace Project_XX with assigned number\n2. Two-reviewer title/abstract/full-text screening\n3. Recheck current Q1/Q2 status and author guidelines\n4. Supervisor/team review and Google Drive upload", 5.68, 2.65, 3.35, 2.2, 14)
    add_text(slide, "Working target: IEEE Transactions on Cloud Computing (Q1 in the attached 2023 JCR list)", 0.6, 6.2, 8.8, 0.3, 14, True, NAVY)
    add_footer(slide, "The package is transparent about what is complete and what still requires human confirmation.")

    prs.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
