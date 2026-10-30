# Final capstone presentation literature evidence

Checked on 27 October 2026. These are eight selected comparators for the
presentation, not 100 included studies or a completed PRISMA review.
There are five journal articles and three conference papers. Deck citation
numbers are independent of the report's reference numbering.

## 1 Kuppa and Le-Khac 2022 journal

Aditya Kuppa and Nhien-An Le-Khac. Learn to Adapt: Robust Drift Detection in
Security Domain. Computers and Electrical Engineering 102, article 108239.
DOI: https://doi.org/10.1016/j.compeleceng.2022.108239

Security drift detection and recursive updating motivate cautious adaptation.
The project examines a different representation and CloudTrail evaluation.
Publisher-deposited Crossref metadata confirms authors, venue and date.

## 2 Han and colleagues 2023 conference

Dongqi Han, Zhiliang Wang, Wenqi Chen, Kai Wang, Rui Yu, Su Wang, Han Zhang,
Zhihua Wang, Minghui Jin, Jiahai Yang, Xingang Shi and Xia Yin. Anomaly Detection
in the Open World: Normality Shift Detection, Explanation, and Adaptation.
Network and Distributed System Security Symposium (NDSS).
DOI: https://doi.org/10.14722/ndss.2023.24830
Primary source:
https://www.ndss-symposium.org/ndss-paper/anomaly-detection-in-the-open-world-normality-shift-detection-explanation-and-adaptation/

OWAD already integrates normality-shift detection, explanation and adaptation
in security applications. Our integration must not be presented as the first
general system to combine those stages. CloudTrail features, the coupling test
and policy-level evaluation define the narrower project question.

## 3 Lee and colleagues 2023 journal

Yongsoo Lee, Yeeun Lee, Eungyu Lee and Taejin Lee. Explainable Artificial
Intelligence-Based Model Drift Detection Applicable to Unsupervised
Environments. Computers, Materials & Continua 76(2), 1701–1719.
DOI: https://doi.org/10.32604/cmc.2023.040235
Primary source: https://www.techscience.com/cmc/v76n2/54010

The study uses SHAP-based evidence and a drift suspicion metric for DGA
detection. Explanation drift in unsupervised security monitoring is therefore
prior work. The project tests its combination with feature drift and an
explicit CloudTrail adaptation policy.

## 4 Li and colleagues 2024 journal

Jinpeng Li, Hang Yu, Zhenyu Zhang, Xiangfeng Luo and Shaorong Xie. Concept Drift
Adaptation by Exploiting Drift Type. ACM Transactions on Knowledge Discovery
from Data 18(4), article 96, 1–22.
Primary source and DOI: https://doi.org/10.1145/3638777

Type-LDA learns drift-type and change-point information to support adaptation.
Our runtime rule instead uses observed feature and attribution changes, while
controlled validation targets remain part of threshold evaluation. We do not
claim to reproduce or outperform Type-LDA.

## 5 Arora Rani and Saxena 2024 journal review

Shruti Arora, Rinkle Rani and Nitin Saxena. A Systematic Review on Detection
and Adaptation of Concept Drift in Streaming Data Using Machine Learning
Techniques. WIREs Data Mining and Knowledge Discovery 14(4), e1536.
Primary source: https://wires.onlinelibrary.wiley.com/doi/10.1002/widm.1536
DOI: https://doi.org/10.1002/widm.1536

This is review evidence for the problem framing and drift taxonomy, rather
than an experimental CloudTrail comparator or evidence that our review is
complete.

## 6 Decker and colleagues 2024 conference

Thomas Decker, Alexander Koebler, Michael Lebacher, Ingo Thon, Volker Tresp and
Florian Buettner. Explanatory Model Monitoring to Understand the Effects of
Feature Shifts on Performance. ACM SIGKDD Conference on Knowledge Discovery
and Data Mining, 550–561.
DOI: https://doi.org/10.1145/3637528.3671959
Author manuscript: https://arxiv.org/abs/2408.13648
Institutional source: https://mcml.ai/publications/dkl%2B24/

XPE combines optimal transport and Shapley values to explain estimated
performance changes under feature shifts. This supports the broader idea of
connecting input changes to model effects. Our task is a different security
diagnosis and update-policy experiment, not a reproduction of XPE.

## 7 Varma and Ramya 2025 conference

Surya Karthikeya Varma.I and Ramya K. An Explainable Machine Learning and Large
Language Model Framework for Anomaly Detection in AWS CloudTrail Logs. 2025
International Conference on Intelligent Computing and Next Generation Networks
(ICNGN), 1–5.
DOI: https://doi.org/10.1109/ICNGN67480.2025.11413642
Publisher record: https://ieeexplore.ieee.org/document/11413642
Publisher-deposited metadata:
https://api.crossref.org/works/10.1109/ICNGN67480.2025.11413642

This is the direct CloudTrail application comparator in the existing verified
core matrix. It combines anomaly detection and explanation, with reported
simulated-event evaluation. It does not establish the benefit of the coupling
and protected-update policy examined by this project.

## 8 Maseno Sun and Wang 2026 journal

E. M. Maseno, Y. Sun and Z. Wang. Detecting Adversarial Evasion in Deep Learning
Intrusion Detection Systems Using Explainable AI. International Journal of
Information Security 25, article 125. Published 15 July 2026.
Primary source: https://link.springer.com/article/10.1007/s10207-026-01299-x
DOI: https://doi.org/10.1007/s10207-026-01299-x

The study examines explanation displacement and dominant-feature stability in
recurrent network IDS models. This limits any claim that monitoring SHAP
instability in security is new. Its supervised network-traffic task differs
from the unlabelled CloudTrail diagnosis and adaptation task.

## Contribution wording and reporting boundary

The project implements and evaluates a CloudTrail-specific coupling question:
do features that change distribution also change their attribution profile,
and does that alignment improve update decisions? Cosine similarity, SHAP,
Isolation Forest and drift monitoring are established components. Current
controlled policy results are neutral relative to the dual rule. The target
calibration checkpoint is exploratory. No direct superiority over these eight
papers, journal acceptance or completed 100-paper review is claimed.

## Other deck references

9. Isolation Forest: https://doi.org/10.1109/ICDM.2008.17
10. SHAP: https://proceedings.neurips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html
11. CloudTrail schema: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-events.html
12. Attribution monitoring: https://docs.aws.amazon.com/sagemaker/latest/dg/clarify-model-monitor-feature-attribution-drift.html
13. Independent corpus: https://github.com/ArielCyber/cloud_log_sampling
