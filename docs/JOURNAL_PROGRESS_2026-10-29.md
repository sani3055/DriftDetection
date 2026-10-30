# Journal and review paper progress

## Scope

Only the experimental paper and review paper were worked on in this phase.
No presentation was created or changed. Sole author requested: Sanidhya Bhandari.
The project number is unknown; no number, email, author approval, submission or
acceptance has been invented. The guide's stated capstone deadline is 3 November.

## Experimental paper

- Revised manuscript: `outputs/SHAP_CloudTrail_Journal_Paper_v2.docx`.
- New code: `src/experiments/journal_protocol.py` and
  `scripts/run_journal_temporal.py`.
- Primary evidence: `results/journal_v2/w128_q0.95_s42/`.
- Six additional settings cover 64/256 events, seeds 17/73 and quantiles .90/.99.
- Native timestamps, event-ID deduplication, training-only maps, earlier benign
  calibration, seven-feature monitoring, corrected feature-aligned SHAP ranks,
  matched 100-tree refits and prediction-before-update are implemented.
- All seven policies process identical windows. Labels enter evaluation only,
  apart from file-integrity and benign-training checks. No attack-name grouping.
- The suite passes 59 tests with the Windows temporary-directory permissions
  resolved. A sandbox-only run failed on temporary-folder access, not assertions.
- Legacy files/results and the previous journal manuscript are preserved.

The new evidence does NOT establish an adaptation improvement. At the primary
setting, static recall/FPR are .9485/.7187; dual recall/FPR are .7735/.6651 and F1
falls from .4888 to .4343. Coupling requests no updates in every setting. A high
static FPR, imperfect representation, candidate contamination and unportable
calibration remain problems. A stronger scientific protocol is not the same as
better detector performance. This remains a draft, not a Q1/Q2 acceptance claim.

## Review paper

- Draft: `outputs/CloudTrail_PRISMA_Review_Working_Draft.docx`.
- Includes proposed review questions, methods, temporal-evidence taxonomy,
  acquisition counts, limitations and a 106-candidate bibliographic register.
- Original 100 candidates plus six directed core journal records.
- Crossref confirms 106 unique DOI identities, journal-article types and reported
  years within 2022--2026. Publication-date bounds establish the 29 October cutoff
  for 105; one record has insufficient date precision. This does not certify venue
  quality, relevance, absence of retraction or full-text eligibility.
- Readable PDFs for 27 candidate records; DOI located on opening pages in 23.
  The other four need explicit file-identity checks.
- Full extracted text, raw DOI responses, download provenance and file hashes are
  in `review_2022_2026/submission_audit/`.
- None of these automated acquisition checks is counted as completed critical
  appraisal or final inclusion. The final 100 full-text summaries are NOT done.
- PRISMA map: `review_2022_2026/submission_audit/PRISMA_completion_map.md` maps all
  42 checklist subitems from the supplied checklist to sections or remaining gaps.
- NotebookLM/SciSpace use and two independent human reviewers are not claimed.

Next work: rebuild an all-record search export; screen by declared scope; obtain
remaining lawful full texts; verify file identity; extract methods/results with
page locations; appraise study validity; synthesise included evidence; produce
real PRISMA selection counts and the consolidated 100-study summary. The author
must verify and approve any eventual submission. PRISMA describes reporting and
does not by itself mandate exactly 100 studies or two human authors/reviewers.

## Venue evidence supplied by the student

`D:/Downloads/JCR IF 2023 (3).xlsx`, Sheet1:

- A2527:I2527: International Journal of Information Security; Q2 in Computer
  Science, Theory & Methods, IF 2.4 in the supplied historical list.
- A2197:I2197: Journal of Information Security and Applications; Q2 in Computer
  Science, Information Systems, IF 3.8 in that list.
- A20525:I20525: IEEE Access; Q2 in Telecommunications, IF 3.4 in that list.

These are 2023-list entries, not verified current JCR classifications. The IJIS
official scope matches information-security implementations, and its author
guidelines require a data-availability statement. Final venue, current category
and year, correspondence email, publication charges and manuscript requirements
must be confirmed. Do not use a historic quartile as current evidence.

Official pages checked:
https://link.springer.com/journal/10207/aims-and-scope
https://link.springer.com/journal/10207/submission-guidelines
https://www.prisma-statement.org/prisma-2020
https://pmc.ncbi.nlm.nih.gov/articles/8005925/

## Reproduction

Use the project virtual environment for experiments:

```powershell
.\.venv\Scripts\python.exe scripts/run_journal_temporal.py
.\.venv\Scripts\python.exe scripts/run_journal_temporal.py --window-size 64
.\.venv\Scripts\python.exe scripts/run_journal_temporal.py --window-size 256
.\.venv\Scripts\python.exe scripts/run_journal_temporal.py --seed 17
.\.venv\Scripts\python.exe scripts/run_journal_temporal.py --seed 73
.\.venv\Scripts\python.exe scripts/run_journal_temporal.py --quantile 0.9
.\.venv\Scripts\python.exe scripts/run_journal_temporal.py --quantile 0.99
.\.venv\Scripts\python.exe -m pytest tests -q
```

Completed result directories deliberately refuse overwriting. Preserve them or
run a reproduction in a separate checkout. Word builders use the Codex bundled
Python and are visually checked through installed Word because bundled soffice
is unavailable. The code, papers and new results are local; no GitHub push or
journal/email/Drive submission was performed in this phase.
