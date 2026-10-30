# Behavioural context and guarded adaptation protocol

Declared 30 October 2026 before v4 model outcomes. This follows inspection of v3
on the same ArielCyber deployment and is exploratory, not external preregistration
or blind confirmation. Preserve every older run. Do not choose a favourable cell
and call it the only primary setting.

## Questions and fixed comparisons

Test whether strictly earlier actor history improves the seven field event
representation, whether cosine coupling adds incremental value within that
representation, and whether a one window quarantine reduces harmful updates.

Compare event only, behaviour only and combined inputs. Use ordinal and one hot
event encodings. Behaviour only has no categorical encoding factor and must not
be counted twice. Compare narrow v3 history with a broader chronological
70/10/10/10 split of all unique February benign events into fitting, reference,
calibration and guard. Purge fitting/reference/calibration boundary timestamp ties
by assigning the complete timestamp group to the later partition. Guard stays
strictly after calibration. Test the identical April sessions from v3.

Event classification uses either the forest training offset or the earlier benign
95th percentile. All forests have 100 trees, max_samples auto, contamination .05.
Seed 42 is the complete main grid: five distinct representation/input combinations
times two historical coverage splits times two event cutoffs = twenty settings.
Seeds 17 and 73 are declared sensitivity runs using the same twenty settings.
They reuse source events and are not independent deployments. The initial pilot
used 128-event windows and exposed two defects: ties could cross an update
boundary, and an empty quarantined pool could crash prediction. Pilot results are
preserved but rejected for the v4 main analysis. Before reading pilot outcome
summaries, replace batching with a target size of 128, extending each batch to
include the complete final timestamp group. Tails and session resets remain.
Quarantine now rejects pools of fewer than ten rows before prediction. Run the
entire grid again in `journal_v4_tiesafe` and record the revised code hashes.
Do not tune on April labels.

For efficiency, the corrected version computes the deterministic, strictly past
numeric history once and caches it without outcome labels or raw identity keys.
Each run verifies archive, event ordering, feature-file and feature-code hashes
before use. This cache does not change the split, state history or model policy.

## Causal history features

Compute chronological state from the supplied records, not the unobserved full
AWS traffic. Do not use count_of_same_events because its aggregation interval is
not a causal per-event history contract. Never use attack_name, should_sample,
filenames or raw actor/account identifiers as model inputs.

Actor key uses the session issuer ARN when present, then identity ARN, principal
ID, invoked service, or a marked fallback identity type/account key. Keys group
activity, not necessarily individual people. Resource tokens use resources ARNs
and selected request target names, never response secrets. Raw identifiers are
state keys only and are not exported as features. Missing resources are not
counted as newly accessed resources.

Sixteen numeric features are fixed: log actor event counts in the preceding five
minutes and hour; log preceding hour count of the same API; preceding hour failure
fraction; log preceding hour distinct services and resources; previously unseen
actor/service, actor/resource, actor/source and actor/user-agent indicators;
log seconds since previous actor activity capped at one day; actor seen before;
current resource present; hour sine and cosine; current readOnly flag.

All events with the same timestamp are featurised before any of them updates
history. Thus tie ordering cannot supply hidden earlier information. Fit and
reference features use only their actual earlier prefix. Each April session
starts from the full February history, then evolves only within that session.
Other April sessions do not warm it. Features from current events may describe
those events, but all frequency/novelty/history statistics exclude the current
timestamp group. Exact session grouping and missing-value rules are recorded.

## Monitoring and policies

Use raw event-category PSI and reference-quantile binned numeric-feature PSI.
Constant numeric references get a narrow central bin so newly nonconstant values
do not disappear. Group signed one-hot SHAP back to original event fields;
numeric fields retain their own contributions. Compare feature-level cosine of
PSI with mean-absolute attribution displacement, retaining magnitude gates.
Numeric bins, encoder and explanation model are frozen before April.

Compare static, periodic, feature only, SHAP only, dual, coupled, score Wasserstein,
ADWIN score, Page Hinkley score, guarded periodic, guarded dual, guarded coupled,
delayed guarded dual and delayed guarded coupled. Scalar monitoring gates use
the same earlier benign 95th percentile and strict greater-than comparisons.
ADWIN/Page Hinkley keep v3 public fixed settings. All current predictions precede
any updates. Every refit replays the full fitting matrix and requires ten current
candidate rows. Labels are read only after runtime decisions.

Immediate candidates are frozen-baseline predicted normal rows. Historical guards
retain v3 margins: benign guard alarm rate no more than static + .01 and top five
percent fitting anchor mean score no lower than static minus .02. These are
historical checks, not security guarantees.

Delayed policies quarantine baseline-predicted normal rows for one complete
window. A request at the current window can release the previous window pool
only if at least ten rows are still predicted normal by its deployed model and
the current frozen alarm fraction is no greater than its earlier benign 95th
percentile. Otherwise defer and record the reason. The released candidate must
also pass the same historical guard. No retrospective relabelling, attack-name
screening or target-batch recalibration. A delay alone does not certify safety.

## Outcomes and interpretation

Report pooled and per-session confusion counts, recall, FPR, precision, F1,
requests, accepted updates, deferrals, guard rejects, and accepted candidate
contamination after decisions. Retain event scores for static ranking analysis
and per-window counts for paired comparisons. Report every setting, not a test
selected best seed. Compare coupling against the same inputs without coupling;
compare behaviour against the event baseline with the same split and cutoff.

Any new external public attack traces are acquired as inert data only. Freeze
model choice before inspecting trace outcomes; preserve all declared cells when
possible. Audit licence, source, timestamp quality, duplication, trace context and
label semantics. Attack-containing traces are not entirely malicious events.
Without credible benign controls and per-event targets, report alert/target-API
coverage, not external FPR or ground-truth attack recall. A trace predating source
training is retrospective cross-environment replay, not future chronology.

## Controlled primary calibration repair

Preserve the original v3 controlled result. A new runner must calibrate on
200-row samples, matching monitoring size, using seeds 17/42/73 for each of nine
validation months. Run both training offset and unlabelled validation score
95th-percentile cutoffs. Candidate cutoffs use earlier validation only. All
existing eight future-month pairs, seven scenario families and two intensities
remain fixed. Background labels remain unknown; negative-class rates remain
mask-relative proxies. No event sequence features are fabricated on this corpus.

## Review and release

### Secondary contamination stress amendment

Before reading v4 performance summaries, declare a separate feature-matrix stress
test on all five narrow training-offset seed-42 input combinations. Construct
candidate pools from labelled April-4 benign/attack rows at nominal attack
fractions 0/.01/.05/.10/.20, pool sizes 200/2000 and seeds 17/42/73. These labels
construct the controlled stress condition only, not a deployable selection rule.
Compare static, unfiltered refit, frozen-normal screened refit and historically
guarded screened refit. Refit on complete February fitting replay plus the pool.
Evaluate the disjoint April-28 session. Do not inject synthetic AWS actions or
claim a native poisoning stream: this is a counterfactual feature-matrix stress
test. Report nominal and accepted attack fractions separately. No optimisation
of gate parameters from stress outcomes. The delayed policy's operational
comparison remains in the native stream grid, not a duplicate label-informed
oracle within this stress test.

Continue source-level full-text assessment and version deduplication. Lawful
retrieval and assisted identity checks do not complete a 100-study systematic
review. No invented reviewers, agreement or PRISMA counts. Do not upload papers,
submit manuscripts or change authorship without explicit scope and permission.
