# PRISMA protocol for the CloudTrail drift-diagnosis evidence review

## Review type decision

Because the evidence spans heterogeneous detectors, datasets, labels, drift definitions, and
metrics, the review will use a structured systematic mapping/narrative synthesis rather than a
meta-analysis. PRISMA 2020 reporting will be followed where applicable, together with PRISMA-S
for search reporting. If the final question remains broad across adjacent cybersecurity domains,
the manuscript should be labelled a scoping or systematic-mapping review rather than implying a
comparative intervention meta-analysis.

## Review question

What methods published from 2022–2026 use machine learning, anomaly detection, explainability,
drift detection, or adaptive learning for cloud/audit-log and cybersecurity monitoring, and what
evidence supports SHAP-guided drift diagnosis for adaptive CloudTrail anomaly detection?

## Eligibility criteria

Include journal articles published from 2022 through 2026 with a DOI and a substantive connection
to at least two of these topic groups: cloud/audit logs; cybersecurity or intrusion/anomaly
detection; drift/adaptation; explainability/feature attribution; or machine learning/outlier
detection. Adjacent network, IoT, industrial-control, and log-monitoring studies are retained when
their method informs the project protocol.

Exclude conference-only records, editorials without a method or evidence contribution, retracted
records, records without a DOI, records outside 2022–2026, and clearly unrelated application-domain
anomaly studies. Non-English eligibility must be confirmed manually because the metadata service did
not provide a reliable language field for every record.

## Information sources and search date

Metadata discovery was executed on 21 October 2026 using OpenAlex with a Crossref fallback. The
exact query strings and retrieval log are recorded in `search_log.json`. The initial automated
search covered 12 combinations of CloudTrail/cloud audit logs, anomaly/intrusion detection,
explainable AI/SHAP, concept drift, and adaptive cybersecurity.

Before claiming a completed review, the team must repeat and archive searches in IEEE Xplore, ACM
Digital Library, Scopus or Web of Science, ScienceDirect, SpringerLink, and Google Scholar, record
the last-search date for each source, and document database-specific syntax, filters, and export
counts. OpenAlex/Crossref metadata alone is not sufficient coverage for a Q1/Q2 systematic review.

NotebookLM and SciSpace are not scholarly indexes. They may be used by the student team for manual
full-text organization after lawful institutional or open-access retrieval, but their use must be
recorded if claimed in the final review. Paywall bypasses or unauthorized copies must not be used.

## Screening and data extraction

The script performs a reproducible metadata-level initial screen using year, article type, DOI,
retraction status, topic-group matching, and excluded-domain terms. It selected 100 records from
1,898 unique DOI values. A triage audit found 18 records with a direct cloud/audit signal and 82
adjacent records; this is a review aid, not an inclusion decision. Every selected record is marked
`automated_include_pending_human_confirmation`.
Two independent reviewers must still confirm title/abstract and full text, resolve disagreements,
and record exclusion reasons before this is called a completed systematic review.

Extracted fields include DOI, title, authors, year, journal, abstract when available, query source,
topic groups, open-access status, PDF status, citation count, and screening status. For the final
review, add dataset, labels, detector, drift method, explanation method, adaptation policy, metrics,
limitations, funding, conflicts, code/data availability, temporal leakage controls, external
validation, and risk-of-bias judgments from full text. The 12 currently downloaded open-access
PDFs do not satisfy the requirement to have reviewed all 100 papers.

## Synthesis plan

The review will use a structured narrative synthesis rather than a meta-analysis because the
included studies are heterogeneous in datasets, labels, tasks, detectors, and metrics. Results will
be grouped into: (1) CloudTrail/cloud audit detection, (2) explainable intrusion detection, (3)
drift detection and adaptation, (4) log anomaly detection, and (5) operational deployment and
monitoring. Sensitivity analysis will compare the full set with a stricter CloudTrail/security-only
subset after human screening.

## Risk of bias and certainty

The current automated package does not yet contain study-level risk-of-bias or certainty ratings.
The reviewers must assess dataset transparency, label validity, temporal leakage, baseline adequacy,
external validation, reproducibility, reporting completeness, and journal/venue legitimacy for every
included article. Use two reviewers and record the disagreement-resolution rule. Do not infer study
quality from citation count alone.

## PRISMA completion gate

The review cannot be reported as PRISMA-complete until it has: (1) database-specific search logs,
(2) independent title/abstract screening, (3) full-text retrieval and exclusion reasons, (4) final
included-study characteristics, (5) risk-of-bias judgments, (6) a completed flow diagram with human
counts, and (7) a completed checklist with manuscript locations. The current files are protocol and
automation evidence only.

## Protocol status

No external registration was performed. This protocol is an internal project protocol and must be
marked as unregistered in the final manuscript. Any changes to eligibility criteria, databases, or
screening decisions must be logged before submission.
