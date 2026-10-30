# Journal v3 comparison protocol

Locked 30 October 2026 before the v3 experiments. This is a post-v2 research
amendment, not independent preregistration or an unseen external corpus. Preserve
all legacy/v2 data. Do not select a favourable variant as if it were prespecified.

## Questions

1. How much of the v2 transfer failure is associated with categorical encoding,
   score calibration and limited normal-workload coverage?
2. Do attribution-based update gates add value over anomaly-score monitoring,
   ADWIN and Page--Hinkley under the same prediction-before-update protocol?
3. Does high cosine coupling discriminate security-relevant changes, or does
   benign feature dominance make that interpretation unreliable?
4. Can a historical shadow-update guard limit regressions without attack labels?

## Temporal data and representation

Use the same earliest benign-day fit/reference boundary as v2. Category maps or
one-hot vocabularies are learned from fitting rows only. Compare ordinal encoding
(unknown -1) with one-hot encoding (unknown categories give all-zero blocks).
One-hot SHAP values are summed with sign within each original feature block.
This preserves additivity but is not a new coalition/Owen SHAP computation.
Drift uses the original categorical values, retaining distinct unseen categories.

Use 19 February benign events for calibration of event scores and monitoring
gates, and 20 February benign events for an untouched historical guard. Do not
use any April labels to choose representations, quantiles, gates or guards.
Calibration and guard dates are earlier than all retained April test sessions.

Fix 128-event windows, retain short tails, and reset models at date/session
boundaries. Default seed 42; repeat full factorial baseline comparisons at seeds
17 and 73. Window sizes 64/256 are sensitivity analyses at seed 42 only. These
replications share events and are not independent incidents or sites.

## Factorial controls

For each representation, compare event classification using the forest's own
training offset with classification using the 95th percentile of earlier benign
anomaly scores. A calibrated model has its own earlier-data score cutoff. Never
use a future test batch to set that cutoff. The empirical false-alarm budget is
not a distribution-free deployment guarantee. All forests have 100 trees,
max_samples auto, contamination .05 and the same seed.

## Matched update comparisons

Compare static, periodic (every fifth batch), feature-PSI, SHAP drift, dual,
cosine-coupled, conservative-coupled, score-Wasserstein, ADWIN-score,
Page--Hinkley-score and guarded-dual. Single-scalar magnitude gates use the higher
95th percentile of the same earlier benign windows. Coupling keeps the full gate
object, and remains a diagnostic alignment measure, not an attack probability.

ADWIN and Page--Hinkley use River 0.26.1 with recorded public parameters and
bounded baseline Isolation Forest anomaly scores. Feed every event in order and
request an update at the end of a batch if any drift alarm fired in it. Warm the
detectors on calibration events and clone this state at each test session.
No error-stream detector is given attack labels. No per-test hyperparameter
tuning or claim that default settings are universally optimal.

Use the complete fitting matrix as replay, not a 512-row replacement. This
avoids conflating a dramatic reduction in historical training data with adaptive
learning. Add current baseline-predicted normal candidates, minimum ten. An
event-score-calibrated refit calibrates its cutoff on the same earlier benign
calibration set; it does not calibrate on its current/future test batch. Hold
encoding/reference/diagnostic baseline fixed. Score first, decide and refit
second. Each policy keeps its deployed model until a later accepted refit.

The exploratory guarded-dual variant checks a candidate against the separate
historical benign guard and frozen fitting-data score anchors. Require guard
false positives no greater than the static model plus .01 and mean anomaly-score
retention on the highest-scoring 5% of fitting rows no lower than baseline minus
.02. These are label-free model-preservation constraints, not ground-truth attack
recall or a security guarantee. Include guarded-feature and guard-only periodic
ablations if the guard is evaluated. Never present its historical check as future
performance. Keep all margins fixed and report rejection counts.

## Endpoints and inference

Report pooled event confusion counts, FPR, recall, precision, F1, update requests,
actual refits, terminal requests, candidate contamination (evaluation only), SHAP
additivity, unknown-category rate, model-fitting/SHAP/decision timing, and
per-session/per-attack breakdowns. Undefined denominators remain undefined.

Record paired window counts for all policies. Use a session-stratified moving
block bootstrap (block length five windows, 2,000 resamples, seed 20261030) for
descriptive within-corpus differences in pooled FPR and recall. Preserve identical
resampled indices across policies. Sensitivity to block lengths two and ten is
required for central comparisons. No population-level incident significance
claim or arbitrary windows-as-independent p-values.

## Failure analysis and novelty boundary

Cosine similarity is scale invariant. Two changes on one feature can have cosine
one whether the activity is benign or malicious. If benign calibration already
has near-one alignment, a high-quantile alignment gate can suppress distributed
future changes. Quantify the observed calibration/test overlap, dominant feature,
effective feature count and gate-pass rates. Do not flip gate direction after
seeing labels and report it as confirmation.

Calibrating anomaly scores, one-hot encoding, streaming drift tests and historical
guards are established ideas. Their combination is not automatically a new
algorithm. A journal claim must rest on the comparative evidence, an explicit
CloudTrail failure mechanism, and validated incremental value if it exists.

## Controlled primary-corpus amendment

After inspecting the four primary external factorial cells, run a separately
declared repair of the controlled experiment on the inherited corpus. This is
exploratory corroboration, not new prospective attack ground truth. Decode the
saved 1,000-row monthly score prefixes using the original training-only maps;
retain the seven-field representation and derived root indicator. Fit a fresh
100-tree ordinal forest on the 27,000 training-month prefix records. Monitoring
reference: a deterministic 200-record stratified sample of those training months.
Calibrate drift gates on nine unmodified validation-month prefixes. Primary
classification uses the forest training offset; sensitivity uses the higher
95th percentile of unlabelled validation scores, not known-benign ground truth.

Use each of the eight consecutive held-out test-month pairs. Draw 200 monitoring
rows in the first month and 200 distinct evaluation rows in the next. Seeds
17/42/73 and intervention intensities .125/.25 are fixed before this run.
Include stable, routine region, routine identity, coherent routine Lambda,
privilege, defence and credential families. Security-target labels mean an
intended synthetic intervention, not a confirmed attack in the original logs.

For security changes, replace whole consistent feature tuples: AttachUserPolicy
with iam.amazonaws.com/Root; DeleteTrail with cloudtrail.amazonaws.com/IAMUser;
CreateAccessKey with iam.amazonaws.com/IAMUser. Set the root flag consistently,
use NotApplicable instance type and the inherited Unknown error placeholder, and compute the actual changed-row
mask. Routine Lambda uses Invoke/lambda.amazonaws.com/AssumedRole. Other routine
changes preserve API/service pairing. No actual AWS operations are performed.

Compare static, periodic, feature-only, SHAP-only, dual, cosine-coupled,
conservative-coupled and score-Wasserstein. Fit a shared candidate on the complete
27,000-row replay plus baseline-predicted normal monitor rows, minimum ten. Score
the distinct next-month matrix only; evaluation rows never enter fitting or gates.
Reset baseline between counterfactual units. Periodic uses a fixed every-fifth
unit schedule, not a real-time monthly deployment policy. ADWIN/Page--Hinkley are
not used here because within-month event order is not supported by timestamps.

The negative-class rate is a mask-relative false-positive proxy, since unchanged
rows have no verified security label. Prefix sampling, shared month pairs and
overlapping counterfactual scenarios prevent independent-incident interpretation.
Save source hashes, actual changed-row counts, per-unit paired counts and all
settings. These outputs do not retroactively repair or replace old results.

Implementation note after the first controlled run: the generator uses Unknown,
not NoError, to match the inherited missing/success placeholder. The completed
run evaluates the training-offset classification condition only. The proposed
unlabelled-validation score-cutoff sensitivity has not been run and must not be
reported as completed. The 200-record reference is an evenly spaced deterministic
selection over sorted training prefixes, not a probabilistic stratified sample.

## Review workstream

Continue lawful OA retrieval using publisher/repository locations, retaining
provenance and hashes. Record DOI identity checks and page-located extraction.
Do not count downloading, parsing or metadata verification as critical reading.
Do not force weak/unrelated studies into a 100-study quota. Report AI involvement,
actual screening work and remaining access gaps accurately.

## Primary implementation references checked

Pre-run compatibility amendment: River 0.23.0 requires pandas below version 3,
conflicting with the preserved research environment. Replace it with River
0.26.1, whose mandatory dependencies permit the pinned pandas environment.
Verify package consistency before running; do not downgrade existing research
dependencies. Record the actual implementation version in every run manifest.

https://riverml.xyz/dev/api/drift/ADWIN/
https://riverml.xyz/dev/api/drift/PageHinkley/
https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OneHotEncoder.html
