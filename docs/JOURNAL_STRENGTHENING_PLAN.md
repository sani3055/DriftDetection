# Journal strengthening and guide deliverables

Plan locked: 29 October 2026, before the new chronological benchmark was run.
Author requested by the student: Sanidhya Bhandari only. Project number and
corresponding-author email remain unknown. No submission or upload is authorised.

## Outcomes and deadline

The guide requests two distinct manuscripts by 3 November 2026: an experimental
work paper and a review paper. The review requires 100 journal papers dated
2022--2026, a consolidated Word summary and downloaded full texts organised under
the project number. A metadata list is not a completed review. NotebookLM and
SciSpace use must be documented if actually performed, not claimed by inference.

## Audit finding

The existing journal draft accurately reports mostly neutral coupling evidence.
The old controlled benchmark has same-batch adaptation/evaluation, unmatched
100-tree baseline versus 50-tree refit, selected-index rather than actual-change
masks, potentially inconsistent API/service/root scenarios, and partial reuse of
a jointly tuned threshold triple. Its SHAP rank term compares sorted feature-ID
arrays rather than feature-aligned ranks. Old external groups are attack-name
informed. Keep those results as legacy evidence, not as prospective validation.

## Phase A: native chronological external benchmark

Implement an additional, versioned protocol, without overwriting old artifacts:

1. Use the independent ArielCyber raw CloudTrail records and native timestamps.
2. Fit category maps and a 100-tree Isolation Forest only on the earliest 70% of
   the first benign training day; reserve the last 30% of that day as reference.
3. Calibrate feature and SHAP magnitude gates at the empirical 95th percentile
   (`method=higher`) of fixed-size benign windows on later training days. Use
   the same calibration false-alarm budget for each scalar gate. The joint gate
   does not inherit an exact 5% false-alarm guarantee under temporal dependence.
4. Evaluate only records later than the last training-archive timestamp. Sort
   chronologically, with event ID/source order as deterministic tie breakers.
   Never use attack names or attack labels to build windows or gates.
5. Use non-overlapping 128-event windows, retaining a short final window. This is
   an event-count protocol, not a fixed-duration or uniformly sampled time series.
6. Predict each current window with the currently deployed policy model BEFORE
   deciding an update. A refit influences subsequent windows only. Reset model
   state at each archive/session boundary, and report separate sessions as well
   as pooled descriptive counts. A gap between sessions is not continuous traffic.
7. Compare static, periodic (every 5 windows), feature-only, SHAP-only, dual,
   cosine-coupled and conservative-coupled policies. All refits use the same
   100-tree model settings and random seed as the baseline, a fixed replay
   sample and current baseline-predicted normal records (minimum 10).
8. Freeze the diagnostic reference/model to separate gate effects from changing
   explanations. Screening uses the baseline model for equal candidate pools.
   This is a design choice and may itself become stale. No clean-data guarantee.
9. Compute all seven features' categorical PSI and SHAP displacement. Correct
   the rank term using feature-aligned mean-absolute-SHAP ranks, average ties,
   and a documented variance floor for normalised Wasserstein distance.
10. Keep all three gates in one explicit policy object. No attack-label tuning.

Pre-run implementation clarifications: remove duplicate event IDs, failing on
conflicting features/time/labels. Exclude training/reference timestamp ties from
fitting. Split windows and reset models at day boundaries inside each archive,
because the April validation-named archive spans two dates. That archive is
held out in this protocol regardless of its filename. Use strict `>` against
calibration gates so a zero-score tie cannot trigger an update. Cache identical
refits shared by several policies, and label attributed timing accordingly.

Primary endpoints: prequential event false-positive rate and recall, reported
together, plus F1 and update count. F1 is computed from pooled confusion counts,
not by assigning zero F1 to attack-free windows and averaging them. Also report
diagnostic window sensitivity and non-attack-window request rate descriptively.
Record actual fit/SHAP time, hashes, duplicates and archive chronology.

Hypotheses, not promised outcomes: dual signals may reduce unnecessary updating;
coupling may add no benefit or hurt transfer. Neither cosine similarity nor SHAP
is a new algorithm. Do not select a favourable threshold after examining test
labels. Two controlled sessions do not establish independent-incident generality.

### Sensitivity amendment after the first run

The initial 128-event, q=0.95, seed=42 run exposed high future-event false alarms
and zero coupling-gated updates. Without choosing a replacement primary setting,
run window sizes 64 and 256 at q=0.95/seed=42, seeds 17 and 73 at 128/q=0.95,
and q=0.90 and q=0.99 at 128/seed=42. Report the entire sensitivity grid, not only
favourable settings. This is a post-primary-run robustness amendment, not an
externally preregistered study. There are three day-separated test sessions from
two archives, including a 35-event session. They are not three independent sites.

## Phase B: controlled benchmark repair and robustness

After Phase A, add coherent interventions to raw categorical records, compute
actual changed-row masks and recompute derived root flags. Keep development and
evaluation source rows distinct. Test intensity, window size, categorical
representation and null-budget sensitivity using a locked protocol. Compare
against simple score-distribution drift and established streaming detectors where
their statistical assumptions and licensing permit. Do not call these finished
until their result artifacts and checks exist.

## Phase C: systematic review rebuild

Audit the existing 100 candidate DOI records for journal-article status, dates,
duplicate DOI, missing abstracts, topic match and real PDF availability. Resolve
publisher/repository OA links and log lawful retrieval attempts. Licence metadata
alone does not establish open access; validate PDF content and provenance.

Keep direct CloudTrail/cloud-audit papers separate from adjacent security studies.
Use a broad, explicitly declared mapping-review scope if needed, not an inflated
claim of 100 direct CloudTrail papers. Save exact database searches and all retrieved
records, not just the selected 100. Freeze eligibility before final inclusion.
Record automated assistance and actual reviewer involvement honestly. PRISMA is a
reporting guideline, not a certificate or a reason to manufacture inclusion counts.

Full-text extraction fields: research question, dataset and labels, chronology,
detector, explanation method, drift signal, adaptation, baselines, metrics,
leakage controls, external validation, limitations and code/data access. Do not
invent missing metrics or claim to have read inaccessible papers. A request for
100 papers does not justify including irrelevant or unverifiable studies.

## Phase D: manuscript and submission package

Update the research manuscript only from new saved results. Distinguish legacy
controlled, native temporal and observation-only evidence. Prepare reproducible
commands, supplementary results and data-availability/AI-assistance statements.
Confirm data reuse rights, author responsibility, correspondence email, guide's
venue choice, publication charges and the applicable JCR year/category before
submission. Scope fit and Q1/Q2 status do not guarantee editorial acceptance.

## Working schedule (not an acceptance-time estimate)

- 29 October: audit, native protocol, tests and first chronological results.
- 30 October: repaired controlled/robustness experiments and full-text retrieval.
- 31 October--1 November: extraction and evidence synthesis, manuscript revision.
- 2 November: author/guide checks, formatting and package validation.
- 3 November: student/guide-approved delivery/submission, if completion gates pass.

This is a target schedule, not a claim that 100 full texts are already available.
Access restrictions and actual evidence may require revising scope or timing.

## Official references checked

- PRISMA 2020: https://www.prisma-statement.org/prisma-2020
- IJIS author guidelines: https://link.springer.com/journal/10207/submission-guidelines
- Dataset documentation: https://github.com/ArielCyber/cloud_log_sampling

PRISMA has no universal requirement of exactly 100 included studies. The number
100 is the guide's requirement. The journal requests a data-availability statement
and numbered citations. Final author/venue choices remain subject to approval.
