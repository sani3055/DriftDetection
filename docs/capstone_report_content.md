# Abstract

Cloud audit logs record how users, services and automated workloads interact with an AWS environment. Their behaviour changes as applications grow, services move between regions and access patterns evolve. An anomaly detector trained on historical activity may therefore raise alerts for legitimate changes. Updating the detector after every distribution change can also be problematic, because a new training sample may contain unusual or harmful activity. This capstone project investigates whether changes in feature distributions and changes in model explanations can be combined to make adaptation decisions more selective.

The implemented framework uses Isolation Forest to score CloudTrail events and TreeSHAP to explain the detector's output. It monitors categorical feature distributions, attribution distributions and the alignment between them. The proposed attribution–feature coupling measure compares a vector of feature-level population stability indices with a vector of absolute SHAP displacement. A conservative alignment variant and an unsupervised transfer-calibration experiment are evaluated separately. The contribution is a CloudTrail-specific design and evaluation protocol that connects these signals to protected retraining and measures unnecessary adaptation.

The primary corpus contains 1,939,207 records, 18 columns and 45 monthly windows. It has no attack labels, so its real-data analysis describes observed changes without assigning attack-detection accuracy. A chronological partition reserves 27 months for training, nine for validation and nine for testing. Controlled benign and security-related perturbations provide a separate evaluation track, with validation seeds used for threshold selection and held-out seeds used for policy comparison. An independent labelled cloud-log corpus supports detector evaluation and a small temporal diagnosis checkpoint.

The dual-signal configuration achieved validation diagnosis macro-F1 of 0.7306. In the controlled adaptation comparison, its mean false-positive rate was 0.3397 against 0.4282 for the static baseline, while the paired F1 difference was not statistically distinguishable from zero. Coupling matched the dual policy in that benchmark. Source-calibrated coupling transferred poorly, but a threshold selected from unlabelled target scores achieved F1 of 1.0 on the external 12-window checkpoint. This small result motivates further validation rather than a claim of general superiority. The completed prototype provides reproducible code, saved evidence, automated checks and an auditable demonstration of drift diagnosis and protected adaptation.

# 1 INTRODUCTION

## 1.1 Background

AWS CloudTrail records operations performed through AWS services, including the API name, service, region and identity associated with an event. These fields allow an analyst to examine how a cloud account is used and which behaviours deserve closer inspection. A routine deployment can generate many similar events, while an occasional administrative action may look unusual even when it is authorised. The practical problem is therefore to interpret unusual behaviour in its operational context rather than equating rarity with an attack. The CloudTrail event schema provides the starting point for this analysis [10].

Machine learning offers a way to identify patterns that are difficult to describe through individual rules. In a cloud audit corpus without verified attack labels, an unsupervised detector is a reasonable baseline. Isolation Forest identifies observations that are easier to isolate through random tree partitions [1]. Its scores can highlight unusual combinations of API activity and identity attributes, but the detector learns from the reference sample supplied to it. If that reference becomes outdated, the meaning of an unusual score can also change.

This problem is closely related to distribution drift. For example, a team may begin using a new AWS region or replace an IAM user with a service identity. Both changes affect the observed feature distribution. Neither change, by itself, establishes that the account is compromised or that the model needs immediate retraining. A monitoring framework should provide enough evidence to distinguish a broad input change from a change that affects the model's decision behaviour. The distinction becomes especially important when the detector operates without a continuous stream of confirmed incident labels [3], [4].

The project studies that distinction through model explanations. SHAP assigns additive feature contributions to a model output [2]. By comparing attribution distributions between a reference window and a current window, the system can examine whether the detector is relying on its inputs differently. Attribution drift remains evidence about the model, rather than proof of malicious intent. Nevertheless, it can help an analyst ask a more useful question: are the features that changed in the data also the features associated with the detector's changed explanation profile?

## 1.2 Motivation

The starting point for this capstone was an existing CloudTrail-style dataset used in an earlier cloud-security project. Reusing that corpus retains continuity with the earlier work, but a research question must match the evidence the data can support. The current export contains month-level timestamps and no attack ground truth. It can support a careful longitudinal description of distributional changes; it cannot support an honest claim of event-level incident recall or reconstruction of complete attack sequences.

The revised direction turns these constraints into explicit engineering requirements. Instead of assigning assumed labels to real records, the project keeps the original data observational and evaluates diagnostic decisions through controlled perturbations. Instead of adding automatic enforcement claims, it implements a reproducible adaptation controller whose inputs, candidate training rows and decisions can be inspected. This makes the project easier to reproduce, demonstrate and critically evaluate.

There is also a practical reason to examine adaptation carefully. A model that never changes may become noisy as legitimate workloads evolve. A model that retrains too readily may absorb undesirable behaviour or change versions without a useful improvement. The project therefore treats adaptation frequency and unnecessary updates as outcomes in their own right. Detection F1 alone does not describe that trade-off, particularly when the chosen update policy changes false-positive burden and recall in different directions.

## 1.3 Scope of the Project

The capstone delivers a local research prototype covering data audit, temporal feature construction, unsupervised detection, SHAP validation, drift measurement, diagnostic rules, controlled adaptation experiments, robustness analysis and independent validation. The primary data remains read-only. Outputs are saved as CSV, JSON, model files, figures and documentation so that each reported number can be traced to an artifact. The project can be demonstrated from these outputs and through the implemented commands without depending on an active AWS account.

The primary detector uses six categorical event fields and one derived root-identity indicator. Monthly distribution analysis uses the shared event, service, region, identity-type and error-code fields. This compact representation keeps the relationship between inputs and explanations understandable. It also imposes limits: the prototype does not analyse request payload semantics, causal user sessions, full policy documents or graph relationships between identities and resources.

The implementation does not deploy AWS infrastructure or modify IAM permissions. A diagnostic state called security_relevant_drift means that the configured model-related evidence exceeded its thresholds. On the original unlabelled corpus, it is a review signal rather than a confirmed incident. On controlled scenarios, its correctness is measured against the scenario definition. The report uses these meanings consistently to avoid overstating what the prototype establishes.

## 1.4 Capstone Contribution and Engineering Outcome

The engineering outcome is an integrated pipeline with explicit interfaces and reproducible experiments. Each stage has a defined input and output, including a provenance manifest, a chronological split, a stable feature contract, a fitted detector, attribution samples, drift summaries and policy-comparison results. This supports both a live demonstration and an examination of the design decisions behind the results. The capstone includes implementation and verification rather than ending with a conceptual architecture.

The research contribution centres on attribution–feature coupling and its role in adaptation decisions. The system tests whether the changed categorical features align with changes in the detector's attributions, compares the resulting rule with simpler alternatives and records negative or neutral results. A separate experiment examines whether an unlabelled target-score distribution can recalibrate the coupling threshold when source thresholds transfer poorly. Established components such as Isolation Forest, SHAP and cosine similarity are acknowledged as prior methods.

# 2 PROJECT DESCRIPTION AND GOALS

## 2.1 Literature Review

The literature was organised around unsupervised anomaly detection, explanation-based monitoring, drift without labels, selective adaptation and cloud audit analysis. These areas establish most of the individual building blocks, but they place different demands on evaluation. A detector study needs reliable anomaly labels or a clearly stated surrogate. A drift study needs a meaningful reference and temporal protocol. An adaptation study must also show what happens after an update and compare that outcome with reasonable alternatives. The present design brings these requirements together for the available CloudTrail corpus.

### 2.1.1 Unsupervised Anomaly Detection

Isolation Forest provides the baseline because it does not require positive attack examples and operates on a compact tabular representation [1]. Its tree structure also supports efficient attribution analysis. This choice is practical, but it does not make every low-density observation malicious. The model's behaviour depends on feature representation, training composition and the contamination setting. For that reason, the report includes detector-family and sample-size ablations instead of treating the baseline as universally optimal.

Work on normality shift addresses a closely related issue: an unsupervised security detector may learn a useful reference and later encounter legitimate behaviour outside that reference. OWAD explicitly connects normality-shift detection, explanation and adaptation [6]. This prior work supports the importance of the problem and prevents an overly broad novelty claim. The present study differs in its CloudTrail representation, feature–attribution alignment measure, controlled protocol and policy accounting, rather than in inventing the general idea of adapting anomaly detectors.

### 2.1.2 Explainability and Attribution Monitoring

SHAP offers an additive framework for interpreting predictions [2]. In this project, its role is to describe the fitted detector's internal output. TreeSHAP explanations are checked numerically before their distributions are used for monitoring. This validation is essential because an explanation pipeline can appear plausible while explaining an output with a different scale or polarity from the score shown to an analyst.

Lee and colleagues studied explanation-based model drift detection applicable to unsupervised environments [8]. AWS documentation also describes monitoring feature-attribution drift against a reference [9]. These sources show that SHAP drift is an established direction. The narrower question here is whether feature-level alignment between input drift and attribution displacement adds useful information when selecting CloudTrail model updates. The project therefore compares coupling with both single-signal and dual-signal alternatives.

### 2.1.3 Drift Detection and Selective Adaptation

Research on unlabelled drift warns that a change in the input distribution need not correspond to a harmful change in the model's useful behaviour [3]. Earlier security work also examined legitimate behavioural changes and their effect on false alerts [4]. These findings motivate a diagnostic stage that interprets an alarm before choosing a retraining action. They do not justify assuming that a particular combination of drift scores will always distinguish benign activity from an attack.

Security-domain adaptation introduces further concerns because current observations may include adversarial or contaminated behaviour [5]. Drift-type-aware adaptation also studies how the character of change can inform the update strategy [7]. The capstone responds through a conservative retraining design: it retains replay data, admits only rows predicted normal by the baseline and records when the candidate set is too small. This is a transparent safeguard, although a baseline prediction cannot guarantee that a row is benign.

### 2.1.4 CloudTrail Studies and Literature Synthesis

Existing CloudTrail work combines anomaly detection with explanations and contextual reporting [11]. Such work is relevant to the input schema and analyst-facing use case, but it does not by itself establish the value of coupling feature drift to attribution drift before adaptation. The report therefore uses CloudTrail studies to define the application setting and uses drift research to frame the experimental comparison.

The repository also contains an automated 100-record literature collection for the broader review requirement. It is an initial evidence set, not a completed systematic review. The recorded status is 100 DOI records and 12 downloaded open-access PDFs, with title/abstract screening, full-text decisions and study-level risk of bias still requiring completion. This report draws on the verified core matrix and does not describe all 100 records as included journal studies. PRISMA provides the reporting framework for the separate review-paper effort [13].

@table literature

## 2.2 Research Gap

The defensible gap is a CloudTrail-specific evaluation of whether model-attribution change and input-distribution change provide complementary evidence for selective adaptation. A high feature-drift score tells us that the observed data moved away from its reference. A high attribution-drift score tells us that the detector's explanation distribution changed. The proposed coupling score asks whether those changes concentrate on the same features. This feature-level relationship is more specific than requiring two aggregate alarms to exceed thresholds independently.

The project also addresses a reporting gap. Unlabelled real data is often difficult to evaluate, and a demonstration can become misleading if assumed attack labels are introduced after the fact. Here, real monthly observation, controlled perturbation evaluation and independent labelled validation are documented as separate sources of evidence. Their results answer different questions and are not combined into a single accuracy claim.

This contribution is conditional on empirical results. The current controlled comparison found no incremental policy benefit from coupling over the dual rule. The independent source-threshold experiment also exposed poor transfer. Those outcomes constrain the claim and guide the next experiment. A useful capstone contribution can be an implemented and reproducible test of a plausible method, including a clear explanation of where that method fails.

## 2.3 Objectives

The first objective is to audit the reused corpus and establish its schema, row count, temporal resolution and concentration before modelling. The second is to implement a chronological reference protocol and train-only feature encoding so that later observations do not influence the fitted category maps or baseline detector. The third is to verify that TreeSHAP explanations are numerically consistent with the model output being explained.

The methodological objective is to compute feature drift, attribution drift and feature-level coupling, then translate their combinations into interpretable diagnostic states. The evaluation objective is to compare static, periodic, feature-only, SHAP-only, dual and coupling-based adaptation decisions under the same controlled scenarios. Finally, the capstone must provide independent checks, uncertainty estimates, reproducible artifacts and a working demonstration that allow another reader to inspect the conclusions.

## 2.4 Problem Statement

Given an unsupervised CloudTrail anomaly detector trained on historical observations, determine whether a later change warrants adaptation using only the observed feature values and model explanations available to the diagnosis stage. The controller must avoid using attack labels as inputs, preserve a trace of its decisions and distinguish uncertainty from a confirmed diagnosis. Its value must be assessed through false-positive burden, detection performance and unnecessary adaptation rather than through alarm counts alone.

The main experimental questions are whether attribution drift changes the update decisions made from feature drift alone, whether coupling identifies a useful subset of joint alarms, and whether a source-calibrated rule transfers to an independent corpus. The design allows negative answers. In particular, equal performance between two policies is reported as equality rather than evidence that the more complicated policy is better.

## 2.5 Project Plan

The project progressed from data audit and literature positioning to baseline modelling, explanation validation, drift measurement and controlled evaluation. Subsequent work added coupling, robustness experiments, independent detector validation and transfer calibration. Reporting followed the saved results so that the document could be revised without rerunning model training simply to reproduce a table.

@table phases

The current Review–3 outcome is a working research prototype with a documented experimental package. The longer-term journal contribution requires stronger independent temporal recovery experiments and completion of the separate literature-screening process. These remaining activities do not change which implementation modules are already available for the capstone demonstration.

# 3 TECHNICAL SPECIFICATION

## 3.1 Requirements

The requirements follow from the research question and from the evidence limits of the reused data. The pipeline must preserve source integrity, make temporal assumptions visible and prevent evaluation-only labels from entering model fitting or diagnosis. It must also provide a reproducible link between configuration files, generated data and reported metrics. A model score without this context would be difficult to interpret during a review or replicate afterwards.

### 3.1.1 Functional Requirements

@table functional

The diagnosis layer must return an explicit state for each evaluated window. The coupled extension distinguishes stable, likely benign drift, model-relevant drift, hidden model instability and review-required cases. The adaptation layer must then apply a selected policy consistently, record whether an update was requested and count the normal candidates used for a possible refit. Evaluation must retain scenario and seed identifiers so that comparisons remain paired.

### 3.1.2 Non Functional Requirements

Reproducibility is supported through fixed random seeds, pinned dependencies, deterministic category maps and saved intermediate artifacts. Auditability requires the source checksum, feature order and threshold configuration to remain available. Interpretability requires both aggregate scores and per-feature evidence; an unexplained binary drift flag would not meet the project's purpose.

@table nonfunctional

Resource use is managed through chunked CSV processing and bounded scoring and explanation samples. These choices make the system practical on a local CPU, but they also mean that attribution summaries describe the sampled events rather than every row in the original corpus. The sampling limit is therefore part of the experimental specification and is considered in the robustness discussion.

## 3.2 Feasibility Study

### 3.2.1 Technical Feasibility

The implementation uses established Python libraries for tabular processing, tree-based anomaly detection, SHAP explanations and statistical evaluation. No GPU-specific dependency is required by the core design. The input file is processed in chunks, while saved monthly distributions and event samples reduce repeated access to the full source. Model artifacts are stored through joblib so that reporting stages can inspect an existing model without fitting it again.

The main technical constraint is the quality and resolution of the available data. Month-level timestamps are suitable for a coarse longitudinal comparison, but a short attack sequence or a minute-level detection delay cannot be reconstructed from that export. The richer timestamp export has been audited and contains day/hour information, yet it belongs to the same underlying corpus. It may support later experiments but does not count as independent validation.

### 3.2.2 Economic Feasibility

The prototype reuses an existing dataset and open-source software. Its main costs are local CPU time, storage for artifacts and the work needed to inspect literature and results. Because it does not create AWS resources or call paid inference services as part of its detection pipeline, the experiment does not incur a demonstrated cloud deployment cost. This supports feasibility for a student capstone, but it is not an estimate of operating cost for a production security service.

Repeated SHAP computations, retraining runs and bootstrap comparisons are the most expensive analytical stages. Saved outputs reduce the cost of report generation and demonstration. The cost-sensitivity experiment discussed later considers hypothetical consequences of missed security changes, false alerts and unnecessary updates. Those weights are analytical assumptions and are not monetary measurements from an organisation.

### 3.2.3 Social and Operational Feasibility

An analyst can use the prototype to inspect changes in cloud behaviour and the associated detector evidence. Its diagnostic vocabulary is intended to make uncertainty visible. A review-required output is useful when the available signals disagree, because forcing such a window into a security category would create an unsupported claim. Any operational deployment would still need analyst feedback, incident validation and a process for approving model versions.

Cloud audit logs may contain account identifiers and access-related metadata. The feature contract deliberately avoids using raw access keys, account IDs, IP addresses and full identity ARNs as model inputs. This reduces dependence on direct identifiers and limits exposure in generated outputs. It does not amount to a complete privacy assessment of the source dataset or establish permission to publish raw records.

## 3.3 System Specification

### 3.3.1 Hardware Specification

The demonstrated environment is a local Windows workstation using CPU execution. The design requires enough storage for the approximately 831 MB source CSV, model artifacts, controlled results and generated figures. The source path is configured externally and remains read-only. Exact minimum RAM and processor requirements have not been benchmarked, so the report does not present an untested hardware minimum. Chunked processing and bounded samples are the mechanisms used to control memory consumption.

### 3.3.2 Software Specification

The project declares Python 3.11 and uses pandas and NumPy for data handling, scikit-learn for detectors, SHAP for attribution, SciPy for distributional statistics, joblib for model persistence and pytest for automated checks. YAML files hold the dataset, temporal, model, benchmark, explanation and adaptation settings. The dependency file records the reproducible environment; the artifact-report builder is separate from the anomaly-detection pipeline.

@table configuration

## 3.4 Data Dictionary and Feature Contract

The audited CSV contains 18 source columns. These include event identifiers, time, source address, user agent, event name and source, region, version, identity attributes, error fields and instance type. A subset is selected for the detector to keep feature order stable and permit external mapping. The `isRoot` indicator is derived from `userIdentitytype`; it is not an additional source column.

@table features

Category maps are fitted on training data only. Each observed training category receives a deterministic integer code, and a later unseen value maps to −1. Missing categorical values become the explicit string Unknown before mapping. This behaviour makes the encoding reproducible and avoids fitting a new vocabulary on the test set. Ordinal integer codes can nevertheless impose an artificial numeric ordering on nominal categories. That representational limitation remains relevant to both the anomaly detector and the perturbation experiments.

# 4 DESIGN APPROACH AND DETAILS

## 4.1 System Architecture

The architecture separates data preparation, model evidence, diagnosis, adaptation and evaluation. The audit module reads the source and writes a provenance manifest. Temporal preparation constructs month-level distributions and records the chronological partition. The event-feature module then produces a stable matrix for the baseline detector. TreeSHAP receives the fitted model and the same feature order, and drift monitoring compares current samples with the reference.

@figure architecture

The diagnosis module uses the drift magnitudes and alignment scores to assign a state. The controller evaluates a selected update policy and, where requested, creates a candidate detector from replay data and baseline-normal current rows. Evaluation uses the hidden controlled labels only after predictions have been made. Finally, the reporting layer reads saved artifacts to build tables and figures. These interfaces keep a reporting change from silently changing an experiment.

The independent corpus uses the same seven-feature contract but has its own train/test archives and manifest. It is evaluated through a separate path because its labels and temporal construction differ from the primary corpus. The transfer-calibration experiment is also recorded separately from the source-tuned thresholds. This preserves the meaning of a held-out source evaluation while making the target-distribution calibration visible.

## 4.2 Design

### 4.2.1 Data Flow Diagram

The data-flow design has two information paths. The model path carries event features, anomaly predictions, SHAP values and drift scores. The evaluation path carries scenario identities and changed-row masks. The paths meet only when performance is measured. The source manifest and configuration provide traceability around both paths, but neither is an attack label supplied to the detector.

@figure dataflow

This boundary is necessary because the controlled generator knows which records it selected for perturbation. If those masks were supplied to the diagnosis stage, the experiment would no longer evaluate an unlabelled decision rule. The source code instead sends the perturbed feature matrix to the detector and computes the evaluation mask separately. The report treats the mask as a controlled target definition, not as organic incident ground truth.

### 4.2.2 Use Case Diagram

The main actor is a researcher or security analyst. The actor can audit the configured corpus, reproduce experiments, inspect drift evidence, compare update policies and explain the saved results during a demonstration. The local filesystem supplies the read-only dataset and stores generated artifacts. No AWS enforcement role participates in the implemented workflow.

@figure usecase

The most important use case is reviewing a changed window. The actor examines feature drift, attribution drift and coupling before considering the diagnostic state. If a policy requests adaptation, the candidate-count output and paired evaluation show what was done and how the resulting model behaved. A reviewer can also select a stable or benign scenario to check whether an update was avoided.

### 4.2.3 Component and Class Responsibilities

The repository uses Python functions and scripts rather than a deep object-oriented class hierarchy. The design diagram therefore describes actual module responsibilities and the data structures exchanged between them. A model artifact groups the fitted estimator, category maps and feature names; DataFrames and JSON documents carry the remaining outputs. Introducing fictional runtime classes into the report would make the design less faithful to the implementation.

@figure components

`src/features` owns feature preparation, `src/drift` owns measurement and diagnosis, and `src/adaptation/controller.py` owns policy triggers and protected retraining. The experiment layer orchestrates scenarios and the evaluation layer computes metrics. Scripts in `scripts/` connect these reusable components to configured inputs and output files. This arrangement allows unit tests to target the decision logic without rerunning the entire dataset pipeline.

### 4.2.4 Sequence Diagram

For a controlled experiment, the runner loads the baseline artifact, selects a training-derived reference sample and generates a current sample for a named scenario and seed. The detector scores that sample and the explainer produces attributions. Drift functions compare the reference and current evidence, after which diagnosis returns a state. The controller then decides whether to refit, and the selected detector predicts the current rows for evaluation.

@figure sequence

Each policy/scenario run starts from the baseline detector. The current experiment is therefore a comparison of independent update decisions and immediate outcomes, rather than a persistent online model trajectory. The periodic policy acts on the ordered scenario-run index. That detail matters: its interval of three refers to experimental rows, not three months of live AWS use. Long-running recovery and model-version histories remain future validation tasks.

## 4.3 Decision States and Interpretation

The dual rule compares feature and attribution scores with their thresholds. Low values for both produce stable. High feature drift with low attribution drift produces benign_drift, indicating that the measured input change did not coincide with a sufficiently large explanation change. High values for both produce security_relevant_drift under the configured rule. Low feature drift with high attribution drift is retained as review_required.

The coupled extension adds alignment as a third condition. High feature and SHAP drift produce a model-relevant state only when coupling also exceeds its threshold. When feature drift is low and attribution drift is high, low alignment yields hidden_model_instability; otherwise the result remains review_required. The term hidden describes disagreement between the observed signals. It does not identify a software defect or prove that the fitted model itself changed.

@table diagnosis

The adaptation policies use these states consistently. Static never requests an update, periodic uses the configured interval, and the single-signal policies use their corresponding threshold. Dual and coupled policies request an update only for their model-relevant state. This makes the difference between diagnosis and action explicit: a state describes measured evidence, while a policy determines what the system does with it.

## 4.4 Design Choices and Alternatives

The baseline uses a small tree ensemble because it is reproducible and compatible with TreeSHAP. More expressive representations, such as sequences or identity-resource graphs, would answer different questions and would require finer temporal or relational information. They are reasonable future directions, but adding them without a supported data protocol would not improve the validity of the current experiment.

The coupling design retains per-feature vectors instead of multiplying aggregate scores. Multiplication can make two large scores appear jointly important without revealing whether the same features explain them. Cosine alignment tests that relationship directly, but it ignores overall magnitude and can be high for two very small vectors. The implementation therefore interprets coupling only alongside the feature and SHAP magnitude gates and handles degenerate vectors explicitly.

# 5 METHODOLOGY AND TESTING

## 5.1 Dataset Audit and Provenance

The audit records the source path, file size, SHA-256 checksum, schema, row count, malformed rows and selected category concentrations. The resulting manifest establishes which exact export was analysed. This is especially useful when several similarly named CloudTrail files are available or a later export changes the row count. The verified source contains 1,939,207 rows and 18 columns, with no malformed rows observed by the audit.

@table dataset

The corpus is highly concentrated. August 2019 contains 1,347,680 records, approximately 69.5% of all rows, and RunInstances accounts for 1,323,105 events. Large changes in volume can therefore dominate pooled distributions. These facts affect how drift signals should be interpreted and motivate reporting the temporal split and sample sizes. They also caution against presenting an overall score as representative of every month or every type of activity.

## 5.2 Temporal Preparation and Sampling

The primary export covers 45 monthly windows from February 2017 to October 2020. The first 27 windows, ending in April 2019, form the training partition. May 2019 to January 2020 provides nine validation windows, and February to October 2020 provides nine test windows. This ordering preserves a historical reference and prevents later categories from being fitted into the baseline vocabulary.

The monthly timeline and the controlled benchmark use different evaluation units. The timeline compares real observed months. The controlled benchmark constructs samples from training-derived rows and reserves independent random seeds for validation and test scenarios. Its held-out seeds are not the nine held-out calendar months. Keeping these two protocols explicit is necessary to understand what a reported diagnosis score means.

The model configuration bounds score samples to 1,000 events per window, and the controlled benchmark uses a 200-row reference sample. These limits make repeated explanations and refits practical. They do not imply that every event in the 1.94-million-row corpus received an explanation. The detector and sample-size ablations assess part of the sensitivity introduced by these choices.

## 5.3 Baseline Detector and SHAP Validation

The baseline Isolation Forest has 100 estimators, contamination 0.05 and random state 42. The contamination setting defines a fitted outlier cutoff; it is not an estimate that five percent of the real source consists of attacks. The model is trained on the encoded reference data, saved with its feature contract and reused by the explanation and drift scripts.

For an event x, the explanation has the additive form g(x) = E[g(X)] + Σφj(x), where g denotes the internal model output explained by TreeSHAP. The implementation checks the reconstruction numerically. The maximum recorded residual is 2.6645352591003757 × 10⁻¹⁴, which is consistent with numerical precision for the checked samples. This establishes consistency of the explanation computation, rather than security correctness of the detector.

The distinction between g(x) and a displayed anomaly score is important for Isolation Forest. A tree-based explanation may concern the model's internal path-related output rather than a probability of attack. The report therefore avoids interpreting a SHAP magnitude as a causal risk contribution or a calibrated probability. What matters for monitoring is that the output and feature order remain consistent across reference and current samples.

## 5.4 Feature Distribution Drift

For each monitored categorical feature, the system aligns the union of categories observed in the reference and current windows. A small smoothing value prevents zero probabilities from making the divergence undefined. If pi and qi are the smoothed reference and current proportions, the population stability index is PSI = Σ(qi − pi) ln(qi / pi). The feature score averages the categorical PSI values and can include a scaled scalar-shift term when scalar features are explicitly configured.

Jensen–Shannon divergence is retained as an additional descriptive measure. Its midpoint distribution is m = (p + q)/2, and the divergence is one half of each distribution's Kullback–Leibler divergence to m. The two measures describe distributional separation in different ways. Their values depend on category frequencies and smoothing, so thresholds are calibrated within the experiment instead of adopting an unexplained universal cutoff.

The five shared drift features are eventName, eventSource, awsRegion, userIdentitytype and errorCode. Each produces an individual PSI value, allowing a reviewer to identify which field contributed to the aggregate. A large region shift may be consistent with a deployment change, while an API shift may affect a detector differently. Such interpretations require context; the statistical measure alone does not supply that context.

## 5.5 Attribution Drift

The attribution module compares signed SHAP distributions between the reference and current samples. For each feature, it computes the Wasserstein distance and normalises it by the reference attribution standard deviation with a small stabilising constant. It also compares the sets of top-ranked features and records a rank-based term. The implemented aggregate adds normalised mean Wasserstein distance, top-k set disagreement and its rank-disagreement term.

The script separately records mean signed attribution shift and mean absolute attribution displacement. The latter compares E|φj| between reference and current samples, then retains each feature's absolute difference. These summaries answer different questions: a signed shift can reveal a change in contribution direction, while an absolute shift measures a change in contribution magnitude. Retaining both is more informative than reporting a single scalar explanation alarm.

The existing rank term is a diagnostic summary based on sorted feature-index orders. It should not be interpreted as a calibrated semantic ranking distance or an independent statistical test. The report gives priority to the directly interpretable Wasserstein, top-k overlap and per-feature displacement outputs when discussing the model's behaviour. More rigorous ranking measures can be assessed in a later methodological revision.

## 5.6 Attribution Feature Coupling

For a current window, let d be the vector of the five shared feature PSI values. Let a contain the absolute differences between current and reference mean absolute SHAP values for those same features. The cosine coupling is C = (d · a) / (‖d‖ ‖a‖). Both vectors are non-negative, so the resulting alignment lies between zero and one. If either vector has negligible norm, the implementation returns zero rather than dividing by an unstable denominator.

A high cosine score indicates that the feature-level pattern of distribution drift points in a similar direction to the pattern of attribution displacement. It does not establish that an attack occurred, and it does not imply that either pattern is large enough to matter. The diagnostic rule therefore first uses the feature and attribution thresholds and then considers alignment. This guards against treating a high cosine between tiny vectors as sufficient evidence for adaptation.

The implementation also records centred alignment and rank alignment. Centred alignment maps Pearson correlation to the interval [0, 1] using (r + 1)/2; rank alignment applies the same mapping to Spearman correlation. Constant or degenerate inputs receive zero. The conservative variant takes the minimum of cosine and centred alignment. These are interpretable ablations of the alignment definition, not claims that the mathematical operators themselves are novel.

## 5.7 Threshold Selection and Transfer Calibration

Source thresholds are tuned on validation scenarios only. Candidate feature and SHAP thresholds are drawn from fixed validation-score quantiles. The dual rule selects the combination with the best macro-F1 over the three represented target classes. The coupled search additionally varies an alignment threshold. Its stored macro-F1 uses five output classes, including hidden instability and review-required, which are not equivalent to the dual rule's three-class reporting basis. The two validation numbers should therefore not be read as a direct matched-class comparison.

The saved dual thresholds are 0.1544545922 for feature drift and 0.9659935889 for attribution drift. The saved cosine and conservative coupling thresholds are both 0.8640697362. These are experiment-specific settings, rather than security constants. They remain fixed for the held-out source scenarios and are transferred unchanged in the source-threshold external experiment.

The separate transfer-calibration experiment uses unlabelled target-window conservative scores after applying the transferred feature and SHAP gates. It sorts the finite unique scores, finds the largest adjacent gap and places the threshold at that gap's midpoint. If the score set cannot define a gap, the implementation uses a fallback. Attack labels are not used to choose the threshold, but the target distribution is used. The result is transductive calibration on the evaluated batch, not prospective validation on a later unseen stream.

## 5.8 Controlled Scenario Construction

The benchmark contains seven scenarios: stable, benign region, benign identity, benign service, security privilege, security defence and security credential. The base intensity is 0.25, meaning that an operation selects one quarter of sample rows for its main field change. A second field, where present, changes at half that intensity. Selected row masks are retained for evaluation, while the detector sees only the altered matrix.

@table scenarios

The scenarios are semantic stress tests, not complete attack emulations. A named API such as AssumeRole can be legitimate, and a changed-row mask does not prove malicious intent. Category values absent from the training vocabulary collapse to the shared unknown code, which can reduce distinctions between scenarios. The perturbation code also changes identity type independently of the derived isRoot column, so some synthetic rows may contain a consistency mismatch. These limitations should inform any security interpretation of benchmark performance.

Five seeds, 0 through 4, generate validation scenarios. Ten seeds, 5 through 14, produce the held-out comparison, giving 70 scenario-seed units for each policy. The same units are reused across policies, allowing paired differences. This design evaluates robustness to the chosen perturbation placement, but the 70 units are not 70 independent operational incidents and should not be described as such.

## 5.9 Protected Adaptation

When a policy requests adaptation, the baseline detector first predicts the current rows. Rows predicted normal become candidate additions to the replay sample. If fewer than ten candidates are available, the controller returns the original detector. Otherwise, it fits a 50-tree Isolation Forest on replay rows plus the accepted current rows, using contamination 0.05 and a reproducible run-specific seed. The candidate count is recorded with the result.

This protection reduces direct exposure to rows the baseline already considers anomalous. It cannot eliminate contamination, because an undetected attack can be predicted normal and admitted. The term protected therefore describes the implemented filter and replay mechanism. A production system would need stronger feedback and update approval; the experiment measures the behaviour of this particular safeguard.

All update policies share the same refitting mechanism. Consequently, differences in policy outcomes mainly reflect which scenario runs request a refit, while the fixed 50-tree refit itself remains part of the treatment. The baseline has 100 trees, so a before/after difference can also reflect estimator configuration. A future experiment should include a refit with matched estimator count to isolate that effect more strictly.

## 5.10 Evaluation Metrics and Statistical Comparison

Event-level precision, recall, F1 and false-positive rate are computed from the controlled mask or independent labels after prediction. Precision is TP/(TP+FP), recall is TP/(TP+FN), F1 is their harmonic mean, and FPR is FP/(FP+TN). For benign controlled scenarios, all rows are treated as negative for evaluation. Zero-division handling is explicit in the metrics implementation, which matters when a scenario has no positive rows.

Trigger rate is the fraction of scenario runs where a policy requested adaptation. Unnecessary-adaptation rate is the fraction of all evaluated runs where a request occurred in a non-security scenario. It is not the fraction of requested updates later judged unnecessary. Static therefore has zero unnecessary updates by construction, without that result implying that it makes adequate security decisions.

Paired comparisons use the same scenario-seed units for both policies. The saved inference table includes mean differences, bootstrap 95% intervals, Wilcoxon tests and Benjamini–Hochberg adjusted values. These summaries quantify evidence within the controlled protocol. Shared source samples and scenario definitions limit the independence of the units, and the intervals do not capture uncertainty about real attack diversity or future AWS deployments.

## 5.11 Testing Strategy and Traceability

The automated suite exercises dataset auditing, temporal splits, category encoding, detector behaviour, SHAP additivity, drift functions, diagnosis states, adaptation rules, inference utilities and end-to-end artifact structure. The saved validation record reports 28 passing tests. Unit checks target mathematical and decision boundaries; integration checks verify that stages agree on schemas and outputs. Passing these checks establishes software consistency within their coverage, rather than external security effectiveness.

@table tests

The test suite includes explicit cases for low/high drift combinations and for the largest-gap threshold's deterministic behaviour. Adaptation tests inspect the policy trigger rules and candidate-filtered retraining. Report-level verification separately checks that numbers match saved outputs and that the source template's styles and section geometry are preserved. This distinguishes software testing from evidence review and document-layout quality assurance.

# 6 PROJECT DEMONSTRATION

## 6.1 Demonstration Environment

The demonstration runs locally from the project directory with the pinned Python environment. The configured primary dataset remains at its external read-only path. Saved model and result artifacts are available for inspection, and the implementation scripts expose the underlying computations. This allows the review to show both the working pipeline and the provenance of a reported result without relying on live internet access or paid AWS resources.

The end-to-end entry point is `python scripts/run_all.py`. It audits the data, creates temporal features, trains and scores the baseline, generates explanations, computes drift, runs controlled diagnosis and adaptation, evaluates cost sensitivity and builds result summaries. Full regeneration should be started with sufficient time because it processes the configured source and fits models. During a short review, existing artifacts provide a reproducible checkpoint while selected modules demonstrate the working logic.

## 6.2 Demonstration Sequence

@table demo

The opening demonstration shows the manifest and the chronological split. This establishes the input and prevents confusion between the original corpus and the independent labelled archive. The next step follows an event sample through its encoded features, detector prediction and explanation. The reviewer can then inspect the monthly drift timeline and the per-feature coupling evidence for a window.

The controlled demonstration compares a benign scenario with a security-related scenario. The presenter shows the feature and SHAP scores, the diagnostic state and the update decision for the same seed. It then opens the saved adaptation rows to inspect candidate counts and detection metrics. A policy comparison makes visible that avoiding updates and improving detection are separate objectives.

The final demonstration examines independent validation. It first shows detector metrics from the labelled external corpus and then the small temporal checkpoint. The source-tuned coupling failure and the target-calibrated result are presented together, including the 12-window size. This is a useful demonstration of research reasoning because it explains why a threshold that works on one corpus may fail on another.

## 6.3 Expected Observable Outputs

The data-audit stage produces `data_manifest/real_cloudtrail_manifest.json`. Temporal preparation produces `data/processed/temporal_split.json` and monthly features. The detector is stored in `models/isolation_forest_event_baseline.joblib`. Score and SHAP samples are saved under `data/scores`, while individual and combined drift files are written under `data/drift`. The controlled outputs retain split, scenario and seed identifiers under `data/benchmark`.

The result figures include the monthly drift timeline, diagnosis confusion matrix and adaptation-policy comparison. These are derived from saved experiment artifacts rather than manually entered chart values. External manifests and metrics are stored separately under `data/external_validation`. A complete demonstration should trace at least one figure or table back to its source file and configuration.

## 6.4 Demonstration Boundaries and Recovery

The prototype demonstrates offline drift analysis and protected refitting. It does not require a live cloud account or display a claim that an IAM remediation was executed. If the source path is unavailable on another machine, the saved manifests and artifacts remain inspectable, but a full data rebuild requires the same source file and checksum. That dependency should be checked before the offline review begins.

The automated verification command is `python -m pytest tests -q`. A fresh run supports the software demonstration, while a comparison of saved checksums confirms that the intended source was used. The current report records the established validation evidence and does not invent execution times, response latency or production availability measurements that were not collected.

# 7 RESULT AND DISCUSSION

## 7.1 Real Corpus Observation

The real-data timeline shows feature and explanation distributions changing across the 45 monthly windows. The reference is historical training data, so the curves describe deviations from that reference rather than a sequence of confirmed incidents. Their purpose is to expose where the model's input and attribution profiles move together or differ. Without attack labels, neither a peak nor a quiet period can be assigned attack recall.

@figure monthly

The concentration of events in August 2019 is relevant to interpretation because it lies in the validation calendar partition and contains most source rows. Sampling can reduce computational domination by large windows, while pooled frequency references can still reflect unequal activity levels. These effects make window construction and aggregation choices part of the reported method. Further work should compare balanced and volume-weighted references explicitly.

## 7.2 Controlled Diagnosis Results

The validation-selected dual rule achieved macro-F1 of 0.7306 over its three represented diagnosis classes. The coupled validation search recorded 0.4384 using a five-class output basis. The latter includes review and instability classes without equivalent controlled target categories, so the two stored values do not provide a clean three-class superiority comparison. The held-out confusion matrix gives the relevant breakdown for the configured dual diagnosis.

@figure confusion

These results establish that the rule separates some of the defined perturbation patterns under the chosen sample and seed protocol. They do not establish classification accuracy on the original unlabelled months. A stronger diagnosis claim would require independently observed benign changes and verified security incidents, with label definitions and timing established outside the generator.

## 7.3 Adaptation Policy Comparison

@table adaptation

The dual, SHAP-only, cosine-coupled and conservative-coupled policies produced the same current held-out adaptation metrics. Their trigger rate was 0.2429 and their unnecessary-adaptation rate was zero across the evaluated runs. This equality is important: the benchmark does not demonstrate an incremental adaptation benefit from adding the coupling gate, nor does it demonstrate a dual-signal advantage over SHAP-only under these settings.

Feature-only requested updates more often, at a rate of 0.7571, and had an unnecessary-update rate of 0.3286. It also achieved the lowest aggregate FPR in this table, 0.1825, while its mean F1 was 0.2734. A lower false-positive burden alone therefore does not establish a better security trade-off. The static detector had F1 0.2901 and FPR 0.4282, while periodic updates gave F1 0.2888 and FPR 0.3160.

@figure policies

The averages include stable and benign scenarios whose positive-class F1 can be zero by convention. Their magnitude should be read with the scenario composition and metric definition. Separate security recall and benign false-positive summaries are useful complements. The policy chart is a compact comparison, while the scenario-level results retain the information needed for a more detailed analysis.

## 7.4 Paired Statistical Evidence

The paired dual-minus-static FPR difference was −0.088478, with a bootstrap 95% interval from −0.127232 to −0.056106. This corresponds to approximately 8.85 percentage points in the evaluated benchmark. The Wilcoxon p-value was 0.0002896 and the Benjamini–Hochberg adjusted value was 0.0004344. Within the defined units, the evidence supports a lower FPR for dual than static.

The paired F1 difference was −0.002796, with a 95% interval from −0.018096 to 0.011245. This interval crosses zero and does not support an F1 improvement. It also does not prove formal equivalence or non-inferiority, because an equivalence margin and corresponding test were not specified. The appropriate conclusion is narrower: the observed FPR reduction was accompanied by an inconclusive F1 difference in this experiment.

@table paired

The bootstrap and paired test operate on 70 scenario-seed units. Their statistical precision should not be confused with broad deployment coverage. The samples share a baseline and generator, and the security targets describe synthetic interventions. Independent temporal recovery experiments would test a different and more operationally demanding claim.

## 7.5 Detector and Sample Size Robustness

The detector-family ablation used the controlled robustness protocol, which differs from the adaptation-policy experiment. Under that protocol, a 100-tree Isolation Forest achieved security recall of 0.4918 and security F1 of 0.6185, with benign FPR of 0.0529. Increasing the ensemble to 200 trees gave security F1 of 0.6250. One-Class SVM achieved higher security recall and F1 there, but also a higher benign FPR. Local Outlier Factor performed poorly under this particular controlled configuration.

@table robustness

Sample-size results were also non-monotonic. At 100 rows, security recall was 0.0884; at 200 it was 0.4918; and at 500 it was 0.4152. The sample construction and category composition change the difficulty of the task, so increasing row count did not automatically improve recall. These measurements support configuration sensitivity rather than a universal optimum at 200 rows.

The different protocols should not be merged into a single detector ranking. Controlled ablations examine the implemented generator and sampling choices. The independent labelled corpus examines another data distribution. The fact that the rankings change across them is itself a reason to retain external validation and describe each experimental setting.

## 7.6 Independent Detector Validation

The independent Cloud Log Sampling Dataset contains 16,495 benign training records and 24,087 mixed test records, including 2,585 attack-labelled and 21,502 benign records. The feature mapper aligns it with the same seven detector inputs. Separate archive checksums and a manifest record its origin and split. The experiment fits on the benign training archive and evaluates against labels in the mixed test archive.

@table externaldetectors

Isolation Forest obtained F1 0.4519 and recall 0.7137. Local Outlier Factor obtained higher recall, 0.9954, and F1 0.5334, with a higher FPR of 0.2088. One-Class SVM produced very low recall and F1 in this external setting despite performing differently in the controlled robustness experiment. These results show that a detector choice cannot be justified solely from one benchmark.

This validation supports the portability of the feature mapping and gives independent detection evidence. It does not validate the entire SHAP-driven adaptation loop, because detector-only accuracy is a different outcome from drift diagnosis and post-update recovery. The following checkpoint addresses part of diagnosis transfer while retaining its small scope.

## 7.7 External Temporal Diagnosis and Transfer

@table externaldiagnosis

Feature-only, SHAP-only and dual policies each achieved scenario-window F1 of 0.9524, with FPR 0.5. That false-positive rate reflects the small number of benign windows: the checkpoint contains 12 scenario windows, including ten security windows and two benign windows. Equal results provide no evidence that the dual gate added value over the single signals in this checkpoint.

The source-calibrated cosine and conservative coupling rules obtained precision 1.0 but recall 0.1, giving F1 0.1818. They rejected most security windows under the transferred threshold. The result exposes a threshold-portability problem rather than a benefit from conservative gating. Zero FPR in this case was achieved at the cost of missing most positive windows.

The label-free largest-gap calibration selected a conservative alignment threshold of 0.4990795305 and achieved precision, recall and F1 of 1.0 with zero FPR on the same checkpoint. This indicates that the target-score structure could separate these windows under the tested procedure. It remains an exploratory transductive result based on a small batch. A later unseen-period evaluation is needed before claiming that this calibration remains reliable under new workloads or incident types.

## 7.8 Cost Analysis

The cost-sensitivity experiment defines loss using missed-security cost times one minus recall on security scenarios, false-alarm cost times FPR on benign scenarios, and a penalty for unnecessary adaptation. The grid varies missed-security cost over 1, 2, 5 and 10; false-alarm cost over 0.5, 1, 2 and 5; and update penalty over 0, 0.25, 0.5, 1, 2 and 5. These are relative weights for sensitivity analysis rather than currency values.

The saved analysis does not identify the proposed method as a universal winner. Static and periodic policies are preferred across many cost combinations, while feature-only is preferred in a smaller subset. This finding reinforces the distinction between reducing updates, reducing false positives and maintaining recall. An operational recommendation needs an explicit cost model and acceptance criterion rather than the highest value in a single metric column.

Computational cost is discussed qualitatively because end-to-end runtime and peak memory were not recorded as controlled measurements. The bounded samples and saved artifacts make the prototype practical to reproduce, but they are not evidence for real-time throughput. A production feasibility study should measure latency, memory, explanation overhead and update duration on the intended workload.

## 7.9 Novelty Assessment

The contribution is the implemented CloudTrail-specific protocol and the feature-level coupling test that connects observed distribution changes to attribution displacement before adaptation. The framework makes diagnosis, update requests and immediate detection outcomes inspectable within the same experiment. Its transfer-calibration extension also turns a source-threshold failure into a testable question about unlabelled target-score structure.

The results currently support a restrained novelty claim. Coupling is neutral in the controlled adaptation comparison, source tuning transfers poorly and target calibration succeeds only on a small checkpoint. The research value lies in a clear method, reproducible comparisons and honest boundaries around the evidence. A journal paper should establish incremental value through stronger baselines, matched update configurations and independent temporal recovery before making broader claims.

## 7.10 Threats to Validity

Construct validity is limited by the scenario definitions. API substitutions and selected-row masks are useful controlled targets, but they cannot reproduce the intent, dependencies and timing of complete incidents. Derived-feature inconsistencies and unknown-category collapse can also influence the synthetic task. Diagnosis names should therefore be interpreted in relation to the configured benchmark rather than as verified incident categories.

Internal validity is affected by training-sample concentration, ordinal encoding, fixed baseline composition and the change from 100-tree baseline to 50-tree adapted models. Validation-only tuning avoids direct test-label selection, but it does not eliminate overfitting to a small family of perturbations. The coupled and dual validation macro-F1 definitions also differ, which limits direct comparison of their stored tuning scores.

External validity is limited by one primary unlabelled corpus, one independent labelled corpus and a 12-window temporal checkpoint. Target-based threshold estimation can be unstable when a score distribution has no clear gap or contains many contaminated windows. The current adaptation runs are independent scenario experiments, so they do not establish online detection delay, cumulative recovery, long-term contamination resistance or model-version stability.

Conclusion validity depends on reporting all relevant outcomes. FPR improvements cannot stand in for improved F1, and zero unnecessary updates cannot by itself establish an effective controller. The report retains neutral and negative comparisons and makes the unit of analysis explicit. These practices reduce overstatement while keeping the implemented capstone contribution clear.

# 8 CONCLUSION

## 8.1 Work Completed

The capstone implements a reproducible CloudTrail workflow covering dataset audit, chronological preparation, anomaly detection, SHAP validation, drift diagnosis and policy-driven refitting. Controlled experiments, statistical comparisons, robustness checks and independent validation provide inspectable evidence for the live demonstration.

Attribution–feature coupling tests whether features that changed distribution also changed their attribution magnitudes. Conservative alignment and label-free target calibration extend this question through separately evaluated configurations.

## 8.2 Findings

The dual policy reduced FPR relative to static by approximately 0.0885 in the controlled experiment. Its F1 difference was inconclusive. Coupled policies and SHAP-only produced the same current policy metrics as dual, so the experiment does not establish an incremental adaptation benefit from coupling.

External detector rankings and threshold behaviour differed from the controlled setting. Source-tuned coupling had poor recall, while largest-gap calibration separated the small checkpoint perfectly. Prospective evaluation is needed to test whether that calibration remains reliable on later unseen windows.

## 8.3 Future Work

Further work should preserve derived-feature consistency in perturbations, improve unknown-category handling and compare matched-size baseline and adapted ensembles. Alternative encodings and explanation-drift baselines should use the same class definitions and update budgets.

Independent temporal validation should include separate calibration and test periods, verified changes and a persistent update sequence. It can then measure recovery, delay, false alerts and contamination. PRISMA screening and manuscript preparation remain requirements for journal submission.

## 8.4 Capstone Outcome

The outcome is a working capstone prototype with documented interfaces, tested algorithms and repeatable experiments. It supports the BCSE497J Project-I review and provides a concrete basis for further research, with its present evidence and limitations clearly stated.

# 9 REFERENCES

[1] F. T. Liu, K. M. Ting and Z.-H. Zhou, “Isolation Forest,” Proceedings of IEEE ICDM, 2008, pp. 413–422. doi:10.1109/ICDM.2008.17.

[2] S. M. Lundberg and S.-I. Lee, “A Unified Approach to Interpreting Model Predictions,” Advances in Neural Information Processing Systems, vol. 30, 2017.

[3] T. S. Sethi and M. M. Kantardzic, “On the Reliable Detection of Concept Drift from Streaming Unlabeled Data,” Expert Systems with Applications, vol. 82, pp. 77–99, 2017. doi:10.1016/j.eswa.2017.04.008.

[4] F. Maggi, W. Robertson, C. Kruegel and G. Vigna, “Protecting a Moving Target: Addressing Web Application Concept Drift,” RAID, 2009. doi:10.1007/978-3-642-04342-0_2.

[5] A. Kuppa and N.-A. Le-Khac, “Learn to Adapt: Robust Drift Detection in Security Domain,” Computers and Electrical Engineering, 2022. doi:10.1016/j.compeleceng.2022.108239.

[6] Han et al., “Anomaly Detection in the Open World: Normality Shift Detection, Explanation and Adaptation,” NDSS, 2023. doi:10.14722/ndss.2023.24830.

[7] Li et al., “Concept Drift Adaptation by Exploiting Drift Type,” ACM Transactions on Knowledge Discovery from Data, 2024. doi:10.1145/3638777.

[8] Lee et al., “Explainable Artificial Intelligence-Based Model Drift Detection Applicable to Unsupervised Environments,” Computers, Materials & Continua, 2023. doi:10.32604/cmc.2023.040235.

[9] Amazon Web Services, “Feature Attribution Drift for Models in Production,” Amazon SageMaker documentation. https://docs.aws.amazon.com/sagemaker/latest/dg/clarify-model-monitor-feature-attribution-drift.html.

[10] Amazon Web Services, “Understanding CloudTrail Events,” AWS CloudTrail documentation. https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-events.html.

[11] Varma and Ramya, “An Explainable Machine Learning and Large Language Model Framework for Anomaly Detection in AWS CloudTrail Logs,” ICNGN, 2025. doi:10.1109/ICNGN67480.2025.11413642.

[12] Arora et al., “A Systematic Review on Detection and Adaptation of Concept Drift in Streaming Data Using Machine Learning Techniques,” WIREs Data Mining and Knowledge Discovery, 2024. doi:10.1002/widm.1536.

[13] PRISMA Statement, “PRISMA 2020 Statement and Checklist.” https://www.prisma-statement.org/.

[14] ArielCyber, “Cloud Log Sampling Dataset,” public dataset repository. https://github.com/ArielCyber/cloud_log_sampling.

[15] Scikit-learn developers, “IsolationForest,” scikit-learn API documentation. https://scikit-learn.org/stable/.

[16] SHAP, “TreeExplainer,” API documentation. https://shap.readthedocs.io/.

# APPENDIX A SAMPLE CODE

## A.1 Core Coupled Diagnosis

The following excerpt is taken from the implemented diagnosis module. It shows how the state depends on feature and SHAP magnitude gates and then on alignment. The output labels are part of the research protocol. The function does not receive attack labels.

@code diagnosis

## A.2 Largest Gap Calibration

The calibration helper uses only finite score values. It sorts unique observations and chooses the midpoint of the largest adjacent gap, with a defined fallback when fewer than two distinct scores remain. The helper supplies a threshold; evaluation labels are applied afterwards to assess its effect.

@code calibration

## A.3 Protected Retraining

This excerpt shows the candidate filter and replay mechanism. A baseline-normal prediction is a screening condition, not verified benign ground truth. The original detector is retained when the minimum candidate count is not met.

@code retrain

## A.4 Reproduction Commands

Run the commands from the repository root in the pinned environment. The full primary pipeline requires the configured source CSV. Independent validation also requires the dataset archives recorded in its manifest. Reporting reads the resulting saved evidence.

@code commands

## A.5 Artifact Traceability

@table artifacts

The manifest checksum is b3aa4fcf28747f4f84457d2d3b76f4c27901bd2e6289bf6d6288cb9587d20589. A reproduction should confirm this value before comparing source-corpus results. The report's metrics are linked to saved experiment files, while the accompanying repository contains the implementation and configuration needed to inspect their provenance. Repository: https://github.com/sani3055/DriftDetection.
