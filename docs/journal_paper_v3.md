Attribution Guided Adaptation in Cloud Audit Logs and Its Limits under Temporal Shift

Sanidhya Bhandari

Department of IoT, School of Computer Science and Engineering, Vellore Institute of Technology, Vellore, India

Abstract

An anomaly detector can recognise changes in cloud activity without knowing whether those changes justify retraining. This study tests whether alignment between feature distribution drift and SHAP attribution displacement improves adaptation decisions in AWS CloudTrail logs. A chronological evaluation scores each batch before updating and separates fitting, reference, calibration, historical guard and future test data. Thirteen policies are compared across 20 settings that vary categorical representation, event score calibration, seed and window size. All settings evaluate the same 11,531 later events from a controlled AWS deployment, including 3,126 attack labelled events. Under the ordinal representation and training cutoff, the static detector achieves recall 0.9485 with a false positive rate of 0.7187. Coupling raises recall to 0.9642 but also raises the false positive rate to 0.7713, lowering F1 from 0.4888 to 0.4775. One hot encoding and benign score calibration can instead suppress attack recall entirely. A retrospective audit finds that 16 seven field profiles contain both attack and benign events, demonstrating a representation limit that drift alignment cannot resolve by itself. A separate 336 unit controlled experiment on an inherited monthly corpus also shows no incremental coupling benefit. The contribution is a reproducible comparison and failure analysis, rather than a claim of improved detection. The findings identify historical workload coverage, score calibration and representation ambiguity as necessary considerations when interpreting attribution guided adaptation.

**Keywords** AWS CloudTrail; anomaly detection; SHAP; distribution drift; temporal evaluation; adaptive monitoring; categorical representation

1 Introduction

Cloud audit records describe actions performed by users, services and automated workloads. AWS CloudTrail records API activity and related identity and service information that can support incident investigation [1]. However, an unusual operation is not necessarily malicious. A new application can change normal API usage, and an attacker can perform an operation that is common in legitimate administration. An anomaly score therefore answers a narrower question than an incident label.

This distinction becomes important when a detector is updated automatically. Refusing every update can retain an obsolete description of normal activity. Updating whenever inputs change can absorb suspicious records into the normal model. A useful adaptation rule must justify its decisions on later predictions, not merely produce an interpretable alarm or improve the batch used for fitting.

Concept drift research distinguishes changes in distributions, labels and decision relationships [2, 3]. In streams without immediate outcome labels, input drift alone cannot establish deterioration in security detection. SHAP offers a description of how a fitted model uses its inputs [4, 5]. Comparing feature drift with explanation drift may help identify changes that affect model behaviour. It does not supply the missing security labels.

This work evaluates a feature attribution coupling gate. The gate requires substantial input drift, substantial explanation drift and alignment between the features driving those changes. The original motivation was that aligned changes might be more relevant to adaptation than either signal alone. I treat that motivation as a hypothesis rather than assume that alignment indicates an attack. The experiments retain negative outcomes and compare coupling with simpler score monitors and established streaming tests.

The study addresses four questions. Does coupling add useful future detection behaviour beyond separate magnitude gates? How sensitive are conclusions to categorical encoding and event score calibration? Can a historical guard prevent harmful updates without consulting test labels? What limits follow from representing an event through only seven fields? These questions are evaluated on a labelled, timestamped cloud log corpus and a separate controlled experiment constructed from an inherited monthly corpus.

The principal contribution is an auditable empirical analysis of attribution guided adaptation under temporal shift. The comparison includes matched forest capacity, prediction before update, earlier calibration, explicit candidate contamination auditing and uncertainty estimates that preserve short temporal blocks. A second contribution is the analysis of alignment saturation and label collisions in the chosen representation. Neither the use of SHAP with drift detection nor the combination of standard monitors is claimed as a new learning algorithm.

2 Related work

Isolation Forest isolates observations through random partitions and supplies a practical unsupervised anomaly baseline [6]. SHAP assigns contributions to a specified model output [4], and Tree SHAP supports efficient explanations for tree ensembles [5]. These methods explain model behaviour, not the causal intent of an AWS operation. Consequently, explanation consistency and security effectiveness require separate evaluation.

Kuppa and Le Khac propose a contrastive representation and nearest class mean approach to security drift and new class discovery [7]. Their experiments include withheld classes and adversarially introduced instances and concepts. This is relevant to the risk of treating every changing sample as trustworthy adaptation data. Their labelled network and URL setting differs from a frozen unsupervised CloudTrail detector, so their numerical results are not used as matched baselines here.

Lee and colleagues use SHAP descriptors and Mahalanobis distance to identify suspicious drift in a domain generation algorithm setting [8]. Their framework is designed to reduce dependence on labels during monitoring, while its validation uses labelled constructed data. This is direct prior work for explanation based drift signals. Their discussion identifies computational cost and the aggregation of individual signals as remaining limitations. My experiment instead evaluates whether feature level alignment changes future adaptation outcomes.

Li and colleagues investigate adaptation according to drift type [9]. OWAD addresses adaptation to normality shifts in security systems [10], while XPE connects explanations and distribution changes to performance estimation [11]. These studies establish that interpreting drift and responding to it are established research directions. Their objectives and supervision differ, and none is reproduced here as a supposedly equivalent numerical baseline.

Lara Gutierrez and colleagues study drift detection and adaptation in an AI security framework [12]. Maseno, Sun and Wang examine adversarial perturbations and explanation instability in recurrent network intrusion detectors [13]. Their work further rules out a broad novelty claim based on combining security monitoring with changing explanations. The question in this paper is narrower: whether a particular alignment gate offers incremental decision value under a shared CloudTrail evaluation protocol.

The main comparison includes ADWIN and Page Hinkley through River [14]. They receive the same frozen anomaly score stream rather than errors derived from attack labels. This supports a label independent runtime comparison, although their default parameters are not an exhaustive optimisation of either detector. The related work discussion is selective and does not claim systematic review coverage.

3 Data and chronological design

Timestamped external corpus

The native chronological evaluation uses the public ArielCyber cloud log sampling repository [15]. The source describes a controlled AWS deployment with executed attack scenarios. These are useful labelled security experiments, but they are not independent naturally occurring production incidents. All sessions in the analysis come from this source environment.

The benign base archive contains 16,495 records. Removing nine duplicated event identifiers leaves 16,486 unique events. The earliest day, 18 February 2026, supplies fitting and reference sets after chronological ordering and purging timestamp ties at the fitting boundary. The next day supplies calibration, and 20 February supplies a separate historical guard. Category vocabularies and the initial detector use fitting events only.

Table 1 Chronological data allocation

Test sessions are 4, 27 and 28 April 2026. They originate from one controlled AWS deployment, not three independent sites. Timestamp ties are purged at the fitting boundary.

| Partition | Events | Role |
| --- | --- | --- |
| 18 February fitting | 6,881 | Learn vocabulary and initial detector |
| 18 February reference | 2,949 | Frozen distributions and SHAP reference |
| 19 February calibration | 4,182 | Event cutoff and monitoring gates |
| 20 February guard | 2,474 | Candidate checks only |
| April test sessions | 11,531 | 3,126 attack and 8,405 benign events |

The mixed archive contains records earlier than the training cutoff. Those records are excluded instead of being treated as future observations. The retained portion contributes 7,315 events on 4 April. The separate archive named train_labeled_a contributes 35 events on 27 April and 4,181 events on 28 April, but is held out in this study despite its filename. All retained test events occur after the historical guard. Event identifiers are disjoint across archives.

Non overlapping event count windows preserve timestamp order and retain short tails. Windows reset at date and archive boundaries. At 128 events, the test has 92 windows across three sessions. Models also reset to the same baseline at session boundaries. This design measures within session adaptation; it does not simulate a single continuously deployed model across the long February to April gap.

Labels and attack names are unavailable to runtime gates, candidate screening and fitting. They are used after predictions for event metrics, window annotations and contamination audits. Historical records supplied as benign by the dataset are used to calibrate and guard models, so the overall design is not free of benign data assumptions.

Inherited monthly corpus

The inherited project CSV contains 1,939,207 rows and 18 columns, covering 45 months from February 2017 to October 2020. It has no independently verified attack labels. Its timestamp field supports month level partitioning, not event sequence reconstruction. The source is identified by a SHA 256 manifest; the audit found no malformed rows. Its provenance and redistribution rights require clarification before external release.

The chronological split contains 27 training months through April 2019, nine validation months through January 2020 and nine test months from February to October 2020. Existing saved score artifacts retain the first 1,000 records per month. These deterministic prefixes can be unrepresentative of full monthly activity. August 2019 accounts for approximately 69.5% of all source records, which further discourages treating event volume as balanced temporal coverage.

The repaired controlled experiment uses these prefixes rather than claim attack accuracy on the full unlabelled corpus. It fits a fresh forest on 27,000 training prefix rows, calibrates drift gates on nine validation prefixes and constructs interventions in eight consecutive test month pairs. This separates the monitoring month from the month evaluated after an update.

Representation and comparison factors

Each event contributes eventName, eventSource, awsRegion, userIdentitytype, errorCode, requestParametersinstanceType and a derived root user flag. Missing values use the normalisation contract. Account identifiers, resources, source addresses and action histories are absent. Two events with the same seven values are indistinguishable to a fixed event level model even if their security contexts differ.

Ordinal encoding maps categories to integer codes and unseen values to minus one. One hot encoding uses training categories and represents an unseen category by an all zero block. Both choices can lose distinctions among new values. For monitoring, raw category values are retained so that distinct unseen operations do not collapse into one drift category. This differs from the earlier project implementation that monitored encoded values.

The comparison also varies the event anomaly cutoff. The training offset condition uses the forest's own fitted threshold. The benign quantile condition uses the higher empirical 95th percentile of anomaly scores on earlier benign calibration data. Each candidate forest receives its own cutoff using that same earlier calibration set. Neither condition uses the current or future test batch to choose its cutoff.

Table 2 Declared comparison factors

The four representation by cutoff cells at seed 42 and 128 events are the main comparison. Sensitivity settings reuse the same events and cannot establish independent replication.

| Factor | Settings |
| --- | --- |
| Representation | Ordinal and one hot with training only vocabularies |
| Event cutoff | Training offset and earlier benign 95th percentile |
| Random seeds | 17, 42 and 73 at 128 events per window |
| Window sensitivity | 64 and 256 events at seed 42 |
| Policies | 13 policies in every setting |
| Total | 20 settings and 260 policy configurations |

The protocol was declared after earlier project experiments and before these runs. It is not external preregistration, and the labelled source corpus was already known to the project. All 20 settings are retained. No favourable encoding, seed or threshold is selected after testing and presented as a prespecified winner.

4 Monitoring and adaptation methods

Detector and explanation contract

Every baseline and candidate Isolation Forest has 100 trees, max_samples set to auto, contamination 0.05 and the setting's seed. The contamination parameter sets a training score threshold; it does not estimate attack prevalence. Anomaly scores are the negative scikit learn score_samples output, with larger values treated as more unusual [16].

TreeExplainer explains the Isolation Forest adapter's internal mean path output. Its contributions do not directly reconstruct an attack probability or the calibrated decision threshold. I check additivity against the adapter output. For one hot models, contributions are summed with sign within each original feature block. This retains additivity at seven features, but it is not a separate coalition SHAP or Owen value computation. The maximum residual across the 20 configurations is below 3.1 times ten to the power minus fourteen.

The baseline detector, explanation reference and category encoder remain frozen for monitoring. Deployed prediction models can change after accepted updates. This separates a stable monitoring coordinate system from changing prediction models, but it can also miss changes that would only be visible in explanations of a later deployed model.

Distribution and attribution signals

For each of the seven features, reference and current categorical counts are expanded over their joint support. Counts receive additive smoothing of ten to the power minus six and are normalised. With probabilities p and q, feature drift is measured by population stability index d. The batch feature signal F is its mean across seven fields.

[Editable equation 1 psi]

[Editable equation 2 feature]

Let Phi denote the empirical SHAP contribution distribution of a feature. Its displacement uses first Wasserstein distance divided by a reference scale. The scale is the larger of that feature's reference standard deviation and a common floor s. The floor is the larger of ten percent of the median positive reference standard deviation and ten to the power minus six. This avoids making an almost constant feature arbitrarily dominant through division by a tiny variance.

[Editable equation 3 wasserstein]

The attribution magnitude signal D combines the mean scaled distances, loss of overlap among the top three features by mean absolute attribution, and a Kendall rank disagreement term. In the equation, p is seven, J is top three Jaccard overlap and K is Kendall tau. Kendall tau compares the two vectors at matched feature positions, not the numeric indices of independently sorted arrays. Constant or undefined comparisons follow the implementation's explicit fallback.

[Editable equation 4 shap]

The cosine coupling signal C compares the seven feature drift values with changes in mean absolute SHAP contributions. Its value is zero when the norm product is below ten to the power minus twelve. A conservative variant takes the smaller of cosine and a centred correlation mapped to the unit interval, with zero for degenerate centred vectors.

[Editable equation 5 coupling]

Cosine is invariant to positive rescaling of either vector. If both changes concentrate on the same feature, alignment can equal one regardless of their absolute size or security meaning. This follows directly from the definition and is not a novel theorem. A benign change and an attack can therefore share the same coupling value. Separate magnitude gates prevent tiny aligned changes from triggering, but cannot remove this semantic ambiguity.

To describe concentration, I record the effective number of features for each drift or displacement vector. It equals zero for a zero vector and otherwise ranges from one to seven. Values near one indicate concentration rather than multiple independent pieces of security evidence.

[Editable equation 6 effective]

Update policies and safeguards

Feature only and SHAP only policies use their respective magnitude gates. Dual signal requires both. Coupled and conservative coupled additionally require their alignment gate. Each scalar threshold is the higher empirical 95th percentile of its earlier calibration windows, and comparisons are strictly greater than the threshold. These gates are reused unchanged on test windows.

The score Wasserstein policy monitors the frozen anomaly score distribution, normalised by its reference standard deviation with a numerical floor. ADWIN and Page Hinkley receive every bounded frozen anomaly score in timestamp order. Their states are warmed on calibration events and cloned at each test session. A batch requests an update if a streaming detector alarms during it. River 0.26.1 supplies ADWIN with delta 0.002 and its default window controls, and Page Hinkley with minimum instances 30, delta 0.005, threshold 50, alpha 0.9999 and two sided mode [14]. The code manifests retain the full parameter values.

Static never requests an update. Periodic requests one every fifth batch within a session. Guarded dual, guarded feature and guarded periodic isolate the effect of a historical candidate check. All policies predict the current batch with their currently deployed model before making an update decision. A requested candidate is trained using all 6,881 original fitting events plus current events predicted normal by the frozen baseline. At least ten current candidates are required. Reusing the full fitting matrix avoids confusing adaptation with discarding most historical training data.

The guard checks the candidate on the separate historical benign set and on fixed high scoring fitting anchors. Its historical alarm rate cannot exceed the baseline by more than 0.01. Its mean anomaly score on the highest scoring five percent of fitting rows cannot fall below the baseline by more than 0.02. Both margins are fixed before these experiments. Neither constraint uses test labels. These checks preserve aspects of historical behaviour; they do not certify future attack recall or remove contaminated candidates reliably.

Controlled future month interventions

The primary corpus experiment has seven scenario families: stable, routine region change, routine identity change, routine Lambda activity, privilege activity, defence interference and credential activity. Security tuples use AttachUserPolicy with IAM and Root, DeleteTrail with CloudTrail and IAMUser, and CreateAccessKey with IAM and IAMUser. Root flags are recomputed consistently. Instance type becomes NotApplicable and error uses the inherited Unknown placeholder. The generator changes whole API and service tuples rather than contradictory individual fields.

For each of eight test month transitions, seeds 17, 42 and 73 sample 200 monitoring rows and 200 rows from the next month. Intervention intensities are 0.125 and 0.25. The actual changed row mask is computed after replacement, rather than assuming every selected row differs. Independent perturbation randomness is used for next month rows. Across seven families, this gives 336 counterfactual units per policy.

Candidates are trained on all 27,000 training prefix records plus current baseline predicted normal monitoring rows. Future rows and their masks never enter fitting or gates. Every unit restarts from the original model; periodic uses a declared every fifth unit schedule rather than simulate a deployed monthly stream. ADWIN and Page Hinkley are omitted because the source does not establish within month event order. Saved unknown category codes cannot be decoded into distinct original names, and this limitation is retained explicitly.

5 Evaluation and uncertainty

External outcomes are pooled event precision, attack recall, F1 and benign false positive rate, together with update requests, actual refits, guard rejections and candidate contamination. Candidate labels are consulted only after runtime decisions. All settings predict the same 11,531 events. Ratios with no denominator are undefined, not silently zeroed. A final batch can request or complete an update without any later observation in its session; such work is not evidence of future benefit.

Controlled outcomes instead use actual changed rows in intended security families as positives. Routine and stable scenarios have no positive attack targets. Unchanged background records have no verified security label. The reported negative class rate is therefore a mask relative proxy, and its F1 is a pooled intervention score. It is not comparable directly with external attack detection F1 or a diagnosis macro F1.

For descriptive uncertainty, paired window confusion counts are resampled in contiguous moving blocks within each of the three sessions [17]. The primary block length is five windows, with lengths two and ten as sensitivity checks. The same indices are applied to every policy in each of 2,000 resamples, using seed 20261030. Intervals use percentile endpoints of pooled metric differences. This preserves local blocks, but overlapping resampling blocks, small sessions and nonstationarity limit inferential interpretation. The calculation is not a population coverage guarantee or a test across independent deployments.

Gate failure analysis compares calibration, attack free test and attack containing test windows. Post hoc ranking AUC is used only as a description of those saved signals. It does not retune gates, train a new classifier or establish future ranking performance. The retrospective profile collision diagnostic likewise uses labels after the experiment and is separated from runtime modelling.

6 Results

Ordinal encoding with the training cutoff

The static model detects most attack events, but also flags a large fraction of benign events. Dual updating increases recall while worsening false positives. Coupling makes fewer requests and avoids some of that increase, but still does not improve the static F1. The conservative gate has identical outcomes to coupling in this cell. A lower request count must therefore not be confused with established security improvement.

Table 3 Future event results for ordinal training offset

Rates pool confusion counts over the identical 11,531 events. Requests and accepted refits differ when candidates are insufficient or rejected. A terminal refit has no later observation in its session.

| Policy | Recall | FPR | F1 | Requests | Refits |
| --- | --- | --- | --- | --- | --- |
| Static | 0.9485 | 0.7187 | 0.4888 | 0 | 0 |
| Periodic | 0.9786 | 0.8632 | 0.4552 | 17 | 9 |
| Feature only | 0.9837 | 0.8807 | 0.4521 | 78 | 34 |
| SHAP only | 0.9837 | 0.8871 | 0.4503 | 91 | 48 |
| Dual signal | 0.9837 | 0.8807 | 0.4521 | 77 | 34 |
| Coupled | 0.9642 | 0.7713 | 0.4775 | 7 | 4 |
| Conservative coupled | 0.9642 | 0.7713 | 0.4775 | 7 | 4 |
| Score Wasserstein | 0.9786 | 0.7739 | 0.4821 | 53 | 12 |
| ADWIN score | 0.9757 | 0.7886 | 0.4764 | 11 | 4 |
| Page Hinkley score | 0.9485 | 0.7187 | 0.4888 | 1 | 0 |
| Guarded dual | 0.9757 | 0.8713 | 0.4519 | 77 | 14 |
| Guarded feature | 0.9757 | 0.8713 | 0.4519 | 78 | 14 |
| Guarded periodic | 0.9613 | 0.8075 | 0.4652 | 17 | 4 |

The guarded policies reject some candidates, yet guarded dual still has a false positive rate of 0.8713. Historical guard success does not imply later benign compatibility. ADWIN produces a different update schedule but does not resolve the tradeoff. Page Hinkley requests one update without an eligible completed refit and consequently matches static predictions. None of these observations establishes universal superiority of a monitor.

Table 4 Paired differences from static under ordinal training offset

Session stratified moving blocks of five windows, 2,000 paired resamples. Positive recall and negative FPR are favourable. These intervals describe resampling within this corpus and are not population guarantees. Block lengths two and ten are retained in the supplement.

| Policy | Endpoint | Difference | Descriptive 95% interval |
| --- | --- | --- | --- |
| ADWIN score | FPR | 0.0698 | [0.0170, 0.1268] |
| ADWIN score | Recall | 0.0272 | [0.0084, 0.0490] |
| Coupled | FPR | 0.0526 | [0.0050, 0.1043] |
| Coupled | Recall | 0.0157 | [0.0034, 0.0332] |
| Dual signal | FPR | 0.1619 | [0.1016, 0.2307] |
| Dual signal | Recall | 0.0352 | [0.0184, 0.0531] |
| Guarded dual | FPR | 0.1525 | [0.0897, 0.2213] |
| Guarded dual | Recall | 0.0272 | [0.0084, 0.0490] |

The paired intervals describe the observed increases in recall and false positives. They do not justify an improvement claim based solely on recall. Full interval outputs retain all policies at block length five and central comparisons at lengths two and ten, including settings where all policies have zero recall. Such degenerate results are reported rather than excluded from the analysis.

Representation and calibration sensitivity

One hot encoding under the training cutoff lowers benign alarms but also sharply lowers attack recall. Dual and SHAP updating recover only a small fraction of attack events. This rules out claiming that nominally appropriate encoding alone solves transfer. Unseen values represented by all zero blocks can have very different anomaly behaviour from minus one ordinal values.

Table 5 Future event results for one hot training offset

Rates pool confusion counts over the identical 11,531 events. Requests and accepted refits differ when candidates are insufficient or rejected. A terminal refit has no later observation in its session.

| Policy | Recall | FPR | F1 | Requests | Refits |
| --- | --- | --- | --- | --- | --- |
| Static | 0.0422 | 0.2390 | 0.0501 | 0 | 0 |
| Periodic | 0.0435 | 0.2182 | 0.0534 | 17 | 17 |
| Feature only | 0.0710 | 0.2320 | 0.0838 | 78 | 78 |
| SHAP only | 0.0710 | 0.2134 | 0.0863 | 91 | 91 |
| Dual signal | 0.0710 | 0.2320 | 0.0838 | 77 | 77 |
| Coupled | 0.0694 | 0.2358 | 0.0815 | 49 | 49 |
| Conservative coupled | 0.0694 | 0.2358 | 0.0815 | 49 | 49 |
| Score Wasserstein | 0.0387 | 0.2385 | 0.0461 | 34 | 34 |
| ADWIN score | 0.0416 | 0.1913 | 0.0535 | 6 | 6 |
| Page Hinkley score | 0.0422 | 0.2390 | 0.0501 | 1 | 1 |
| Guarded dual | 0.0704 | 0.2351 | 0.0827 | 77 | 51 |
| Guarded feature | 0.0704 | 0.2351 | 0.0827 | 78 | 51 |
| Guarded periodic | 0.0435 | 0.1913 | 0.0559 | 17 | 11 |

Earlier benign score calibration changes the problem again. Under ordinal encoding, static recall falls almost to zero, while adaptive policies can recover some recall at the cost of additional false positives. Calibration controls an empirical historical tail, not a stable security error budget. A changed benign workload can move the calibrated cutoff beyond many later attack scores.

Table 6 Future event results for ordinal benign quantile

Rates pool confusion counts over the identical 11,531 events. Requests and accepted refits differ when candidates are insufficient or rejected. A terminal refit has no later observation in its session.

| Policy | Recall | FPR | F1 | Requests | Refits |
| --- | --- | --- | --- | --- | --- |
| Static | 0.0006 | 0.0101 | 0.0012 | 0 | 0 |
| Periodic | 0.3877 | 0.2996 | 0.3536 | 17 | 17 |
| Feature only | 0.4523 | 0.3586 | 0.3744 | 78 | 78 |
| SHAP only | 0.4523 | 0.3535 | 0.3765 | 91 | 91 |
| Dual signal | 0.4523 | 0.3586 | 0.3744 | 77 | 77 |
| Coupled | 0.1043 | 0.1907 | 0.1290 | 7 | 7 |
| Conservative coupled | 0.1043 | 0.1907 | 0.1290 | 7 | 7 |
| Score Wasserstein | 0.4082 | 0.3328 | 0.3545 | 53 | 53 |
| ADWIN score | 0.2662 | 0.3083 | 0.2541 | 11 | 11 |
| Page Hinkley score | 0.0320 | 0.0871 | 0.0505 | 1 | 1 |
| Guarded dual | 0.2604 | 0.2358 | 0.2749 | 77 | 15 |
| Guarded feature | 0.2604 | 0.2358 | 0.2749 | 78 | 16 |
| Guarded periodic | 0.0982 | 0.1136 | 0.1399 | 17 | 3 |

With one hot encoding and benign quantile calibration, every policy has zero attack recall in the main cell. Static and coupled policies also have zero false positives. This is a detector that misses all attack events, not a perfect detector. Other policies make some benign errors without recovering positives. A false positive only interpretation would therefore reverse the practical conclusion.

Table 7 Future event results for one hot benign quantile

Rates pool confusion counts over the identical 11,531 events. Requests and accepted refits differ when candidates are insufficient or rejected. A terminal refit has no later observation in its session.

| Policy | Recall | FPR | F1 | Requests | Refits |
| --- | --- | --- | --- | --- | --- |
| Static | 0.0000 | 0.0000 | 0.0000 | 0 | 0 |
| Periodic | 0.0000 | 0.0061 | 0.0000 | 17 | 17 |
| Feature only | 0.0000 | 0.0027 | 0.0000 | 78 | 78 |
| SHAP only | 0.0000 | 0.0033 | 0.0000 | 91 | 91 |
| Dual signal | 0.0000 | 0.0027 | 0.0000 | 77 | 77 |
| Coupled | 0.0000 | 0.0000 | 0.0000 | 49 | 49 |
| Conservative coupled | 0.0000 | 0.0000 | 0.0000 | 49 | 49 |
| Score Wasserstein | 0.0000 | 0.0000 | 0.0000 | 34 | 34 |
| ADWIN score | 0.0000 | 0.0001 | 0.0000 | 6 | 6 |
| Page Hinkley score | 0.0000 | 0.0000 | 0.0000 | 1 | 1 |
| Guarded dual | 0.0000 | 0.0000 | 0.0000 | 77 | 68 |
| Guarded feature | 0.0000 | 0.0000 | 0.0000 | 78 | 69 |
| Guarded periodic | 0.0000 | 0.0000 | 0.0000 | 17 | 12 |

Figure 1 Detection tradeoffs in the four main comparison cells. Each point is a policy; overlapping points share outcomes. A lower false positive rate is useful only in conjunction with adequate attack recall. All panels use the same events and scales.

Across all 20 settings, the source events are unchanged. Seed and window sensitivity measure robustness within that source, not generalisation to independent incidents. The complete 260 row results file accompanies the analysis so that the four main cells cannot conceal unfavourable settings. The evidence supports substantial sensitivity to modelling choices rather than a portable preferred update policy.

Alignment discrimination and gate saturation

Earlier benign alignment is already high: the ordinal median is 0.9105 and its coupling gate is 0.9566. The later attack containing median is lower, at 0.8447, rather than exceeding this gate. Only 7 of 34 attack containing windows pass the full coupled rule, while no attack free window does in the main ordinal cell. This selective behaviour is informative but misses many windows with attack events.

The one hot representation has a lower calibration gate, approximately 0.9356. It admits about 70.6% of attack containing windows, but also 43.1% of attack free windows. Window annotations describe whether any labelled attack event occurs; they do not prove that every observed shift in such a window was caused by the attack.

Figure 2 Frozen cosine alignment by representation and window annotation. Calibration is earlier benign activity. Test windows are labelled attack free or attack containing only after runtime decisions. Dashed lines are the unchanged calibration gates. Overlap prevents interpreting alignment as a security probability.

Post hoc cosine ranking AUC is 0.8073 under ordinal encoding and 0.7155 under one hot encoding on these same windows. These descriptive rankings are more promising than some individual magnitude scores, but they do not demonstrate an effective frozen decision threshold or improved adaptation. Changing the threshold direction or quantile after seeing these labels would require a new evaluation, not a revised claim on the same data.

Representation ambiguity and contaminated candidates

The seven field audit produces only 123 unique profiles among all 11,531 test events. Sixteen profiles contain both labels, covering 3,069 attack and 6,098 benign events. For a single deterministic classifier of these profiles on this pooled sample, summing the minority label count within each profile gives 2,003 unavoidable empirical errors. This is a property of the retained representation and sample, not a population Bayes error estimate or a bound on models with time or identity history.

Table 8 Retrospective feature collision diagnostic

This diagnostic uses test labels after evaluation. The minimum applies to a single deterministic classifier of these seven fields on this pooled sample. It is not a learned classifier, a population Bayes error bound, or a bound on adaptive models using time or history.

| Quantity | Count |
| --- | --- |
| Evaluated events | 11,531 |
| Unique seven feature profiles | 123 |
| Profiles with both labels | 16 |
| Attack events in mixed profiles | 3,069 |
| Benign events in mixed profiles | 6,098 |
| Minimum pooled errors for a fixed profile classifier | 2,003 |

Coupling cannot recover security context absent from these inputs. In the main ordinal training cutoff cell, coupled updates accept 46 current candidate rows across completed refits; 41 are attack labelled in the later audit. A frozen detector's normal prediction is therefore not a trustworthy benign label. The result explains why alignment and conservative request counts do not imply a safe training set.

Normal workload coverage is also narrow. Earlier fitting activity is dominated by decrypting, secret access and database operations, whereas later benign activity includes different mixes of identity, instance and systems management calls. These workload differences can change both scores and explanations. The observed association motivates broader historical coverage, but this paper does not test a newly expanded training set or claim that coverage alone explains every error.

Repaired controlled experiment

The repaired experiment removes same batch evaluation and inconsistent API service substitutions. It still does not establish an incremental coupling benefit. Feature, dual, score and coupled magnitude combinations request no updates at the fixed validation gates. SHAP only requests 33 and periodic requests 67, producing small differences in the background proxy rate. Coupled predictions equal static predictions throughout this controlled run.

Table 9 Future month controlled intervention results

336 counterfactual units per policy. Positive targets are actual changed rows in intended security scenarios. Unchanged rows are unlabelled background, so the negative class rate is not a verified benign event FPR. Scores are pooled across repeated counterfactual evaluations, not unique independent events.

| Policy | Mask recall | Mask FPR proxy | Pooled F1 | Refits |
| --- | --- | --- | --- | --- |
| Static | 0.3333 | 0.1037 | 0.2646 | 0 |
| Periodic | 0.3354 | 0.1042 | 0.2653 | 67 |
| Feature only | 0.3333 | 0.1037 | 0.2646 | 0 |
| SHAP only | 0.3333 | 0.1019 | 0.2667 | 33 |
| Dual signal | 0.3333 | 0.1037 | 0.2646 | 0 |
| Coupled | 0.3333 | 0.1037 | 0.2646 | 0 |
| Conservative coupled | 0.3333 | 0.1037 | 0.2646 | 0 |
| Score Wasserstein | 0.3333 | 0.1037 | 0.2646 | 0 |

Pooled intervention recall is one third for static and coupled policies. That result concerns the synthetic changed row targets, not verified attacks in the inherited data. Shared month pairs, seeds and overlapping source rows prevent treating 336 units as 336 independent incidents. This controlled comparison uses the training offset classification condition only.

7 Discussion

The central distinction is between a monitor that detects changes and an adaptation policy that improves later security decisions. Coupling can rank certain attack containing windows above attack free windows without producing a useful frozen gate. Even a useful gate would not guarantee that the candidate data are safe or that the refitted model preserves the relevant boundary. These stages should be evaluated separately rather than collapsed into one explanation score.

The representation audit provides a concrete reason for caution. Attack and benign activity frequently share the selected event attributes. Adding more explanation statistics to the same seven fields cannot restore a resource, actor history or sequence that was discarded before modelling. An extension with past only identity behaviour and resource context is therefore a justified next experiment. It would need a new leakage audit, because identifiers and attack labels can otherwise encode scenario membership rather than transferable behaviour.

The historical guard is useful as an auditable rejection mechanism, but its tests preserve only two historical properties. It cannot ensure security retention when anchors are unlabelled or protect against a future workload absent from its benign day. Candidate contamination remains an evaluation concern. Trusted delayed labels, separate incident replay or a genuinely independent holdout would be stronger evidence for update safety than a favourable historical score check alone.

These results also change how the original project should be described. Earlier same batch controlled comparisons cannot establish future improvement, and target batch threshold recalibration cannot establish transfer to later windows. The revised protocol addresses those design defects without overwriting the old evidence. Its negative results are research findings only to the extent that their protocol, source restrictions and alternatives are stated clearly.

8 Limitations

The labelled evaluation has one controlled deployment and three date separated sessions. Its events and attack families are correlated. Neither block resampling nor additional forest seeds creates independent sites. The dataset was already inspected during earlier project work, and the v3 protocol follows those observations. The current results are therefore procedural holdout comparisons, not blind confirmation on an untouched corpus.

The inherited corpus has no verified attack outcomes and only monthly timestamps in the used export. Prefix sampling, unrecoverable unknown category names and intervention design limit its corroborating role. Stable and routine interventions do not prove the underlying records benign. The controlled gates compare 1,000 row validation prefixes with 200 row monitoring samples; sample size can affect empirical PSI and remains an additional calibration limitation. Only the training offset condition has been executed for that controlled experiment.

The comparison uses one anomaly model family and default streaming monitor parameters. It does not reproduce OWAD, XPE, HDDAF or all recent drift adaptation algorithms. One hot grouping preserves additivity but changes feature dependence and can cancel signed contributions within a block. Ordinal codes introduce artificial distances. Neither representation is a definitive model of cloud behaviour.

Wall time and component timings are retained in run manifests, but shared candidate fits and cached predictions make them unsuitable for claims of independent policy throughput. The system is an offline local research pipeline, not a live AWS security deployment. Production latency, permissions, adversarial manipulation of monitors and analyst workload require separate evaluation.

9 Conclusion

Feature attribution coupling provides an interpretable description of which input changes coincide with changes in a detector's explanations. In the evaluated CloudTrail setting, it does not consistently improve later attack detection. Encoding and historical score calibration can change results more than the update gate, including a condition with zero false positives and zero attack recall. Mixed label feature profiles and contaminated predicted normal candidates further limit automatic adaptation.

The study contributes a reproducible temporal comparison and explicit failure mechanisms for an otherwise plausible monitoring rule. The next useful test is an independently evaluated representation with past only behavioural context and broader benign coverage. Until that evidence exists, coupling should remain a diagnostic signal for investigation rather than a security label or an autonomous retraining guarantee.

Reproducibility and data availability

The project repository is https://github.com/sani3055/DriftDetection. Versioned v3 artifacts are currently retained locally and require an archived release for independent replication. They include 20 configuration manifests, pooled and session counts, per window predictions and decisions, paired block intervals, gate diagnostics and the controlled future month benchmark. Code hashes, source archive hashes and chronology checks identify each run. The local verification run completed 73 automated tests.

The labelled data are obtained from their original public repository [15]. The inherited monthly source is not redistributed with this manuscript; its provenance and permissions remain a release limitation. Outcomes from older protocols are retained separately and are not substituted for v3 findings.

Acknowledgements

I thank Dr Badrinath N for project guidance.

Use of AI assistance

AI assistance was used for code development, literature discovery, drafting and checking research artifacts. It is not an independent human reviewer or a source of experimental ground truth. The author must verify the manuscript and follow the selected journal's disclosure policy before submission.

References

[1] Amazon Web Services. Understanding CloudTrail events. AWS CloudTrail User Guide, 2026. Accessed 28 October 2026. https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-events.html

[2] João Gama, Indrė Žliobaitė, Albert Bifet, Mykola Pechenizkiy and Abdelhamid Bouchachia. A survey on concept drift adaptation. ACM Computing Surveys, 2014, 46(4), 44:1–44:37. https://doi.org/10.1145/2523813

[3] Shruti Arora, Rinkle Rani and Nitin Saxena. A systematic review on detection and adaptation of concept drift in streaming data using machine learning techniques. WIREs Data Mining and Knowledge Discovery, 2024, 14(4), e1536. https://doi.org/10.1002/widm.1536

[4] Scott M. Lundberg and Su-In Lee. A unified approach to interpreting model predictions. Advances in Neural Information Processing Systems, 2017, 30. https://proceedings.neurips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html

[5] Scott M. Lundberg, Gabriel Erion, Hugh Chen, Alex DeGrave, Jordan M. Prutkin, Bala Nair, Ronit Katz, Jonathan Himmelfarb, Nisha Bansal and Su-In Lee. From local explanations to global understanding with explainable AI for trees. Nature Machine Intelligence, 2020, 2, 56–67. https://doi.org/10.1038/s42256-019-0138-9

[6] Fei Tony Liu, Kai Ming Ting and Zhi-Hua Zhou. Isolation forest. Proceedings of the Eighth IEEE International Conference on Data Mining, 2008, 413–422. https://doi.org/10.1109/ICDM.2008.17

[7] Aditya Kuppa and Nhien-An Le-Khac. Learn to adapt: Robust drift detection in security domain. Computers and Electrical Engineering, 2022, 102, 108239. https://doi.org/10.1016/j.compeleceng.2022.108239

[8] Yongsoo Lee, Yeeun Lee, Eungyu Lee and Taejin Lee. Explainable artificial intelligence-based model drift detection applicable to unsupervised environments. Computers, Materials and Continua, 2023, 76(2), 1701–1719. https://doi.org/10.32604/cmc.2023.040235

[9] Jinpeng Li, Hang Yu, Zhenyu Zhang, Xiangfeng Luo and Shaorong Xie. Concept drift adaptation by exploiting drift type. ACM Transactions on Knowledge Discovery from Data, 2024, 18(4), 96:1–96:22. https://doi.org/10.1145/3638777

[10] Dongqi Han, Zhiliang Wang, Wenqi Chen, Kai Wang, Rui Yu, Su Wang, Han Zhang, Zhihua Wang, Minghui Jin, Jiahai Yang, Xingang Shi and Xia Yin. Anomaly detection in the open world: Normality shift detection, explanation, and adaptation. Network and Distributed System Security Symposium, 2023. https://doi.org/10.14722/ndss.2023.24830

[11] Thomas Decker, Alexander Koebler, Michael Lebacher, Ingo Thon, Volker Tresp and Florian Buettner. Explanatory model monitoring to understand the effects of feature shifts on performance. Proceedings of the 30th ACM SIGKDD Conference on Knowledge Discovery and Data Mining, 2024, 550–561. https://doi.org/10.1145/3637528.3671959

[12] Antonio Lara-Gutierrez, Carmen Fernandez-Gago and Jose A. Onieva. A Framework for Drift Detection and Adaptation in AI-driven Anomaly and Threat Detection Systems. International Journal of Information Security, 2025, 24, 199. https://doi.org/10.1007/s10207-025-01118-9

[13] Elijah M. Maseno, Yanxia Sun and Zenghui Wang. Detecting adversarial evasion in deep learning intrusion detection systems using explainable AI. International Journal of Information Security, 2026, 25, 125. https://doi.org/10.1007/s10207-026-01299-x

[14] River contributors. ADWIN and PageHinkley API documentation. River documentation, 2026. https://riverml.xyz/dev/api/drift/ADWIN/ ; https://riverml.xyz/dev/api/drift/PageHinkley/

[15] ArielCyber. Cloud Log Sampling Dataset. GitHub repository, 2026. Accessed 28 October 2026. https://github.com/ArielCyber/cloud_log_sampling

[16] Fabian Pedregosa, Gaël Varoquaux, Alexandre Gramfort, Vincent Michel, Bertrand Thirion, Olivier Grisel, Mathieu Blondel, Peter Prettenhofer, Ron Weiss, Vincent Dubourg, Jake Vanderplas, Alexandre Passos, David Cournapeau, Matthieu Brucher, Matthieu Perrot and Édouard Duchesnay. Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 2011, 12, 2825–2830. https://jmlr.org/papers/v12/pedregosa11a.html

[17] Hans R. Kunsch. The jackknife and the bootstrap for general stationary observations. The Annals of Statistics, 1989, 17(3), 1217-1241. https://doi.org/10.1214/aos/1176347265
