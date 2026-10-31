# Explainable Drift Diagnosis and Adaptive Anomaly Detection in Cloud and Security Logs

Sanidhya Bhandari and Badrinath N

School of Computer Science and Engineering, Vellore Institute of Technology, Vellore, India

Corresponding author Badrinath N

## Abstract

Security detectors must operate while normal workloads, software and attack behaviour change. Distribution monitoring can identify changed inputs, but it cannot by itself establish whether a change is malicious or whether a model update will help. Explanations provide additional information about model behaviour, although unstable or misleading explanations introduce their own risks. This structured review charts 101 primary journal articles on explainable detection, drift monitoring and adaptation, published within 2022 to the search cutoff of 31 October 2026. Bounded searches of OpenAlex and Europe PMC, supplemented by targeted discovery, support a traceable evidence collection. Journal identities and bibliographic dates were checked against Crossref, and the associated full texts were retained. The review distinguishes six methodological groups and examines their relevance to cloud audit and system logs. Its central finding is a separation of evidence: predictive performance, explanation faithfulness, change detection and adaptation benefit answer different questions and require different tests. Close precedents already connect explanations with monitoring and retraining, so combining SHAP and adaptation is not sufficient to establish novelty. A diagnostic taxonomy and an evaluation checklist are developed to support more precise comparisons, including evaluation of harmful updates and benign workload changes. The synthesis is qualitative; heterogeneous benchmark scores are not pooled. Bounded retrieval, an open-access emphasis, single-stream AI-assisted charting and the absence of independent human appraisal limit its completeness. The paper is a guide-review draft rather than a claim of a completed exhaustive systematic review.

Keywords: concept drift; explainable artificial intelligence; intrusion detection; cloud audit logs; SHAP; adaptive anomaly detection

## 1 Introduction

Cloud security monitoring must distinguish unusual activity from harmful activity. A new service, a changed deployment pattern or an expansion into another region can alter an audit stream without indicating an attack. Conversely, an attacker may exploit familiar APIs and produce records that resemble ordinary operations. An anomaly detector therefore needs more than a rule that treats every distribution change as an incident.

Model explanations offer another view of this problem. An explanation can show which inputs influence a prediction, helping an analyst investigate whether a changed workload affects the model's decision process. However, a feature-importance plot is not evidence that the model remains accurate. Explanation changes may reflect a new population of events, a different model, an altered encoding or a change in the explainer's background sample. Those possibilities must be separated before an attribution signal can support a maintenance decision.

The selected literature already contains explanation-based novelty detection, unsupervised monitoring of explanation descriptors and feedback-driven retraining [@S0112;@S0196;@S0204]. More recent work studies adversarial explanation changes, correlations in feature importance, and validation-calibrated adaptation [@CORE05;@S0005;@S0034]. A defensible research contribution must therefore identify the additional evidence or decision that it supplies, rather than claim novelty from combining established components.

This review asks four questions. What do recent journal methods actually monitor? What data, labels and timing assumptions support their evaluations? How are explanations used to inform detection or adaptation? Which conclusions are directly supported for cloud logs, and which remain transfers from another security domain? The contribution is an evidence-oriented taxonomy and a checklist for testing proposed monitoring policies. It is not a new detector or a claim of a first comprehensive survey.

## 2 Review method and evidence boundaries

### 2.1 Scope and eligibility

The evidence collection focuses on primary journal studies that materially address explainable intrusion detection, explanation quality, distribution-aware monitoring, security adaptation or anomaly detection in system logs. The publication interval is 1 January 2022 through 31 October 2026. Conference papers, standalone preprints, duplicate versions, physical perimeter-coverage problems and unrelated application areas are not counted as primary journal evidence. Secondary surveys are retained as contextual leads, not counted as additional independent experiments.

Network-flow, medical-IoT, industrial and vehicular studies are included as supporting methodological evidence. Their inclusion does not imply that their features, threat labels or performance transfer to AWS CloudTrail. A narrow distinction is also made between actual system-log analysis and a general architecture described as cloud-enabled. The latter description alone does not establish an audit-log experiment.

### 2.2 Information sources and retrieval

The earlier OpenAlex search archived four bounded queries, each limited to 100 records: explainable intrusion detection; concept drift intrusion detection; cloud audit log anomaly detection; and SHAP concept drift cybersecurity. The archive contains 400 returned records and 392 distinct DOIs. These searches were run with a cutoff of 30 October 2026 and are not represented as exhaustive.

A supplementary Europe PMC search on 31 October used three broader queries and eight year-restricted queries for 2022 to 2025. The first three were limited to 100 records each and the remaining queries to 25 each. The archive contains 500 returned records and 410 distinct DOIs within that source. The year-restricted queries improved coverage of earlier years, but neither the source nor these caps provide comprehensive coverage of computer-security research. Exact queries, limits, returned records and retrieval results are preserved in the project records.

Full-text retrieval used lawful publisher, repository and public archive routes. Europe PMC article XML and the current NCBI public cloud archive supplied supplementary text and PDF versions. No institutional authentication was bypassed. SciSpace was used for supplementary discovery; its connected plan did not permit PDF downloads. NotebookLM was used for a cited extraction of an initial three-paper batch. That limited use is recorded rather than extended into a claim that every summary was independently produced or verified by those services.

### 2.3 Selection and charting

The focused charting pool contains 128 distinct article records with retained full text. From this pool, 101 primary journal articles were selected; 27 records were secondary context or outside the narrower analysis question. This focused pool is not identical to all records identified in the discovery searches. The remaining discovery records have not all received independent final screening. Consequently, these numbers describe the selected evidence collection, not a completed PRISMA flow from an exhaustive search.

For each selected record, the package links the DOI, journal identity, authors, bibliographic date, PDF, hash, summary, methodological theme and reviewer interpretation. Charting uses abstracts and targeted full-text evidence. The summaries avoid importing numerical results without their evaluation context. Reviewer cautions are kept distinct from author-reported findings and should not be read as findings that a particular article definitely contains leakage or an invalid experiment.

Crossref's bibliographic year may describe the issue year when an earlier online date appears elsewhere. Date differences are retained for resolution rather than silently converting a DOI suffix or repository deposit date into a publication date. All selected records remain within the eligible year interval under the checked metadata.

### 2.4 Synthesis and reporting

Articles were assigned one dominant methodological theme for descriptive organisation. These themes are reviewer-defined and mutually exclusive for counting purposes; a method may contain components relevant to several themes. Classification accuracy, attack F1, drift-diagnosis F1, change-point delay, calibration and update frequency were not combined as a common outcome. No meta-analysis or pooled estimate of superiority was calculated.

PRISMA 2020 provides a reporting structure for search and selection transparency [102]. The project includes a completion map identifying which items are documented and which remain incomplete. PRISMA is a reporting guideline, not a guarantee of rigorous methods or journal acceptance. This draft does not claim prospective registration, independent dual screening, completed study-level risk-of-bias assessment or publication readiness. These boundaries are part of the method, not interchangeable with a generic disclaimer at the end.

## 3 A taxonomy of monitoring evidence

### 3.1 Changes in observed inputs

A feature-distribution monitor asks whether the current observations differ from a reference. Marginal tests are useful because they can often operate before labels arrive. They do not show that a model's decision boundary has become wrong. A benign workload change can produce a substantial shift, while a harmful change may be hidden in a small subpopulation or in relationships between features.

Window-based and statistical drift methods illustrate the variety of relevant signals. EMNCD combines non-parametric tests, while incremental and hybrid frameworks combine change monitoring with online classifiers [@S0277;@E283;@S0048]. These methods differ in their reference windows, response rules and access to labels. They should not be treated as equivalent implementations of a single drift threshold.

### 3.2 Changes in the model's reasoning

An attribution monitor examines the inputs to which a model assigns influence. Lee and colleagues use SHAP-based descriptions in a DGA-monitoring setting, while another study learns an autoencoder over SHAP explanations to identify unfamiliar attacks [@S0196;@S0112]. Their evidence establishes precedents for treating explanations as monitoring representations.

Explanation-based monitoring nevertheless depends on a stable measurement procedure. The model version, feature encoding, predicted output, explainer configuration and background sample should be recorded. Otherwise, a measured displacement can combine changes in the data with changes in how explanations are computed. Comparing absolute attribution magnitudes also answers a different question from comparing signs, ranks or interactions.

### 3.3 Explanation quality and reliability

Explanation fidelity, stability and usefulness are separate properties. E-XAI evaluates several such dimensions across detectors and datasets, while adversarial studies show that SHAP and LIME can behave differently under perturbation [@S0094;@E344]. A ranking that changes little is not necessarily faithful, and a faithful local explanation may still be too expensive for every event in a high-volume stream.

Attribution similarity is also not a deterministic risk measurement. The transferability study explicitly treats importance-vector similarity as an approximation that should be checked against direct attack testing [@S0005]. Adversarial explanation monitoring similarly supplies an auxiliary signal rather than perfectly separating clean and manipulated observations [@CORE05]. These findings caution against translating an aligned pair of feature and attribution changes directly into an attack label.

### 3.4 Changes that justify an update

Adaptation is an intervention with potential benefits and harms. It can restore detection after normal behaviour changes, but it can also absorb malicious activity, forget rare attacks or alter the false-alarm burden. An alarm and a decision to retrain should therefore be evaluated separately.

The reviewed literature includes active incremental learning, changing feature subsets, replay, memory-based learners and federated participation control [@S0206;@S0091;@S0092;@E316;@E079;@S0006]. These methods use different feedback and labels. ASRAE, for example, combines an initially unsupervised component with later labelled few-shot adaptation; the entire pipeline should not be called label-free [@S0007].

## 4 Findings across the selected studies

### 4.1 Explainable intrusion classifiers

The largest group in the selected collection adds explanation to a predictive detector. Examples include tabular tree models, recurrent ensembles, CNNs and attention-based models [@S0120;@S0090;@S0115;@S0137;@E055;@S0140;@E066;@E406]. Their practical contribution is often an interpretable view of individual classifications or influential inputs.

These results should be read at the task level. Binary attack detection, multi-class attack identification, encrypted-DNS classification and CAN anomaly detection have different labels and observation units. XI2S-IDS explicitly uses staged prediction for less frequent attacks, while X-CANIDS uses domain-readable vehicle signals [@S0245;@S0129]. Neither task is equivalent to identifying a harmful change in a cloud audit stream.

Optimisation-heavy pipelines further complicate attribution of improvements. Studies combine resampling, feature selection, metaheuristic search and deep learning before applying an explainer [@E053;@E059;@S0199;@E148;@E356]. Matched tuning budgets and component ablations are needed before crediting the explanation layer with better detection. High benchmark accuracy alone provides no such attribution.

### 4.2 Drift and adaptation

The adaptation literature covers several mechanisms rather than a single model-maintenance pattern. Some methods alter feature selection, some retain recent exemplars, some query labels, and others update ensemble contributions or representation parameters [@S0091;@S0092;@S0206;@E316;@S0139;@S0034]. Their assumptions determine whether a comparison with an unsupervised CloudTrail detector is fair.

Not every use of the word adaptive indicates temporal drift diagnosis. Adjusting training epochs, selecting an expert for a sample, or optimising attention weights can improve model fitting without measuring a post-deployment shift [@E294;@E357;@E336]. The review therefore separates adaptation inside a learning architecture from maintenance after changed deployment conditions.

Two close precedents are particularly important. AutoSHARC already links explanation-driven analysis with post-hoc retraining, and ADAWU-IDS calibrates its response on validation data before chronological evaluation [@S0204;@S0034]. The project should not claim that explanation-guided retraining or validation-selected adaptation is itself new. A stronger contribution would demonstrate when feature-attribution alignment changes a decision and whether that difference produces a measurable benefit under matched conditions.

### 4.3 Temporal evidence and unsafe reassurance

Future-domain tests are more informative for drift than a randomly mixed split when the deployment question concerns change over time. DriftDroid separates historical validation from later-domain testing and reports both performance degradation and adaptation sensitivity [@S0082]. Its findings illustrate why a high source-domain score cannot serve as a deployment guarantee.

The audit of label-free monitoring similarly questions whether confidence, agreement or abstention remain reliable under security-relevant temporal shift [@E232]. Agreement among models may reflect shared failure rather than independent reassurance. This matters when a system has no timely target labels: a monitoring dashboard can remain apparently healthy while the actual task has changed.

Simulated shifts, withheld classes and adversarial perturbations remain useful because they permit controlled comparisons. They should be named accurately, however. A synthetic geographic propagation experiment, a held-out attack-family test and a feature-space adversarial attack each establish a different type of evidence [@E223;@E366;@E116]. None alone establishes sustained independent real-world validation.

### 4.4 Cloud audit and system logs

The CloudTrail RAG study provides a direct audit-log example, but its target is contextual interpretation of individual events [@CORE07]. That is distinct from deciding whether a time window requires retraining. Its controlled provenance, annotation process and lack of an evaluated temporal sequence must remain visible when it is used as related work.

System-log studies offer complementary methods. Temporal decay changes the influence of older training information; NLP-LightGBM examines representations; parser-free BERT provides word-level explanations; graph methods represent event relationships; and distributed methods address heterogeneous logs [@E317;@E128;@E134;@E008;@S0017;@S0202]. These are relevant comparisons, but fault labels and system anomalies should not be silently converted into attack labels.

For CloudTrail, feature semantics matter. Region, service, identity type, API action and error outcome have operational meanings. Encoding decisions and unknown-category handling can create apparent shifts. A detector should record those processing changes separately from a claimed change in user behaviour or attack prevalence. This follows from the taxonomy and is a design recommendation, not a benchmark result established by this review.

### 4.5 Distributed learning and operational response

Federated studies address heterogeneity, restricted data sharing and constrained participants [@S0031;@E070;@E071;@E079;@E110;@E137;@E346]. Some add threshold cryptography or aggregated explanations [@E373;@E152]. Keeping raw records local is useful, but privacy and robustness depend on the actual mechanism and threat model; they are not automatic consequences of using federated learning.

Operational responses introduce further distinctions. Tamper-evident alert storage does not prove that an alert is correct, and a controller that changes firewall or honeypot behaviour changes the system being measured [@E231;@E131;@E156]. Evaluation should distinguish prediction, explanation, integrity and intervention effects. Those endpoints answer different security questions and should not be compressed into one trustworthiness claim.

## 5 An evaluation framework for risk-sensitive drift diagnosis

The proposed framework is a synthesis of the selected evidence, not a newly validated detector. It separates observation, diagnosis and action. First, measure changes in inputs and model explanations under a controlled representation. Second, test whether the observed changes relate to a decision failure or security-relevant subgroup. Third, compare candidate responses under a fixed validation policy. Finally, assess the chosen response on later observations that were not used to tune its thresholds.

At the feature level, an alignment measure could ask whether the inputs that moved are also the inputs whose attributed influence changed. This is a testable diagnostic hypothesis. High alignment does not identify malicious intent, and low alignment does not prove safety. A monitor might instead be sensitive to a changed explainer background, an unseen category or a poorly calibrated detector.

A useful benchmark should include stable windows, benign operational changes and security-relevant changes. It should compare a static detector, a fixed update schedule, input-only monitoring, explanation-only monitoring and joint policies using the same observations and update budgets. If two policies make identical decisions, equal average outcomes do not show an added benefit from the more complex policy.

Update safety should also be measured directly. Candidate training records may include undetected attacks even when they were predicted as normal. Replay, minimum sample counts, contamination limits, held-out evaluation and rollback conditions can constrain that risk, but none should be described as a proof of safety. The contribution is the observed outcome under specified conditions, including cases where adaptation performs worse.

Explanation computation belongs in the cost model. A complete report should state the number of explained events, background size, explainer method, hardware, inference latency and retraining frequency. Subsampling can reduce cost, but should be tested for sensitivity rather than assumed to preserve every rare security signal.

## 6 Reporting checklist for future studies

The evidence suggests eight questions for a study claiming explanation-guided drift adaptation. Is the observation unit an event, flow, session or window? Are the labels real, expert annotated, simulated or inferred? Are train, validation and test periods ordered without information flowing backwards? Does the policy use delayed labels, rewards or target-batch calibration? Are explanation settings fixed across the comparison? Do baselines receive matched data and tuning effort? Are false alarms, missed attacks and unnecessary updates evaluated separately? Are update contamination, computation and negative outcomes reported?

These questions should be answered with implementation artifacts, not just prose. Dataset manifests, stable identifiers, recorded thresholds, model versions, seeds and machine-readable outputs make the claims easier to audit. Counterfactual or LLM-generated explanations should retain the underlying evidence and be assessed for feasibility and grounding [@E033;@S0203;@E318].

The review does not assign a universal quality score to the selected studies. A score without completed, domain-appropriate appraisal would hide uncertainty rather than resolve it. The accompanying summaries instead distinguish the reported method from reviewer cautions and provide the original source for further checking.

## 7 Limitations

The search is bounded and partly shaped by full-text availability. OpenAlex and Europe PMC have different coverage, and the latter is not a comprehensive computer-security index. Search-result caps, default result ordering and targeted acquisition affect the sample. The strong representation of recent papers describes this collection and must not be presented as a population-level publication trend.

The focused pool does not complete independent screening of every discovered record. Charting was performed through one AI-assisted stream, using abstracts and selected full-text passages. The work has no independent second reviewer, no inter-reviewer agreement estimate and no completed study-level risk-of-bias assessment. Those activities cannot be invented to satisfy a checklist or inferred from a downloaded PDF.

Heterogeneous datasets, labels, partitions, models and evaluation targets prevent a justified pooled ranking. Reported superiority claims remain tied to their original experiments, and this review does not independently reproduce them. Apparent reporting inconsistencies are questions for source reconciliation, not proof of misconduct or invalidity.

Before journal submission, the authors should validate the selection decisions and summaries, complete the applicable PRISMA reporting items, assess study quality and choose whether a broader systematic search or an explicitly limited structured-review design is appropriate. Authorship, corresponding-author contact details, funding and conflict declarations also require author confirmation. No journal submission or acceptance is claimed.

## 8 Conclusion

The selected journal evidence supports a clear separation between explaining a prediction, detecting a changed operating environment and demonstrating that adaptation helps. Explanation-based monitoring and explanation-guided retraining already have close precedents. Future work should therefore test the additional value of a proposed diagnostic signal under matched chronological conditions, including benign shifts, hidden failures and unsafe updates.

For the CloudTrail project, a defensible research direction is to measure whether alignment between feature drift and attribution movement changes an update decision, and whether that change improves the outcome on unseen data. Negative and equivalent-policy results remain valid findings. The review's evidence collection and reporting checklist provide a basis for that evaluation, while its remaining screening and appraisal limits must be resolved or explicitly retained in the chosen journal-review design.

## References

The Word version expands the 101 verified study references and the PRISMA 2020 reference here. Study numbers correspond to the consolidated summaries and PDF register.
