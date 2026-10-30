# Journal work status — 30 October 2026

## Completed locally

- A 14-page journal manuscript draft, with 20 references, 10 tables, an experiment figure and six editable equations, is saved in `outputs/SHAP_CloudTrail_Journal_Paper_v4.docx`. It was rendered with Microsoft Word and its pages visually inspected. Its conclusions retain mixed and negative findings.
- The tie-safe experimental grid covers 60 combinations of input representation, historical coverage, calibration and model seed, with 14 policies in each combination. The same labelled deployment is reused across cells, so these are not 60 independent studies.
- The inherited dataset was studied using 42,513 deduplicated sampled events from a richer timestamped export; it remains unlabelled and is not independent of the original dataset. Separate public trace replay and a synthetic background test add limited cross-source evidence, not verified production attack-detection performance.
- A controlled candidate-contamination stress test and a size-matched synthetic monthly intervention were completed. The automated suite passed 93 tests in the recorded run.
- A locally verified evidence archive with SHA-256 inventory, source code and results is at `outputs/CloudTrail_Journal_Research_Evidence_v4.zip`. It omits raw datasets and fitted models. See `docs/REPRODUCIBILITY_V4.md`.

## Remaining limitations and work

- The strongest missing evidence is an independently labelled CloudTrail environment with representative benign activity, followed by a frozen prospective evaluation and stronger matched baselines. Existing data cannot prove those findings.
- The current coupling rule does not consistently improve the dual-signal rule; high benign alert rates in some configurations and unsafe candidate contamination remain important findings, not issues to hide.
- A target journal, author/corresponding details, verified citations, required statements and journal-specific formatting require completion before submission. The author must review and approve any submission. Q1/Q2 acceptance is not guaranteed.
- The separate systematic review is **not complete**: 392 DOI records from bounded searches and 153 distinct downloaded PDF hashes are discovery resources, not 100 included and critically appraised journal papers. Final screening, eligibility and full-text extraction, a defensible PRISMA flow, synthesis and 100 relevant journal-paper summaries remain to be completed. Some records may be ineligible; source access and use must be lawful. No NotebookLM or SciSpace use, independent human screening, journal submission, or completed review is asserted.
- No submission, email, external sharing or GitHub update is implied by this local package.
