# Behavioural Context and Attribution Guided Adaptation for Cloud Audit Logs

Sanidhya Bhandari

Department of IoT, School of Computer Science and Engineering, Vellore Institute of Technology, Vellore, India

## Abstract

Cloud audit anomaly detectors encounter changes in both legitimate workloads and attack activity. This study tests whether past-only behavioural context and alignment between input drift and SHAP attribution drift improve decisions to update an Isolation Forest. Fourteen policies are evaluated in 20 main settings covering five input representations, two historical coverage splits and two score cutoffs. Every setting scores the same 11,531 later CloudTrail events from one controlled deployment before requesting any update. With ordinal event inputs and the training cutoff, the static model reaches recall 0.9485 and benign false-positive rate 0.7187. Adding behavioural context lowers static recall to 0.3957 and raises the false-positive rate to 0.7333. On the combined ordinal representation, the dual-signal policy reaches recall 0.9488 with false-positive rate 0.9792; adding coupling reduces recall to 0.8944 and false-positive rate to 0.9750. Historical guards and one-window quarantine reduce some updates but do not consistently prevent attack-labelled records from entering accepted candidates. A separate replay covers 1,047 unlabelled events from 31 public CloudTrail traces; it does not estimate attack recall or benign false positives. Controlled contamination and future-month synthetic interventions further examine update sensitivity. The findings support a comparative failure analysis rather than a claim that coupling or behavioural context universally improves security detection.

**Keywords** AWS CloudTrail; anomaly detection; concept drift; SHAP; temporal evaluation; adaptive monitoring; behavioural context

## 1 Introduction

AWS CloudTrail records API activity associated with identities and services [@aws]. The same operation can be legitimate in one context and suspicious in another. Cloud workloads also change when applications, permissions or operational practices change. An anomaly detector may therefore flag a routine operational shift, or fail to flag an attack that resembles familiar activity.

Updating a detector presents an additional risk. A model that never changes can become unsuitable for the current workload. A model that learns every apparently normal event can absorb suspicious activity. A meaningful adaptation evaluation must measure future predictions and the composition of accepted updates, not only whether a drift signal changes.

Input distribution changes and changes in model explanations offer complementary monitoring signals. SHAP describes how a fitted model allocates its output to input features [@shap; @treeshap]. The coupling rule considered here compares feature-level distribution drift with displacement in feature attributions. High alignment means that similar features dominate both vectors. It does not establish malicious intent, explain causal effects or guarantee that a retrained model will improve.

An earlier analysis of this project found that 16 of 123 observed seven-field profiles in the labelled test corpus contain both attack and benign events. For a fixed classifier using only those profiles, this ambiguity creates unavoidable errors on that sample. It does not establish a population error bound. This observation motivates testing history that is available before an event, such as an identity's recent activity and first-seen services or resources.

The questions are: whether past-only behaviour improves event detection; whether coupling adds value beyond feature and attribution magnitude gates; whether a historical guard and a one-window quarantine improve update safety; and how conclusions vary with representation, score calibration and historical coverage. The analysis includes a separate retrospective replay on public unlabelled traces and a controlled update-contamination experiment.

The contribution is a reproducible comparison with explicit negative findings and safeguards against temporal and label leakage. The feature families, Isolation Forest, SHAP, drift tests and historical guards are established techniques. Their combination is treated as an empirical hypothesis, not a claim of a universally superior or first-of-its-kind algorithm.

## 2 Related work

Concept drift research distinguishes changes in data distribution from changes in the relationship between observations and outcomes [@gama; @arora]. In an unlabelled operational stream, feature shift alone does not prove that attack detection has degraded. Isolation Forest provides an unsupervised anomaly baseline through random partitions [@isof], while SHAP and Tree SHAP describe fitted model outputs [@shap; @treeshap].

Kuppa and Le Khac examine drift and new class discovery in security settings under withheld classes and adversarial perturbations [@kuppa]. Lee and colleagues use SHAP descriptors and Mahalanobis distances for drift detection with reduced reliance on current labels [@lee]. Li and colleagues study adaptation based on drift type [@li]. OWAD and XPE also examine adaptation or performance monitoring under shifting inputs [@han; @decker]. Their datasets and objectives differ from the present CloudTrail comparison; their published scores are not matched numerical baselines here.

Lara Gutierrez and colleagues consider drift detection and adaptation in security systems [@lara]. Maseno and colleagues study explanation changes under adversarial evasion in network intrusion models [@maseno]. Adediran and colleagues evaluate retrieval-augmented interpretation of labelled CloudTrail events in a controlled setting [@adediran]. Their data are available on request and are not used as a test dataset in this study. Together, these works show that explanation based security monitoring and contextual CloudTrail analysis are established topics.

The study compares score drift with ADWIN and Page Hinkley through River [@river], in addition to feature, attribution and coupling rules. These baselines receive anomaly scores without test attack labels. Default streaming-detector parameters are fixed, rather than optimised after viewing test outcomes.

## 3 Data and study design

### 3.1 Native chronological corpus

The primary labelled evaluation uses the public ArielCyber cloud log sampling dataset [@clouddata]. It originates from a controlled AWS deployment with executed attack scenarios. The `should_sample` annotation is used as the event-level attack label for evaluation. These records are not independent naturally occurring production incidents.

The benign base archive contains 16,495 records. Nine repeated event identifiers are removed, leaving 16,486 unique events. Two chronological splits test historical workload coverage. The narrow split follows the previous experiment: the first day is divided into fitting and reference portions, the second day calibrates scores and drift gates, and the third day supplies an independent historical guard. The broad split assigns approximately 70%, 10%, 10% and 10% of the full benign archive to fitting, reference, calibration and guard, respectively. Tied timestamps at split boundaries are assigned to the later partition.

[[TABLE:v4_split]]

The test comprises 7,315 events on 4 April 2026, 35 on 27 April and 4,181 on 28 April. It contains 3,126 attack-labelled and 8,405 benign-labelled events. Earlier records in the mixed archive are excluded. The archive named train_labeled_a is held out despite its name. Event identifiers do not overlap across the source archives.

Each session begins from the same initial prediction model and historical feature state. A batch targets 128 events but is extended to contain the whole final timestamp group. This prevents a model update from being deployed between events whose recorded timestamps do not establish an order. A short final batch is retained. Models and streaming monitors reset between the date-separated sessions; the experiment is not a continuous deployment across the February to April gap.

The v4 protocol was specified after earlier results on this deployment were inspected. The same April records are therefore held out from fitting and threshold calibration, but they are not a previously unseen external corpus. A preliminary implementation that split equal timestamps and could fail on an empty quarantine pool was rejected for the main analysis. Its outputs remain separate from the corrected results.

### 3.2 Inherited monthly corpus

The project also retains a 1,939,207-row, 45-month CloudTrail-style CSV without verified attack labels. Its available timestamp field supports month-level, not within-month event, ordering. The saved experimental sample consists of deterministic prefixes of up to 1,000 records per month, which may not represent the full workload.

The controlled extension fits a forest on 27,000 training-prefix rows and tests eight consecutive held-out month pairs. Seven scenario families, three seeds and two intervention intensities produce 336 counterfactual units per policy and cutoff. Security labels indicate actual rows changed by a synthetic intervention, not confirmed attacks in the original data. Validation and monitoring samples both contain 200 rows in this revised experiment.

A separate richer export of the same corpus contains day-and-hour timestamps. For an exploratory real-data analysis, up to the first 1,000 source-order rows per month are sampled, then sorted by time. An identifier audit found 2,487 repeated event IDs with matching timestamps and selected analysis fields; the first occurrence is retained without backfilling. Unselected fields were not checked for complete-row identity. The resulting sample contains 42,513 records. Only the selected fields necessary for event representation and historical grouping are read; access-key identifiers and response contents are excluded, and raw actor identifiers are not exported.

For this richer-export analysis, the earliest 80% of sampled training-month records fit the models and the remaining training-month records form the reference, with timestamp ties assigned to the later partition. Event ordinal, behaviour-only and combined ordinal models are tested on one window per validation and test month. These are observations of the inherited corpus, not independent validation. The flattened export does not provide the resource identifiers used by the external context analysis.

### 3.3 Input representations

The event representation contains eventName, eventSource, awsRegion, userIdentitytype, errorCode, requestParametersinstanceType and a derived root flag. Categorical maps are fitted only on the corresponding historical training rows. Ordinal encoding maps unseen categories to minus one; one-hot encoding gives an unseen category an all-zero block. Both representations can obscure differences among unseen values.

The behavioural representation has sixteen numeric fields: recent actor event counts in five minutes and one hour; recent counts of the same API; recent error fraction and counts of distinct services and resources; first-seen service, resource, source and user-agent indicators; time since previous activity; actor-seen and resource-present indicators; time-of-day sine and cosine; and the current readOnly flag. Event-only, behaviour-only and combined inputs are evaluated. Event and combined inputs use both categorical encodings; behaviour-only inputs are numeric.

Actor state is keyed by the session issuer when present, then identity ARN, principal identifier, invoked service or a marked fallback. A role can represent multiple people or processes, so an actor key is not assumed to identify one human. Resource tokens use resource ARNs and selected request target names, not response contents. Identifiers are state keys and are not numeric model inputs. Missing resources are not treated as newly accessed resources.

All records sharing a timestamp are featurised before the history state incorporates any of them. Frequency, novelty and gap features exclude the current timestamp group. The history covers retained dataset records, not all AWS activity. The dataset's aggregate count_of_same_events field is excluded because its aggregation timing is not established as a past-only per-event feature. Frozen numeric histories are cached with archive, order and code hashes, without outcome labels or raw actor keys.

## 4 Monitoring and adaptation

### 4.1 Detector and explanation output

All initial and candidate Isolation Forest models have 100 trees, contamination 0.05, max_samples set to auto and the setting's fixed random seed [@sklearn]. The main comparison uses seed 42. Score-cutoff alternatives are the fitted forest offset and the higher empirical 95th percentile of anomaly scores from earlier benign calibration events. A candidate model receives its own cutoff calculated on that same earlier calibration set, not on the current or future test batch.

TreeExplainer describes the Isolation Forest adapter's internal mean path output, not an attack probability. Signed contributions for one-hot columns are summed within their original event feature. Numeric features keep separate contributions. This grouping preserves additivity but is not a separate coalition SHAP calculation. The explainer, encoder and monitoring reference remain frozen even when a deployed prediction model changes.

### 4.2 Drift signals and coupling

Categorical drift is measured on the original event values. Numeric behavioural features are divided using quantile cut points fitted on the reference set. A constant reference feature receives a narrow central bin so later nonconstant values are not silently collapsed. Reference and current counts are smoothed by adding ten to the power minus six before normalisation. For feature j, the population stability index is:

[[EQ:psi]]

The feature magnitude F is the mean PSI across m original features. Thus m equals seven for event-only inputs, sixteen for behaviour-only inputs and twenty-three for combined inputs.

[[EQ:feature]]

Attribution drift combines reference-scaled Wasserstein distances between per-feature SHAP distributions, top-three feature overlap and a feature-aligned Kendall rank comparison. The scale is the larger of the reference standard deviation and a floor equal to ten percent of the median positive reference deviation, bounded below by ten to the power minus six.

[[EQ:wasserstein]]

[[EQ:shap]]

In the attribution equation, p is the number of original features, J is the Jaccard overlap of top-three features and K is Kendall tau. The coupling value C is the cosine of the PSI vector and the change in mean absolute feature attribution:

[[EQ:coupling]]

The value is set to zero when the product of vector norms is below ten to the power minus twelve. Cosine is invariant to positive rescaling. A concentrated benign shift and a concentrated attack-associated shift can therefore have the same alignment; magnitude gates do not by themselves solve this ambiguity. An effective-feature diagnostic records whether a vector is concentrated or distributed, returning zero for a zero vector:

[[EQ:effective]]

### 4.3 Policies and update safety

Fourteen policies are compared: static, periodic, feature-only, SHAP-only, dual signal, coupled signal, score Wasserstein, ADWIN, Page Hinkley, guarded periodic, guarded dual, guarded coupled, delayed guarded dual and delayed guarded coupled. Scalar drift gates use the higher 95th percentile of earlier benign calibration windows and strictly greater-than comparisons. The coupled rule requires both magnitude gates and the coupling gate. Periodic updates are requested every fifth batch in a session.

ADWIN and Page Hinkley are warmed on earlier calibration anomaly scores and cloned for each test session [@river]. Each receives frozen-model scores, not labels. All current-window predictions use the previously deployed model. Only after scoring can a requested candidate be fitted with the full historical fitting matrix plus at least ten frozen-baseline predicted-normal current rows.

The historical guard accepts a candidate only when its historical benign guard alarm rate is no more than 0.01 above the baseline and its average anomaly score on the top five percent of fitting anchors is no lower than the baseline by more than 0.02. This checks historical behaviour; it does not measure future attack retention.

Delayed policies quarantine predicted-normal rows for one complete window. When the current gate requests an update, the previous pool is eligible only if its current deployed model still predicts at least ten rows normal and the current frozen alarm fraction does not exceed an earlier benign calibration limit. The same historical guard is then applied. The procedure can defer an update, but cannot guarantee that released rows are benign.

### 4.4 Evaluation and uncertainty

The main seed-42 grid crosses five distinct input representations, two coverage splits and two cutoff types. Fourteen policies run in each of the 20 settings. The labels are used after runtime decisions for confusion counts, scenario breakdowns and accepted-candidate contamination audits. Scores with an undefined denominator are not silently converted into valid performance estimates.

Differences between policies use paired window confusion counts. For descriptive intervals, windows are sampled in contiguous blocks within each session [@kunsch]. The same indices are used for both policies in 2,000 resamples. Lengths two, five and ten are retained, with five used for the main displayed comparison. These intervals describe this dataset and do not establish confidence coverage for independent organisations or incidents.

Additional seeds 17 and 73 repeat the same grid. They reuse the same source events and cannot be interpreted as independent deployments. The full per-setting summaries, paired intervals and chronology checks are retained for inspection rather than selecting a favourable setting after testing.

## 5 Results

### 5.1 Behaviour and coupling under the main condition

For the narrow historical split and training cutoff, the event-only ordinal static model has the highest recall among the five static representations shown in Table 2, but its benign false-positive rate is already high. The combined ordinal static model flags a similar proportion of benign events while detecting fewer attack-labelled events. Thus adding behavioural context does not automatically improve the detector.

[[TABLE:v4_main]]

On combined ordinal inputs, the dual policy recovers much of the static recall loss, but flags nearly all benign test events. Coupling reduces both recall and false positives slightly relative to dual. The resulting F1 remains below the event-only ordinal static F1. These are comparisons within one corpus, not evidence that one representation is universally better.

The event-only one-hot and combined one-hot settings illustrate a different trade-off. Combined one-hot dual updating improves recall relative to event-only one-hot dual, but increases the benign false-positive rate substantially. A recall improvement alone would omit that operational cost.

[[FIG:tradeoffs]]

Table 3 retains the F1 outcomes for static, dual and coupled policies in all 20 main settings. All of them reuse the same labelled source events. A low F1 or a zero-recall setting is retained rather than excluded. Full recall, FPR, precision and candidate counts are reported in the accompanying machine-readable results.

[[TABLE:v4_factorial]]

### 5.2 Coupling and historical safeguards

In the combined ordinal main condition, coupled minus dual recall is approximately minus 0.0544 and FPR approximately minus 0.0042. The descriptive paired interval for F1 includes zero. These results do not establish an incremental improvement from the coupling gate.

[[TABLE:v4_ci]]

Across all 60 representation, coverage, cutoff and seed combinations, coupled
minus dual pooled F1 is positive in ten cells, negative in 49 and equal in one,
using a numerical tolerance of ten to the power minus twelve. The same test
events recur throughout these cells, so these sign counts are descriptive and do
not represent 60 independent replications or a significance test.

The safety audit counts attack-labelled records among rows accepted for completed updates after decisions are fixed. For combined ordinal dual, 1,889 such candidate rows enter 40 refits. The historical guard still allows 1,799 in 38 refits. Delayed guarded dual allows 41 in two refits and defers many requests. The reduction in accepted count accompanies a different update schedule and does not show that the resulting detector is safe or effective.

[[TABLE:v4_guard]]

These counts are not estimates of independently occurring attacks. They depend on the labels and sampled stream of one controlled deployment. Candidate rows in a baseline-predicted-normal pool can nevertheless carry attack labels, demonstrating that predicted normality is not a verified benign label.

### 5.3 Controlled contamination

To examine the update mechanism directly, a separate counterfactual experiment constructs candidate pools from earlier April benign- and attack-labelled events at nominal attack fractions of zero, one, five, ten and twenty percent. Pool sizes are 200 and 2,000, with seeds 17, 42 and 73. All five narrow training-cutoff input representations are included. Outcomes are evaluated on the later 28 April session.

The source labels select the constructed stress conditions and measure outcomes. They are not supplied to the runtime screen or historical guard. Each condition compares static predictions with unfiltered, screened and guarded-screened refits. Candidate histories are inherited from the observed source stream; mixing their feature matrices does not simulate a new chronological attack stream.

[[TABLE:v4_stress]]

At a nominal twenty percent contamination and a 2,000-row pool, the number of attack-labelled records remaining after predicted-normal screening varies substantially across representations. Historical guard rejection can prevent some candidate models from being deployed, but acceptance says only that the two historical checks passed. Later F1 and recall must still be evaluated, and three seeds on the same deployment are dependent.

### 5.4 Matched monthly intervention experiment

The repaired monthly experiment uses 27 calibration samples of 200 records, matching its 200-record monitoring samples. It tests both the forest training offset and an earlier unlabelled validation-score quantile. Coupled and dual policies request no updates in this experiment and match static predictions.

[[TABLE:v4_primary]]

The training-offset static model detects one third of pooled synthetic changed-row targets. The validation-score quantile produces much lower synthetic target recall. Neither result is a verified attack-detection rate: the positive labels are constructed interventions and the negative-class rate is a mask-relative proxy on unlabelled background.

### 5.5 Observed drift on the richer inherited export

The timestamped sample permits a past-only context analysis on the original corpus. After the fitting and reference split, the three models are observed over nine validation and nine test months. The dual and coupled gates request no updates in any of the nine test months for all three representations. No model is actually retrained in this observation track.

[[TABLE:v4_rich]]

Monthly alert fractions vary by representation and event cutoff. These are unlabelled alarm rates, not false-positive rates. The validation months supply only nine calibration windows, so the higher 95th-percentile gate is effectively the observed maximum. Selected source-order prefixes, duplicate removal without backfilling and unequal monthly sample sizes also limit interpretation.

### 5.6 Cross-environment trace replay

A frozen source revision of Splunk's public attack-data repository provides a separate collection of CloudTrail traces [@splunk]. After schema checks and deduplication, 31 traces contain 1,047 native-format events. The models are not updated on these traces. Behavioural history starts cold for each trace, and some source timestamps precede the model's training period. This is retrospective cross-environment replay, not a forward-in-time evaluation.

[[TABLE:v4_external]]

The fraction of records producing an alert differs greatly across input representations. An attack-scenario filename does not label every record, and this collection has no established event-level attack labels or verified benign controls. The results therefore measure alert coverage only. They cannot establish attack recall, false-positive rate or independent production effectiveness.

### 5.7 Independent synthetic baseline

An independently authored synthetic CloudTrail sample contains 11,575 events in a fictional AWS account [@trailhunt]. Its documented first seven days supply 8,816 benign-background events before three simulated incidents. The 20 frozen source models are replayed without target retraining. Actor history starts cold at the beginning of the synthetic stream. A secondary background rate excludes the first 24 hours to show cold-start sensitivity.

[[TABLE:v4_synthetic]]

In the narrow training-cutoff condition, the combined ordinal model flags 99.5% of the synthetic background, while event-only ordinal flags 25.0%. All five displayed models produce at least one alert in each of the three declared 15-minute incident windows. Those windows mix incident and background activity; an alert anywhere in a window is not proof that an attack event was detected. Across all 20 main models, sixteen flag all three windows, two flag two windows and two flag none. These results are descriptive for one simulator, not event-level attack recall or a production false-positive rate.

## 6 Discussion

The experiments separate three questions that are often combined. A feature can shift, a model's explanation can shift, and a candidate model can change future detection. Similarity between the first two does not prove the third will improve. In this evaluation, coupling changes update schedules but does not consistently improve the dual policy.

Past-only behavioural context addresses a real information gap in isolated event fields. However, the observed context features can also amplify workload and cold-start differences. The combined ordinal static model ranks attack-labelled events poorly in the primary setting, while its adaptive variants produce very high benign false positives. Better context features may require actor-specific baselines, longer trusted history or different modelling, each evaluated with a new protocol. These results should not be used to claim that adding more features necessarily solves event ambiguity.

The historical guard and quarantine demonstrate measurable policy differences. They also expose an unresolved safety issue: frozen predicted-normal screening can admit attack-labelled rows, and historical checks cannot certify behaviour on future incidents. A selective update policy should be evaluated for deferred benign adaptation and missed security activity alongside reduced candidate exposure.

The external trace replay broadens source and attack-family coverage but supplies no event-level ground truth. The independently authored synthetic stream adds a documented benign baseline; its high alert rates reveal a transfer problem, but three mixed incident windows do not establish attack recall. The annotated CloudTrail study by Adediran and colleagues is a relevant possible future comparison, subject to data access and an audit of annotation and simulator-marker leakage [@adediran]. It is not used here. A stronger claim will require a separate labelled environment with representative benign workloads and a frozen prospective evaluation.

## 7 Limitations

The main labelled corpus comes from one controlled deployment. Date-separated sessions, repeated seeds and paired resamples are not independent organisations. The data were already inspected in earlier project work, so the revised protocol is exploratory. Broad historical coverage also changes fitting and reference sizes along with the training time span; it does not isolate workload diversity as a single causal variable.

Behavioural features describe only retained source records. Actor keys can group multiple sessions or fall back to coarse identities, and missing resources are incompletely observed. A first-seen flag is not inherently malicious. User-agent or identity patterns can also reflect simulator-specific characteristics, limiting transfer. One-hot attribution grouping is an additive signed sum rather than a coalition explanation.

The monthly intervention track has no verified attack labels and uses only month-level time in its scored export. The richer export has finer timestamps, but its 42,513-row sample remains unlabelled, source-order selected and non-independent of the original corpus. Its temporal features describe only retained samples rather than complete activity. Intervention masks and background proxy rates do not establish production detection. The contamination study mixes labelled source feature matrices into constructed pools, rather than executing an actual poisoning stream. The external trace replay lacks per-event labels, verified benign controls and representative continuous actor history. The separate synthetic baseline derives its benign period from simulator documentation, and its incident windows do not identify individual malicious records.

The comparison uses one anomaly-model family. ADWIN and Page Hinkley use fixed public defaults, not exhaustive tuning, and OWAD, XPE and HDDAF are not reimplemented as matched baselines. Candidate fitting is shared where possible, so recorded wall time is not independent per-policy production throughput. The system is an offline research pipeline, not a live AWS deployment.

## 8 Conclusion

Past-only behavioural context, attribution coupling and guarded adaptation are plausible components of cloud audit monitoring. In the evaluated data, their combination does not consistently improve the recall and false-positive trade-off. Some safeguards reduce the number of accepted attack-labelled candidates but do not eliminate contamination or establish future security retention.

The value of the current study lies in its controlled comparisons and failure analysis. Further work should obtain an independent labelled CloudTrail environment with representative benign behaviour, freeze choices before that evaluation, and test whether improved representations and update safeguards offer measurable incremental value.

## Reproducibility and data availability

The project repository is https://github.com/sani3055/DriftDetection. The versioned research evidence is currently retained locally and requires an archived release for independent replication. It includes code and archive hashes, tie-safe event partitions, per-window policy counts, candidate decisions, paired intervals, contamination conditions and unlabelled trace results. The labelled source is publicly described by ArielCyber [@clouddata]; the separate trace source is maintained by Splunk [@splunk].

The inherited monthly source is not redistributed with the manuscript because its original provenance and release permissions remain to be clarified. No live AWS actions are performed. The complete local automated test suite contains 93 passing tests.

## Acknowledgements

I thank Dr Badrinath N for project guidance.

## Use of AI assistance

AI assistance was used for implementation, literature discovery, drafting and verification of research artifacts. AI is not an independent human reviewer or a source of experimental ground truth. The author must verify the manuscript and follow the chosen journal's disclosure policy before submission.

## References

[[REFERENCES]]
