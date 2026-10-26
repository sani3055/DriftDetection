# Tomorrow's project-review speaking guide

## Recommended format

Use the existing 8-slide presentation for a 7-10 minute review. Spend roughly 45-60 seconds on
each slide and reserve the final 2-3 minutes for questions. Do not run the full 1.94-million-record
pipeline live; use the saved outputs and the package validator.

## Opening statement (memorize this)

> This project studies whether feature-distribution drift and SHAP-attribution drift can provide
> complementary evidence for deciding when an unsupervised AWS CloudTrail anomaly detector should
> adapt. Because the primary CloudTrail-style corpus has no attack labels, we separate observational
> real-data drift analysis from a controlled labelled perturbation benchmark.

## Slide-by-slide script

### Slide 1 - Title

Introduce the topic, team, and objective. Say that the project is a research prototype with a
reproducible evaluation package, not a claim of production deployment.

### Slide 2 - Problem

Explain that feature drift means the observed activity changed, while attribution drift means the
detector relies on features differently. The research question is whether both signals can reduce
unnecessary adaptation while preserving sensitivity to controlled security changes.

### Slide 3 - Study design

Emphasize the two evidence tracks:

- real corpus: 1,939,207 records, 45 monthly windows, no attack labels;
- controlled benchmark: labelled benign and security-relevant perturbations evaluated without
  exposing labels to the detector or adaptation controller.

This separation is one of the project's most important research-integrity decisions.

### Slide 4 - Data and protocol

State the chronological split: 27 training months, 9 validation months, and 9 held-out test
months. Thresholds are selected using validation data, not held-out test labels.

### Slide 5 - Method

Walk through: train-only encoding, Isolation Forest, TreeSHAP, feature drift, attribution drift,
diagnosis, and protected retraining. Suspicious windows are not blindly added to the training set.

### Slide 6 - Main result

Do not claim universal F1 improvement. Say:

> In the controlled benchmark, dual-signal adaptation reduced false-positive rate relative to the
> static policy by 0.0885, while the F1 difference was -0.0028 with a confidence interval crossing
> zero. The practical benefit is reduced unnecessary adaptation, not guaranteed F1 improvement.

### Slide 7 - Robustness and external checkpoint

Explain that detector choice and window size materially affect results. The external temporal
checkpoint was neutral: feature-only, SHAP-only, and dual policies each achieved F1 0.9524 and FPR
0.5000 at the scenario-window level. Present this as a limitation and falsification result, not as
evidence that the proposed policy always wins.

### Slide 8 - Readiness

State that the implementation, results, report, presentation, and submission package are ready.
Clearly say that the 100-paper set is automated triage and still requires human PRISMA screening;
do not call it a completed systematic review.

## Safe live demonstration

If a demo is required, use this short sequence:

```text
1. Open the GitHub repository and show README.md.
2. Open docs/manuscript_draft.md or Project_Report_Draft.docx.
3. Run: .venv\Scripts\python.exe scripts\validate_submission_package.py
4. Show the output: 100 matrix records, readable DOCX/PPTX, external metrics present, valid=true.
5. Open the presentation and one results figure.
```

Do not download papers, run the full pipeline, or depend on internet access during the review.

## Likely questions and answers

**What is the novelty?**

The novelty is a CloudTrail-specific, reproducible protocol that combines feature drift and
attribution drift for protected, cost-aware adaptation evaluation. SHAP, Isolation Forest, and
concept drift are established methods and are not claimed as inventions here.

**Does the real dataset contain attack labels?**

No. It is an unlabeled observational corpus. Attack-recall claims are restricted to the controlled
labelled benchmark and the separate labelled external corpus.

**Why use synthetic perturbations?**

They provide controlled labels while preserving the base data distribution. The manuscript labels
them semi-synthetic and does not present them as real incidents.

**Why did the external temporal checkpoint not show a dual-signal advantage?**

It is a useful neutral result. It shows that attribution drift does not automatically add decision
value at every evaluation granularity and prevents overclaiming generality.

**How was leakage controlled?**

Chronological splits were used; category maps and thresholds were fitted on training/validation
data; scenario labels were used only for evaluation; suspicious windows were quarantined from
protected retraining.

**Is this ready for a Q1/Q2 journal?**

It is a strong reproducible prototype and manuscript foundation, but Q1/Q2 acceptance is not
guaranteed. The main remaining research gaps are final PRISMA screening and stronger independent
post-adaptation temporal validation.

## Do not say these claims

- “This is the first use of SHAP for drift detection.”
- “The real CloudTrail data contains confirmed attacks.”
- “Dual-signal adaptation always improves F1.”
- “The systematic review is PRISMA-complete.”
- “Q1/Q2 publication is guaranteed.”

## Final preparation checklist

- Replace `Project_XX` with the assigned project number if required.
- Add team-member names, guide name, department, and institution to the title slide.
- Keep the demo folder and repository available offline.
- Run the package validator once before leaving for the review.
- Practice the opening statement and the novelty answer aloud.
- Keep the limitations visible; honest limitations make the evaluation more credible.
