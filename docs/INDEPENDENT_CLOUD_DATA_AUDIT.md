# Independent CloudTrail data audit

## Splunk attack traces

The public [Splunk attack data repository](https://github.com/splunk/attack_data)
contains CloudTrail traces from attack-range scenarios. A bounded, deterministic
selection is stored under `data/external/splunk_cloudtrail_v4`, with the source
commit, acquisition manifest, licence, file hashes and per-file schema audit.
Twenty files were retrieved. Eleven contain 147 unique native-format events after
the first parsing and deduplication pass. The remaining files include OCSF
representations or duplicate/unsupported records. These counts are acquisition
results, not labelled test-set counts.

Trace names establish scenario provenance but do not label every event. Without
event-level labels and suitable benign controls, report trace alert coverage and
event alert fraction only. Do not report external attack recall or FPR. Where
source timestamps precede the model's training period, this is retrospective
cross-environment replay and is not a forward-in-time deployment evaluation.

The first twenty paths were selected lexicographically, which limits attack-family
coverage. A separate extension adds remaining native-format-named CloudTrail
paths from the same frozen source commit. Its selection is declared before model
outcomes and preserved independently; duplicated events must be excluded across
both subsets before any aggregate claim.

## Additional annotated study

Adediran, Awuson-David and Ahmed's 2026 CloudTrail study reports a manually
annotated 200-event evaluation of a retrieval-augmented system. It is a relevant
independent research setting, but the paper says its data are available upon
reasonable request, not that the dataset is openly downloadable. Its annotation
description refers to Stratus Red Team user-agent markers, so any future reuse
must investigate marker-based label leakage and uncertainty. No email or access
request has been sent. [Author-hosted paper, especially PDF pages 6-7 and 24](https://www.open-access.bcu.ac.uk/16916/1/TSP_CMC_77606.pdf).

Independent labelled CloudTrail evaluation with established benign controls is
still open. The trace collection does not by itself resolve that gap.

## Independently authored labelled generic synthetic events

The Apache-2.0 [cloud-threat-anomaly-lab](https://github.com/katerina20/cloud-threat-anomaly-lab)
provides a committed, cloud-neutral synthetic sample with per-event normal/anomaly
labels. A frozen, retrospective cross-domain replay is documented in
`docs/INDEPENDENT_LABELLED_SYNTHETIC_FINDINGS.md`. It is not a native CloudTrail
corpus and does not supply an independent real AWS environment; it therefore
does not resolve the independent labelled CloudTrail validation gap.

## Independent synthetic baseline

Opsbreak's MIT-licensed Trailhunt sample contains 11,575 generated CloudTrail
records at source commit `24aef4fb441ae00739395aa741fa5f53c77d9cde`. The source
describes the first seven days as benign background before three simulated
incidents. The replay includes 8,816 background events and three predetermined
15-minute mixed incident windows. All twenty frozen main models are retained.

This is independently authored synthetic data, not a production site or a
separate set of independently verified incident labels. A model alert anywhere
in a mixed incident window may originate from benign activity. The synthetic
background alert rate is not a production FPR, and window alerts are not
event-level attack recall. Input was read as inert published data; no generator
or attack code was run. See `INDEPENDENT_SYNTHETIC_PROTOCOL.md` and
`results/journal_v4_synthetic_independent/` for the declared method and outputs.
