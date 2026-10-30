# Exploratory context analysis on the inherited timestamped export

Declared 30 October 2026 before these outputs. The file
`D:/Projects/CloudGuard/data/nineteenFeaturesDf.csv` has 1,939,207 records and
timestamps with day/hour information according to its existing audit. It is a
richer export of the same inherited corpus, not an independent dataset. No
verified attack labels are available. Do not call alert rates attack recall or
benign false-positive rates.

Read only eventID, eventTime, sourceIPAddress, userAgent, eventName, eventSource,
awsRegion, userIdentitytype, userIdentityaccountId, userIdentityprincipalId,
userIdentityarn, errorCode and requestParametersinstanceType. In particular, do
not read or export userIdentityaccessKeyId, response data, full request bodies or
error messages. Identity, source and event identifiers are used transiently for
ordering and past-only grouping; do not write raw values or trained model files.

For every month, retain up to the first 1,000 source-order records. Sort this
sample by timestamp and event ID for chronology, with all equal timestamps
featurised together. Counts and novelty describe this sampled stream, not full
AWS activity. If some months contain fewer rows, record actual sizes. This
sampling is not a representative random sample.

Pre-analysis identifier amendment: the bounded 45,000-row sample has no missing
or placeholder event IDs, and 2,487 IDs are repeated. Each repeated ID has the
same timestamp and values on the selected analysis fields. Retain the first
occurrence per event ID without backfilling from later source rows. Fail if a
repeated ID conflicts on any selected field. Because credential and other unused
columns are deliberately not read, do not claim that complete source rows are
identical. Record duplicate counts and effective monthly sample sizes.

Use the existing 27/9/9 month train/validation/test split. Within the training
months, fit on the earliest 80% by timestamp and reserve the remainder as the
monitor reference, assigning any split ties to the later partition. Train only
three seed-42, 100-tree models: event ordinal, behaviour only and combined
ordinal. Use the same causal history, raw categorical PSI, reference numeric bins
and grouped SHAP contracts as the corrected external experiment. One-hot is not
run because the original dataset has a much larger categorical vocabulary and
the aim is a bounded feasibility analysis, not a model-selection contest.

Measure one window per validation or test month. Use nine validation windows to
calibrate feature, attribution, coupling and anomaly-score drift gates with the
higher 95th percentile. Separately compare the model training cutoff and the
95th percentile of unlabelled validation event scores. Report drift signals,
update requests and alert fractions, not false-positive rates or security recall.
Do not actually retrain on these unlabelled windows. Nine calibration windows
give a coarse maximum-like gate; window sample-size imbalance, source-order
prefixes and Aug-2019 volume concentration limit interpretation.

Save only aggregate windows, feature descriptions, counts, source/content hashes,
environment and code hashes. Do not export actor identifiers, source addresses,
raw event IDs or credential fields. The result does not provide independent
external validation or determine maliciousness.
