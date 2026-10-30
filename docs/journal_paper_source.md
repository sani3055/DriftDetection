# SHAP Guided Drift Diagnosis for Adaptive Anomaly Detection in AWS CloudTrail

Sanidhya Bhandari

Department of IoT, School of Computer Science and Engineering, Vellore Institute of Technology, Vellore, India

## Abstract

An anomaly detector can react to changing cloud workloads even when the change is operationally routine. Updating the detector whenever its inputs shift can therefore be unnecessary, while delaying an update can leave it poorly matched to current activity. This study evaluates a CloudTrail monitoring pipeline that combines feature distribution drift, SHAP attribution drift and feature-level alignment. The alignment score couples a vector of categorical population stability indices with changes in mean absolute SHAP attribution. The study separates observations from an unlabelled corpus of 1,939,207 records across 45 months, controlled perturbation experiments, and tests on an independent labelled cloud-log corpus. Seven controlled scenario families and ten held-out perturbation seeds produce 70 paired units per update policy. Relative to a static detector, dual-signal adaptation reduces mean false-positive rate from 0.4282 to 0.3397, with a paired difference of −0.088478 and a bootstrap 95% interval of [−0.127232, −0.056106]. An F1 improvement is not established. Coupling and conservative coupling match the simpler dual and SHAP-only policies in this benchmark. On a retrospective external checkpoint, the source coupling threshold identifies only one of ten security scenario windows. Label-free recalibration separates the current batch, but provides no prospective recovery evidence. The findings support a reproducible diagnostic protocol and expose the limits of transferring alignment thresholds. They do not establish production security effectiveness or a general performance advantage for coupling.

**Keywords** AWS CloudTrail; anomaly detection; distribution drift; SHAP; model adaptation; attribution feature coupling; external validation

## 1 Introduction

AWS CloudTrail records activity associated with identities, services and resources in an AWS account [@aws]. These records support security analysis, but the same API operation can occur in both legitimate administration and an attack. The distribution of activity also changes when an organisation introduces services, changes regions or modifies its automation. An anomaly detector trained on historical records may then issue alerts that reflect a change in workload rather than an incident. Determining when to update that detector is a different problem from identifying an unusual event.

Research on concept drift distinguishes changes in the data-generating process from the mechanisms used to detect and respond to them [@gama; @arora]. In an unlabelled operational stream, an observed change in inputs does not establish a change in the relationship between inputs and security outcomes. This distinction matters here because the primary CloudTrail corpus contains no verified attack labels. We use the term distribution drift for directly measured changes, and retain security-related labels only for explicitly defined experimental scenarios.

Isolation Forest provides a practical unsupervised baseline by isolating observations through random partitions [@isof]. SHAP decomposes a model output into feature contributions [@shap]. Together, these tools allow two complementary questions: did the event distribution change, and did the model's attribution profile change? Their combination is already consistent with earlier work on detecting, explaining and adapting to normality shifts in security systems [@han]. The remaining question is whether a more explicit comparison of the features involved adds decision value.

We examine attribution feature coupling: the alignment between per-feature distribution drift and per-feature attribution displacement. A high alignment score means that the two vectors concentrate on similar features. It does not establish that the change is malicious, that a feature caused an incident, or that retraining will improve future predictions. Magnitude gates remain necessary because two very small vectors can point in the same direction. The proposed use of coupling is therefore a testable decision rule rather than a replacement for security ground truth.

The study asks three questions. First, does adding coupling to feature and attribution magnitude gates change update decisions in controlled CloudTrail scenarios? Second, do source-calibrated gates transfer to a separate cloud-log corpus? Third, how do detector choice, sample size and assumed operational costs affect the conclusions? We answer these questions without merging the unlabelled monthly observations, controlled row masks and external attack annotations into a single accuracy claim.

The contributions are a feature-aligned diagnosis rule with explicit zero-vector handling; a reproducible protocol that separates monthly observation from controlled diagnosis and update evaluation; and an empirical account of neutral coupling results and failed threshold transfer. The study also reports a small transductive recalibration experiment as an exploratory result. Standard components such as cosine similarity, Isolation Forest and SHAP are not claimed as new algorithms. The contribution lies in their CloudTrail-specific formulation and the evidence used to test its limits.

## 2 Related Work

Kuppa and Le-Khac study robust drift detection in security applications and combine detection with recursive updating [@kuppa]. Han and colleagues introduce OWAD, which detects, explains and adapts to normality shifts in security anomaly detection [@han]. These studies establish that integrating drift monitoring and adaptation is prior work. Our experiment uses a different event representation and tests whether attribution-feature alignment changes the behaviour of a lightweight update controller.

Lee and colleagues use SHAP-based evidence to detect model drift in unsupervised cybersecurity settings [@lee]. Their application concerns domain generation algorithm detection, rather than CloudTrail events. Their work rules out treating explanation drift itself as the novelty of the present study. We instead examine how explanation drift relates to the features whose marginal distributions changed, and retain simpler feature-only and attribution-only policies as internal comparisons.

Li and colleagues propose Type-LDA, which identifies drift type and a change point to guide adaptation [@li]. The drift-type identifier is pretrained on examples with known types. Our runtime diagnosis uses measured distributions and attributions rather than a learned drift-type classifier. Nevertheless, the present magnitude and alignment thresholds are selected using labelled controlled validation scenarios. The runtime score is label-free; the complete development procedure is not wholly unsupervised.

Decker and colleagues combine optimal transport and Shapley values in Explanatory Performance Estimation to attribute estimated performance change to feature shifts [@decker]. This provides a related formulation of the link between changing inputs and model effects. Their performance-estimation objective differs from our update-gating objective. We neither reproduce XPE nor infer superiority over it from experiments on a different dataset.

Maseno, Sun and Wang examine SHAP explanation instability under adversarial evasion in recurrent network intrusion detection models [@maseno]. Their findings show that explanation displacement can support a secondary security signal, while their supervised traffic setting differs from the unlabelled CloudTrail observations used here. AWS documentation also describes feature-attribution monitoring using ranking comparisons [@awsattr]. We therefore position coupling as a restricted empirical question, not the first use of attribution changes for monitoring.

The broader reviews by Gama and colleagues and Arora and colleagues emphasise the importance of matching drift assumptions, adaptation strategies and evaluation protocols [@gama; @arora]. Our literature discussion is selective rather than a systematic review. The experiments compare implementations within one shared protocol; results from the cited studies are not imported as numerical baselines. This avoids implying a matched comparison where the data, supervision and decision units differ.

## 3 Data and Evaluation Design

### 3.1 Primary corpus and temporal partition

The primary source is an existing CloudTrail-style CSV inherited from the project dataset. Its audit records 1,939,207 rows, 18 source columns, a file size of 830,904,812 bytes and no malformed rows detected by the audit. The available eventTime values resolve only to months, from February 2017 to October 2020. No column provides independently verified attack labels. The source file is read-only and is identified by a SHA-256 manifest rather than redistributed with the manuscript.

The chronological partition contains 27 training months, nine validation months and nine test months. Training ends in April 2019; the validation period spans May 2019 to January 2020, and the test period spans February to October 2020. The baseline fits 251,613 records from the training period. August 2019 contains 1,347,680 records, approximately 69.5% of the full corpus. Such concentration makes global event counts a poor substitute for per-window analysis and makes representative sampling an important validity concern.

[[TABLE:protocol]]

We retain up to 1,000 scored records per month using a deterministic prefix in source order, and explain the first 200 retained records per month. The resulting SHAP artifact contains 9,000 explained rows. The month partition describes real-data observation. It does not mean that the controlled security scenarios were drawn from the nine calendar test months: their reference rows come from training-period samples, while held-out perturbation seeds define their experimental test split.

A richer export from the same underlying corpus contains finer timestamps. It is recorded separately as a possible source for a future event-sequence study. It is not counted as an independent dataset or used to imply that the current monthly experiment validates session reconstruction.

### 3.2 Event representation

The detector receives eventName, eventSource, awsRegion, userIdentitytype, errorCode, requestParametersinstanceType and a derived isRoot flag. Categorical vocabularies are fitted only on training months. Missing values are represented as Unknown, and unseen categories receive code −1. The root flag is derived from the identity type before normal event encoding. Account identifiers, access-key identifiers and source IP addresses are excluded from the seven-feature model.

Ordinal encoding preserves compatibility with the existing detector but imposes artificial ordering on nominal categories. Different unseen operations can also collapse to the same −1 code. We retain these choices to evaluate the implemented pipeline consistently, while treating them as limitations rather than claiming that the representation is optimal.

### 3.3 Controlled scenarios and evaluation units

The controlled benchmark takes the first 200 encoded rows from the ordered training-score sample as a fixed reference matrix. Every scenario starts from a copy of that same matrix. A seeded intervention replaces one or two fields in selected rows. The primary field affects 25% of rows; a secondary field, when present, affects 12.5% of rows selected separately. These selections may overlap. A stable scenario leaves the reference unchanged.

[[TABLE:scenarios]]

Validation uses seeds 0–4 and testing uses seeds 5–14. Thus, seven families produce 35 validation units and 70 held-out test units per policy. The seeds alter intervention selections rather than supplying independent reference datasets. A scenario-level category labels the intended intervention family. For row-level evaluation, selected intervention indices are positive only in security-related families; all rows in stable and benign families are negative. The mask records selected indices, including possible replacement by a value already present. These targets are experimental annotations, not confirmed malicious actions.

Security-oriented API names are chosen to represent privilege, defence and credential changes. Their use alone does not establish an attack: for example, AssumeRole can be legitimate. The intervention generator can also produce inconsistent combinations, because fields are replaced independently and derived features are not recomputed after every perturbation. These design choices constrain the interpretation of both successes and failures.

## 4 Methodology

### 4.1 Detector and explanation contract

The baseline Isolation Forest uses 100 trees, contamination 0.05, max_samples set to auto and random seed 42. The contamination setting chooses the model's training-score cutoff; it is not an estimate that 5% of operational events are attacks. Scoring records the scikit-learn decision function and the prediction convention in which −1 denotes an anomaly.

TreeExplainer produces seven SHAP contributions per explained event [@treeshap]. For the Isolation Forest adapter, those contributions reconstruct an internal mean tree-path output, not the decision function and not an attack probability. We check the expected value plus the contribution sum against the adapter's own predicted output. A detailed validation record reports a maximum absolute residual of approximately 2.66 × 10⁻¹⁴. SHAP describes the fitted model's behaviour; it does not provide a causal account of maliciousness.

[[FIG:pipeline]]

### 4.2 Distribution drift

We measure categorical drift on five shared features: event name, service, region, identity type and error code. For a feature, reference and current counts are expanded over the union of observed categories, smoothed by adding 10⁻⁶ to each count, and normalised. With reference probabilities p and current probabilities q, the population stability index is:

[[EQ:psi]]

The method also records Jensen–Shannon divergence as a descriptive measure. The feature drift gate uses the mean categorical PSI plus a scaled scalar-shift term:

[[EQ:feature]]

Here m is five. The scalar term z is the mean of absolute deviations from reference means, divided by reference scales and clipped at ten. A near-zero reference standard deviation is replaced by the larger of the absolute reference mean and one. Monthly observation uses counts, rates, category diversity, entropies and concentration features. The controlled benchmark uses event count and a fixed high-risk-rate placeholder; those scalar values do not change, so its feature gate reduces to mean PSI. The external checkpoint uses event count, error rate and high-risk-event rate. These different scalar contracts are an additional obstacle to direct threshold transfer.

### 4.3 Attribution drift

For each model feature, we compare signed SHAP distributions in the reference and current samples using the one-dimensional Wasserstein distance. The distance is divided by the reference SHAP standard deviation plus 10⁻⁹:

[[EQ:wasserstein]]

The explanation gate combines the mean normalised distance, disagreement between the sets of three highest mean-absolute-attribution features, and an order term:

[[EQ:shap]]

J is the Jaccard overlap of the top-three feature sets. The implemented order statistic K is Kendall's tau applied directly to the two index arrays sorted by absolute signed mean attribution, with nonfinite results replaced by zero. This differs from computing rank correlation over feature-aligned rank vectors. We report the implemented statistic explicitly and treat it as a heuristic component whose replacement needs validation. We do not silently substitute a different ranking formula when describing the saved results.

Two additional summaries record absolute differences between signed attribution means and differences between mean absolute attributions. Neither summary retains the direction of change after the absolute difference. This distinction prevents interpreting a displacement magnitude as evidence that an event became more malicious.

### 4.4 Attribution feature coupling

For the five shared categorical features, let d contain per-feature PSI values. Let a contain the absolute changes in mean absolute SHAP attribution between current and reference samples. The coupling score is their cosine similarity:

[[EQ:coupling]]

For nonnegative, nonzero vectors this score lies between zero and one. The implementation returns zero if either vector has norm at most 10⁻¹². A large score indicates alignment, not large drift. The feature and attribution magnitude gates therefore remain separate from the coupling gate.

[[TABLE:diagnosis]]

We also record shifted Pearson alignment, shifted Spearman alignment and a conservative score that takes the minimum of cosine and shifted Pearson alignment. Shifted correlation is the correlation plus one, divided by two; constant vectors receive zero. These are established mathematical operators used as ablations. We make no claim that the minimum is a statistically optimal combination.

### 4.5 Threshold selection and update controller

The validation search considers empirical quantiles at 0.20, 0.35, 0.50, 0.65, 0.80 and 0.90. The dual rule selects feature and SHAP thresholds by validation macro-F1 over stable, benign-drift and security-relevant-drift classes. The selected values are 0.154455 and 0.965994. Coupling and conservative coupling use an alignment threshold of 0.864070. Their search scores use five output labels, including review and instability, so the raw validation macro-F1 values are not directly matched to the dual rule's three-class score.

The coupling search explores joint threshold triples, but the downstream implementation retains the feature and SHAP thresholds selected by the dual search and adds the alignment threshold. Consequently, its stored search score cannot be read as an evaluation of every subsequently applied threshold combination. The reported policy outcomes come from the saved applied decisions, not from an assumption that the search found a globally optimal controller.

We compare static, periodic, feature-only, SHAP-only, dual, coupled and conservative-coupled policies. Static never updates. Periodic requests a refit at every third scenario-run index, including the zero index; this is an experimental ordering, not a three-month schedule. Single-signal policies use their respective magnitude gates. Dual and coupling policies update only when their diagnosis is security-relevant drift.

Every policy–scenario run begins with the same baseline model. On an update request, the controller retains current rows predicted normal by that baseline, requires at least ten candidates, and fits a new 50-tree Isolation Forest on those candidates plus the 200-row replay reference. If too few candidates remain, the baseline is retained. Predictions of normality do not guarantee clean candidates. The difference between the 100-tree baseline and 50-tree refit is a model-capacity confound. Moreover, the current window used for candidate selection is also scored after refitting; the experiment does not provide an independent future recovery window.

### 4.6 Metrics and uncertainty

Row-level precision, recall and F1 use the controlled intervention mask. False-positive rate is false positives divided by all negative rows in the run. We average each metric over scenario–seed units, rather than pool every record across runs. Four of the seven families contain no positive targets. Their positive-class F1 is zero under zero_division = 0, including the case of an entirely correct all-negative prediction. Thus, mean event F1 must be read alongside security recall and false-positive rate.

The update rate is requests divided by all runs. The unnecessary-update rate is requests on stable or benign scenarios divided by all runs, not divided by the number of updates. These definitions keep a low update count from being mistaken for comprehensive security detection.

Paired inference compares dual minus static using common scenario–seed keys. Percentile bootstrap intervals use 2,000 resamples of paired differences [@efron]. Two-sided Wilcoxon signed-rank tests omit zero differences [@wilcoxon]. Benjamini–Hochberg adjustment is applied across the available nondegenerate tests in the exported inference table [@bh]. Because all runs reuse a reference matrix and scenario families, independence is limited. The intervals describe this experimental resampling scheme, not population uncertainty over independent cloud incidents.

## 5 Results

### 5.1 Diagnosis and policy comparison

The dual threshold search obtains validation diagnosis macro-F1 of 0.7306 across three classes. The coupling search records 0.4384 across five output labels, subject to the search/application distinction above. Neither number is attack-detection accuracy on the unlabelled monthly corpus. Applied held-out dual and coupled decisions are identical in this benchmark.

The held-out decisions identify all ten credential scenarios and seven of ten defence scenarios as security-relevant. None of the ten privilege scenarios receives that diagnosis. All region and identity changes receive benign-drift diagnoses; three service changes receive benign-drift diagnoses and seven remain stable. Every stable run remains stable. This pattern explains why the zero unnecessary-update rate coexists with missed security-related scenarios.

[[FIG:signals]]

[[TABLE:policies]]

The dual policy requests 17 updates in 70 units and none in the 40 non-security units. Feature-only requests 53 updates, including 23 non-security requests. Periodic requests 24 updates, of which 14 are non-security requests. Coupling and conservative coupling request exactly the same updates as dual and SHAP-only. The experiment therefore supplies no added decision benefit for alignment gating under these scenarios.

Relative to static, dual reduces the mean false-positive rate by 8.85 percentage points. However, its mean recall is lower, and its mean F1 is 0.2873 compared with 0.2901 for static. Feature-only has the lowest mean false-positive rate in this table but also a lower mean F1 and more unnecessary updates. None of these observations supports declaring a universally best policy from a single metric.

[[TABLE:paired]]

The paired false-positive difference has an interval entirely below zero. The F1 interval crosses zero, and its adjusted q-value is 0.943392. A nonsignificant difference does not establish equivalence or noninferiority, which would require a prespecified margin and suitable analysis. Since the adapted model scores the same window used to select its fit candidates, the false-positive reduction is contemporaneous experimental evidence, not a demonstrated future generalisation gain.

### 5.2 Detector and sample size sensitivity

The robustness experiment refits each detector directly on a reference prefix, rather than reusing the 251,613-row baseline from the policy comparison. It tests Isolation Forest with 50, 100 and 200 trees, Local Outlier Factor with 20 neighbours in novelty mode [@lof], and One-Class SVM with nu = 0.05 and gamma = scale [@ocsvm]. This protocol difference explains why robustness metrics should not be substituted for the policy table's averages.

[[TABLE:detectors]]

One-Class SVM has higher controlled security recall and F1 here, at the cost of more benign false positives. Local Outlier Factor has substantially lower security recall in the ordinal representation. In the separate sample-size test, security recall is 0.0884 for 100 rows, 0.4918 for 200 rows and 0.4152 for 500 rows. The nested deterministic prefixes change both sample size and sample composition. Their non-monotonic result does not establish 200 rows as a general optimum or show that adding representative data would harm a detector.

### 5.3 Independent detector evaluation

The independent track uses the public Cloud Log Sampling repository [@clouddata]. Its training archive contains 16,495 benign records; its labelled mixed test archive contains 24,087 records, including 2,585 attack-labelled and 21,502 benign records. We reconstruct the same seven-feature contract and fit category maps on the training archive only. This is an independent corpus, although its injected scenario labels do not amount to naturally occurring production incidents.

[[TABLE:external_detectors]]

Isolation Forest obtains event-level F1 of 0.4519. Local Outlier Factor has higher recall but also a higher false-positive rate. One-Class SVM has very low recall despite its low false-positive rate. The ranking differs from the controlled robustness test, illustrating why a detector should not be selected from the most favourable single protocol. This external experiment validates application of the feature contract and detector fitting; it does not by itself validate adaptation recovery.

### 5.4 Retrospective external diagnosis and calibration

An additional checkpoint groups 16,772 earlier benign test records into a reference group and 7,315 later records into ten security scenario groups and one benign target group. Group sizes vary from one to several thousand records; SHAP uses up to the first 500 time-ordered records in each group. These are retrospective scenario groups, not uniformly sized online windows. In particular, attack_name annotations define the target grouping before drift calculation. They are excluded from model features and threshold calculations, but the grouping itself is label-informed. This checkpoint cannot be described as a fully label-free prospective detection trial.

The exported evaluation includes the benign reference group as a negative observation, giving 12 units: ten security groups and two benign groups. Feature-only, SHAP-only and dual each flag all ten security groups and one benign target group. Source-threshold coupling identifies only one security group. The conservative variant has the same result.

[[TABLE:external_windows]]

A separate recalibration uses the conservative scores of target groups that pass the transferred feature and SHAP gates. It selects the midpoint of the largest adjacent score gap, yielding a threshold of 0.499080. It uses no attack labels in that calculation, but estimates and assesses the threshold on the same target batch. It separates the ten security groups from the two exported benign groups in this checkpoint. This is transductive, small-batch separation, not held-out future accuracy.

Including the reference group also affects the false-positive denominator: the dual result is one false positive among two benign groups. Considering only the single benign target group would yield one false positive out of one. We retain the exported metrics for traceability and disclose the denominator rather than suggesting that a rate based on two benign groups is stable operational evidence.

### 5.5 Cost sensitivity

The saved sensitivity analysis assigns costs to missed security targets, benign false positives and unnecessary updates, averages the resulting losses across runs, and varies all three weights. Miss cost takes values 1, 2, 5 and 10; false-alarm cost takes 0.5, 1, 2 and 5; unnecessary-update cost takes 0, 0.25, 0.5, 1, 2 and 5. These 96 combinations are hypothetical priorities, not measured monetary costs or retraining runtimes.

[[EQ:cost]]

In this expression r is run-level recall, u indicates an unnecessary request, and the indicators select security or non-security families. The loss penalises missed positives within security runs and false positives within non-security runs; it does not include every possible operational consequence. The saved winners are predominantly static, with periodic and a small number of feature-only selections. The table identifies one minimum per cost setting and does not enumerate all tied minima. Coupling does not emerge as a general cost winner, reinforcing the importance of the recall–false-alarm trade-off.

## 6 Discussion and Threats to Validity

The central hypothesis is not supported by the current policy benchmark: adding alignment does not change the held-out decisions made by simpler gates. This neutral finding is informative because high coupling is plausible even for a routine region shift, while a security-oriented privilege intervention can remain below the SHAP magnitude threshold. Alignment alone cannot repair a magnitude gate that does not fire. It also cannot resolve uncertainty about whether an API operation is legitimate.

The source threshold's external failure shows that alignment scores are not automatically portable. Their scale depends on category maps, feature distributions, attribution behaviour, group construction and sample sizes. The feature drift gate also changes its scalar contract across the monthly, controlled and external tracks. A transferred numerical threshold therefore combines several shifts in measurement conditions. Recalibrating on the target batch addresses score separation in that batch but does not distinguish a stable operating regime from a favourable small-sample partition.

The primary dataset's lack of attack labels remains the largest evidential limit. Its 45 months provide longitudinal observations of a fixed detector, not verified temporal changes in attack risk. Monthly aggregation cannot establish fine-grained sessions or causal API sequences. Deterministic prefix sampling can overrepresent early source records, and the extreme August 2019 volume concentration limits naive pooling. The controlled reference is only a 200-row prefix, not a representative random draw independently repeated for every seed.

The intervention design introduces a separate construct-validity limit. Security-related replacements encode plausible operation names, but do not simulate complete attacks with consistent identities, regions and dependencies. Replacing identity type without recomputing isRoot can create internally inconsistent rows. Unknown-category collapse can merge semantically distinct operations. A model response to these vectors may therefore reflect encoding artefacts or inconsistent combinations rather than a security mechanism.

Adaptation evidence has two additional limits. First, current records selected for fitting are also present when the updated detector is evaluated. Second, baseline and adapted forests differ in ensemble size and fit data composition. A lower current-window false-positive rate can result from fitting the observed distribution without guaranteeing better future recall or resistance to contaminated candidates. The experiments reset between units rather than maintain an evolving detector, so they do not measure cumulative forgetting or recovery across an attack stream.

Statistical uncertainty also needs a narrow interpretation. Repeated seeds share the same reference observations, scenario definitions and detector. Stable scenarios repeat unchanged data. The percentile bootstrap and signed-rank tests do not remove those dependencies, and their p-values should not be generalised to populations of independent incidents. The external checkpoint contains only one target attack period, unequal scenario groups and effectively one benign target group. Its perfect recalibrated separation should motivate another experiment, not a claim of robust deployment.

A stronger follow-up would use time-only windows defined without attack annotations, calibrate on an earlier unlabelled target period, and freeze the complete measurement contract before assessing later windows. Matched baseline and refit capacities, future-only scoring, consistency-preserving perturbations and independent account-level repetitions would address the most direct confounds. Feature-aligned rank comparisons should replace the current index-array order statistic only in a separately regenerated experiment. Analyst confirmation would be required before presenting model-derived drift categories as operational security judgements.

## 7 Reproducibility and Availability

The implementation uses Python, scikit-learn [@sklearn], SHAP, NumPy, pandas and SciPy. The research dependency versions are pinned in requirements.txt. The public project repository is https://github.com/sani3055/DriftDetection. Primary data provenance is recorded in data_manifest/real_cloudtrail_manifest.json; the source checksum is b3aa4fcf28747f4f84457d2d3b76f4c27901bd2e6289bf6d6288cb9587d20589. This identifies the evaluated file but does not establish an unrestricted redistribution licence.

The main pipeline is organised into audit, temporal feature construction, detector fitting, SHAP generation, drift calculation, controlled diagnosis and adaptation evaluation. Separate scripts generate detector/sample-size robustness, independent detector evaluation, external retrospective diagnosis and cost sensitivity. A local Streamlit interface replays saved held-out signals through the actual diagnosis rule. It is a review aid rather than a live AWS integration or a new performance experiment.

The policy results can be traced to data/benchmark/adaptation_results.csv and its summary. Paired intervals and adjusted tests are in results/paired_inference.csv. External source manifests record archive checksums separately from event-level and scenario-level results. At manuscript preparation, the current software suite passes 44 tests, including checks that all 70 replayed decisions match saved evidence. Passing implementation tests does not establish detector effectiveness. No runtime, peak-memory or live deployment benchmark is reported, and no immutable manuscript-specific repository release is claimed.

## 8 Conclusion

This study evaluates a CloudTrail anomaly-monitoring pipeline that combines feature drift, SHAP drift and attribution feature coupling. The formulation makes explicit whether changing input features also change their attribution profile, while preserving separate magnitude gates. Dual signals reduce false positives relative to a static detector in the defined controlled experiment, but an F1 improvement is not established. Coupling does not add a measured policy benefit in that benchmark and its source threshold transfers poorly to the retrospective external checkpoint.

The useful outcome is an inspectable method and evaluation protocol with clear failure cases. Target-batch recalibration offers an exploratory response to score-scale shift, but prospective temporal validation, consistent scenario construction and future-only adaptation evaluation remain necessary. The present evidence supports further investigation of attribution-aware update decisions, rather than a claim of generally improved attack detection or production readiness.

## Acknowledgements

The author acknowledges Dr Badrinath N for capstone supervision at Vellore Institute of Technology.

## Data Use and Research Transparency

The study analyses existing log exports and does not collect new live user activity or enforce AWS IAM actions. Raw identifiers are excluded from the model's feature contract, while source files remain read-only. Public redistribution rights for the inherited primary corpus have not been established. The independent corpus is referenced through its public repository. Generative AI tools assisted software development, data-to-table conversion and manuscript drafting. Reported measurements derive from saved experiment artifacts; generated prose is not empirical evidence.

## References

[[REFERENCES]]
