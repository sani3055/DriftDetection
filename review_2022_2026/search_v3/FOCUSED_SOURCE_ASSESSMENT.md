# Focused assessment of directly relevant sources

Assessed 30 October 2026 with AI assistance. These are targeted checks of methods,
evaluation and limitations at the PDF pages listed below. They are not complete
independent human reviews, final inclusion decisions, or the completed 100 study
synthesis. Metadata and full text retrieval alone are not critical appraisal.

## Kuppa and Le Khac 2022

DOI 10.1016/j.compeleceng.2022.108239. File
`review_2022_2026/retrieval_v3/Downloaded_Papers/CORE02_4116919d82f404a90f6f.pdf`.
Inspected PDF pages 4, 14 to 16 and 20.

The method uses contrastive representations and nearest class mean classification
for drift and new class discovery. Network and URL data support withheld class
and injected adversarial experiments. The reported split is 75 to 25 percent;
withheld classes simulate drift. Baselines include autoencoders, CADE and
INSOMNIA. These experiments do not establish native chronological CloudTrail
transfer. The relevant lesson is to distinguish adaptation to new concepts from
resistance to attacker supplied updates. No numerical superiority over this
paper is claimed by the project.

## Lee and colleagues 2023

DOI 10.32604/cmc.2023.040235. File
`review_2022_2026/retrieval_v3/Downloaded_Papers/CORE03_b65937b4e64ace3787dd.pdf`.
Inspected PDF pages 7, 9, 10, 12 and 16 to 18, corresponding to printed pages
1707, 1709, 1710, 1712 and 1716 to 1718.

SHAP descriptors and Mahalanobis distances generate suspected drift scores.
Monitoring reduces dependence on current labels, but historical class reference
and labelled DGA validation remain relevant supervision assumptions. Expert plot
inspection selects important features. The authors identify limited comparison
settings, SHAP cost and aggregation of individual signals as limitations.
This directly precedes explanation based drift monitoring; it does not validate
our coupling rule or a CloudTrail retraining benefit.

## Maseno and colleagues 2026

DOI 10.1007/s10207-026-01299-x. File
`review_2022_2026/submission_audit/Downloaded_Papers/CORE05_c104141fd5c3ba61e552.pdf`.
Inspected PDF pages 6 to 8, 14, 16 and 18.

LSTM and GRU models are evaluated on labelled ToN IoT flow data under FGSM and
PGD. SHAP deviation and feature overlap support rule based and learned secondary
detectors. Small Kernel SHAP and larger GradientExplainer branches are distinct.
The paper reports overlap between clean and adversarial explanation behaviour.
Reviewer inference: constructing overlapping windows before a stratified random
split creates a potential shared record leakage risk that requires checking;
the text alone does not prove realised leakage. This is adversarial input
monitoring, not natural temporal CloudTrail drift or demonstrated safe retraining.

## Implication for the project

Explanation based security monitoring is established prior work. A defensible
contribution needs matched comparisons, future evaluation, explicit supervision
assumptions and evidence of added value. The v3 paper now evaluates those claims
and retains the negative coupling findings. None of these three sources should
be cited as proof that our update rule is new or superior.

## Adediran and colleagues 2026, targeted addition

DOI 10.32604/cmc.2026.077606. Journal metadata: Computers, Materials & Continua,
87(2), article 100. [Publisher page](https://www.techscience.com/cmc/v87n2/66657).
This is an additional targeted discovery, not part of the original 392-record
bounded-search export. The author-hosted PDF is separately retained as CORE07.
Inspected PDF pages 6-10, 13-14, 17, 19, 23-24.

The authors evaluate retrieval-augmented LLM interpretation of 200 annotated
CloudTrail events from a controlled Stratus Red Team environment. Their target is
event interpretation and technique mapping, not drift-triggered retraining. The
article reports that individual events do not provide a temporal sequence, and
states that the data are available upon reasonable request. Its annotation
description includes simulator user-agent markers; reviewer inference is that a
replication must check marker leakage rather than treat these markers as robust
evidence of attack intent. Dataset access has not been requested. This targeted
assessment does not constitute full critical appraisal or an inclusion decision.

## Retrieval identity audit

The expanded search contains 392 distinct DOI records from four bounded queries.
It does not exhaust all matching research. Of 297 retained or uncertain metadata
records, 155 have readable retrieved PDF records. Hash deduplication identifies
153 distinct PDF files. Two pairs are repository and journal records sharing an
identical PDF and must not be counted twice as studies. Automated opening title
and DOI evidence supports 154 records; one translated title needs a source check.
These are acquisition and identity counts, not 153 eligible journal studies or
100 critically appraised papers. No final inclusion total has been declared.
