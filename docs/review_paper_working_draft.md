Explainable Drift Monitoring for Adaptive Cybersecurity Detection

Systematic review manuscript in preparation

Sanidhya Bhandari

Department of IoT, School of Computer Science and Engineering, Vellore Institute of Technology, Vellore, India

Abstract

Security detectors face changing workloads, but a distribution shift does not by itself identify an attack or justify retraining. This review examines how recent journal research connects anomaly detection, feature attribution and adaptation, with cloud audit logs as the motivating application. The planned synthesis separates direct cloud-audit evidence from adjacent network, IoT and general log research and assesses temporal validity, label use and reproducibility. A metadata search conducted on 21 October 2026 produced 100 initial candidates. Directed primary-source follow-up and DOI verification on 29 October expanded the current register to 106 unique journal-article records with reported publication years from 2022 to 2026. 27 candidate records have readable PDF files available locally. These are acquisition counts, not the number of included studies. Full-text eligibility and study-level critical appraisal remain incomplete, so the review does not yet report a final PRISMA flow, an included-study synthesis or comparative performance conclusions. The proposed evidence framework distinguishes drift measurement, explanation change and demonstrated future recovery after adaptation. It provides a basis for assessing whether attribution-guided update claims survive time-respecting evaluation.

Keywords: systematic review; cloud audit logs; explainable artificial intelligence; concept drift; anomaly detection; adaptation; PRISMA

1 Introduction

Cloud audit logs record actions taken by users, services and automated workloads. A detector can flag unfamiliar activity when a workload changes, even when the activity is legitimate. Conversely, an attacker can use common administrative operations. These conditions make the interpretation of changing anomaly scores important for cloud monitoring.

The research problem extends beyond detecting input drift. A system must determine whether a change matters to its decisions, whether an explanation helps interpret the change, and whether updating improves subsequent predictions. These are distinct evidential questions. A study that explains an alert does not necessarily evaluate adaptation, and a study that lowers error on its update batch does not necessarily demonstrate future recovery.

The review will examine journal research from 2022 to 2026. It uses cloud audit monitoring as its focal application while retaining clearly identified adjacent security methods. This broader scope avoids implying that every retrieved article studies AWS CloudTrail. Direct and adjacent evidence will remain separate throughout extraction and synthesis.

2 Review questions

RQ1 asks which datasets, representations and label assumptions support cloud or adjacent security anomaly detection. RQ2 asks how studies measure input drift and changes in explanations. RQ3 asks whether those signals affect an adaptation policy and whether the study evaluates later, untouched data. RQ4 asks which evidence supports transfer, contamination control and operational reproducibility.

The intended contribution is a structured account of the evidence supporting an update decision. It will distinguish a change in model attribution from a verified security incident or a measured benefit of adaptation. The categories below are proposed extraction dimensions, not findings about all candidate papers.

3 Methods

The reporting framework follows PRISMA 2020 [1]. The supplied checklist governs the reporting items, including search sources and dates, selection, extraction, study appraisal, synthesis and access to materials. PRISMA does not prescribe a minimum of 100 studies. That number is the capstone requirement, and final inclusion must still follow relevance and quality checks. The protocol is not externally registered.

Eligibility covers journal articles first published from 1 January 2022 through 29 October 2026, with a verifiable DOI and a substantive connection to security detection and at least one of explanation, drift, adaptation or cloud/log analysis. Conference papers may support background discussion but will not count toward the required journal corpus. Retractions, nonresearch notices and unrelated applications are excluded after verification. Existing surveys will be distinguished from primary experimental studies rather than mixed as equivalent evidence.

The initial metadata discovery used OpenAlex with a Crossref fallback. The archived queries cover AWS CloudTrail, cloud audit anomaly detection, explainable intrusion detection, SHAP drift, concept drift and adaptive cybersecurity. A directed follow-up added six relevant journal records identified from primary publisher pages and the research bibliography. That follow-up is a separate discovery route and must appear separately in the eventual flow accounting.

The initial collector saved only its selected candidate set rather than a complete record-level export of every search hit. Consequently, the historical aggregate hit counts cannot be reconstructed into a fully audited exclusion flow from the current files. A database search update must archive all retrieved records and exact database-specific syntax before a final review is submitted. Scopus, Web of Science, IEEE Xplore and ACM searches have not been claimed as completed.

The DOI verification step queries Crossref and checks article type, bibliographic identity and first available publication date. It records publisher licence links and retrieves PDFs from exposed links when an explicit Creative Commons licence is present. Previously available files are checked separately. PDF parsing, page counts, hashes and a DOI search on the first two pages help check file identity, but parsing alone does not prove that the file is the correct final article, that it has been critically read, or that redistribution is permitted.

Screening will use title and abstract first, followed by full-text eligibility with one recorded reason for each exclusion. AI-assisted triage and data extraction must retain their evidence locations. No completed independent human screening round is claimed. PRISMA requires an accurate account of who screened and how automation was used. A second human check would reduce selection error, but an AI pass must not be described as an independent human reviewer. The author remains responsible for the final manuscript.

For each included paper, extraction will record the dataset and its provenance, input representation, label access, detector, explanation method, drift metric, calibration, adaptation strategy, baseline settings, evaluation chronology, metrics and uncertainty, external validation, code/data access and stated limitations. Missing values will remain not reported rather than being inferred. Claims about false positives or attack recall require the paper to define the corresponding denominator and ground truth.

4 Evidence framework

Dimension | Question asked of each study

Security target | Does the evaluation use true attack labels, anomaly labels, selected-row masks or no ground truth?

Time order | Are training, calibration and evaluation periods separated? Do updates precede the records used to evaluate them?

Explanation evidence | What model output does the explanation describe? Is reconstruction or stability checked?

Adaptation evidence | Does the method compare updates with a static and a simple update baseline under matched settings?

Transfer and access | Does the study test another account or dataset? Can code, data and calibration decisions be traced?

Temporal evidence will be coded descriptively as random/static evaluation, chronological evaluation, test-then-update evaluation with future recovery, or evaluation across independent environments. These are analysis categories, not a validated numerical quality scale. A chronological split can coexist with leakage if future labels influence threshold selection or if the update batch also supplies the recovery score.

The synthesis will group papers by direct cloud-audit monitoring, explainable security detection, drift/adaptation and general log methods. Results from different datasets will not be ranked by raw accuracy. A narrative synthesis is planned because label definitions, imbalance, model outputs and units of analysis are heterogeneous. No meta-analysis or pooled effect estimate has been performed.

Critical appraisal will consider dataset and label validity, chronological leakage, baseline comparability, test-informed tuning, same-batch recovery claims, independence of repeated trials and reproducibility. Each judgment needs a full-text location and an explanation. Citation count, a DOI or a journal name alone cannot establish methodological quality. Reporting-bias and certainty judgments remain pending rather than assumed favourable.

5 Acquisition results

The current register contains 106 unique DOI records from 85 journal titles. Crossref confirms their journal-article type and a reported publication year within 2022 to 2026. Publication-date bounds establish the search cutoff for 105 records. Incomplete dates retain their reported precision rather than an invented day. Abstract text is available from the verified metadata for 96 records. These checks support bibliographic tracing, not final study inclusion or journal-quality certification.

Publication year | Verified candidate records

2022 | 4

2023 | 13

2024 | 28

2025 | 39

2026 | 22

Acquisition measure | Current count

Candidate DOI records | 106

Readable PDFs available | 27

PDFs with DOI found on first two pages | 23

Full text reviews completed by the retrieval script | 0

Final included studies | 0

The initial automated relevance audit found only 18 direct cloud/audit signals among the original 100 candidates. That is a keyword-based triage result, not a completed screening decision. Some remaining records concern adjacent network or IoT security, and some may ultimately be excluded. Expanding the register rather than forcing all 100 into the synthesis protects the distinction between a collection target and scientific eligibility.

The candidate register in Appendix A preserves bibliographic identity and full-text availability. It is not the final consolidated summary of 100 fully reviewed papers requested by the guide. That deliverable requires full-text methods, findings and limitations for each included study. NotebookLM and SciSpace use has not been performed or claimed in this preparation step.

6 Research positioning

The experimental manuscript provides a concrete example of why temporal evidence matters. Its legacy controlled benchmark reports fewer false alarms after some updates, but uses the current adaptation batch for scoring. A separately versioned native-time protocol instead scores before updating and exposes a recall versus false-alarm trade-off. This example motivates the review framework. It is the author's own experiment, not a finding extracted from the candidate literature.

The intended synthesis will ask whether explanation changes provide information beyond input drift, whether an update gate can distinguish routine changes from security-relevant shifts, and whether that distinction remains useful under transfer. It will also examine the risk of using predicted-normal records during retraining. A model can assign a normal prediction to an attack, so filtering by its own predictions cannot guarantee clean adaptation.

7 Limitations and completion requirements

The present draft has an incomplete full-text collection and no completed included-study appraisal. The original retrieval selected a fixed number of metadata hits and omitted relevant core papers that later citation follow-up recovered. These limitations preclude a claim of exhaustive coverage. Current date and language eligibility, venue legitimacy and PDF-to-article matching still require review at the study level.

Before submission, the review needs a complete search update, recorded screening and exclusion decisions, at least the required number of eligible journal papers, complete extraction, appraisal and a synthesis linked to those included papers. The final PRISMA flow must use actual records at each stage. The checklist location column must refer to real manuscript sections or final page numbers. These counts and locations must not be fabricated to satisfy a deadline.

8 Conclusion

An attribution-guided update claim requires evidence about both model behaviour and subsequent detection quality. The proposed review separates these claims and organises them by data, label access, chronology and transfer. Bibliographic verification and lawful retrieval have advanced the evidence collection, but the final systematic synthesis remains unfinished. No claim about the comparative effectiveness of all candidate methods follows from metadata alone.

Declarations

The review protocol is unregistered. Generative AI assisted metadata auditing, candidate organisation and drafting. No independent reviewer agreement statistics or completed risk-of-bias ratings are reported. Funding and competing-interest declarations require author confirmation. The project number remains unspecified. Code and evidence paths are recorded in the local research package; no new public release or journal submission is claimed.

References

[1] Page MJ, McKenzie JE, Bossuyt PM, et al. The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. BMJ. 2021;372:n71. https://doi.org/10.1136/bmj.n71. This methodological reference is outside the 2022 to 2026 candidate count.

Candidate article references appear in Appendix A. Their presence in the register does not indicate final inclusion.

Appendix A Candidate journal article register

Records P001 to P100 preserve the original candidate identifiers. CORE records are directed follow-up additions. Availability indicates a readable PDF, not completed full-text review. All records await final eligibility and critical appraisal.

CORE01  Shruti Arora, Rinkle Rani, Nitin Saxena. A systematic review on detection and adaptation of concept drift in streaming data using machine learning techniques. WIREs Data Mining and Knowledge Discovery. 2024-03-19. https://doi.org/10.1002/widm.1536

Full text not retrieved. Abstract metadata: available.

CORE02  Aditya Kuppa, Nhien-An Le-Khac. Learn to adapt: Robust drift detection in security domain. Computers and Electrical Engineering. 2022-09. https://doi.org/10.1016/j.compeleceng.2022.108239

Full text not retrieved. Abstract metadata: not available.

CORE03  Yongsoo Lee, Yeeun Lee, Eungyu Lee et al.. Explainable Artificial Intelligence-Based Model Drift Detection Applicable to Unsupervised Environments. Computers, Materials & Continua. 2023. https://doi.org/10.32604/cmc.2023.040235

Full text not retrieved. Abstract metadata: not available.

CORE04  Jinpeng Li, Hang Yu, Zhenyu Zhang et al.. Concept Drift Adaptation by Exploiting Drift Type. ACM Transactions on Knowledge Discovery from Data. 2024-02-12. https://doi.org/10.1145/3638777

Full text not retrieved. Abstract metadata: available.

CORE05  Elijah M. Maseno, Yanxia Sun, Zenghui Wang. Detecting adversarial evasion in deep learning intrusion detection systems using explainable AI. International Journal of Information Security. 2026-07-15. https://doi.org/10.1007/s10207-026-01299-x

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

CORE06  Antonio Lara-Gutierrez, Carmen Fernandez-Gago, Jose A. Onieva. A Framework for Drift Detection and Adaptation in AI-driven Anomaly and Threat Detection Systems. International Journal of Information Security. 2025-09-02. https://doi.org/10.1007/s10207-025-01118-9

Full text not retrieved. Abstract metadata: not available.

P001  Basharat Ali. On the fog’s frontline: a federated machine learning approach for industrial network threat detection and intrusion prevention. Journal of Cybersecurity. 2025. https://doi.org/10.1093/cybsec/tyaf041

Full text not retrieved. Abstract metadata: available.

P002  Purushottam Perapu. Anomaly Detection in User Behaviour Using Machine Learning For Cloud Platforms. International Journal of Scientific Research in Computer Science, Engineering and Information Technology. 2025-05-26. https://doi.org/10.32628/cseit25113343

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P003  Jitender Sharma, Sonia, Karan Kumar et al.. Enhancing Intrusion Detection Systems with Adaptive Neuro-Fuzzy Inference Systems. Mesopotamian Journal of CyberSecurity. 2025-01-10. https://doi.org/10.58496/mjcs/2025/001

Full text not retrieved. Abstract metadata: available.

P004  Aziz Abibulaiev, Petro Pukach, Myroslava Vovk. Context-Aware ML/NLP Pipeline for Real-Time Anomaly Detection and Risk Assessment in Cloud API Traffic. Machine Learning and Knowledge Extraction. 2026-01-22. https://doi.org/10.3390/make8010025

Full text not retrieved. Abstract metadata: available.

P005  Dhruvitkumar V Talati. Enhancing Multi-Cloud Security with Quantum-Resilient AI for Anomaly Detection. World Journal of Advanced Research and Reviews. 2022-03-30. https://doi.org/10.30574/wjarr.2022.13.3.0250

Full text not retrieved. Abstract metadata: available.

P006  Brian Lewandowski, Randy Paffenroth. Autoencoder Feature Residuals for Network Intrusion Detection: One-Class Pretraining for Improved Performance. Machine Learning and Knowledge Extraction. 2023-07-31. https://doi.org/10.3390/make5030046

Full text not retrieved. Abstract metadata: available.

P007  Mohamed Sasi, Oluwatayomi Rereloluwa Adegboye, Ahmad Alzubi. Explainable and Optimized Random Forest for Anomaly Detection in IoT Networks Using the RIME Metaheuristic. Electronics. 2025-11-16. https://doi.org/10.3390/electronics14224465

Full text not retrieved. Abstract metadata: available.

P008  Mohammed Aly, Naif M. Alotaibi. SHAP enhanced transformer GWO boosting model for transparent and robust anomaly detection in IIoT environments. Scientific Reports. 2025-11-20. https://doi.org/10.1038/s41598-025-25033-0

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P009  Sreeja Reddy Challa. Cloud Automation in Financial Services: Securing and Scaling Banking Infrastructure in AWS. European Modern Studies Journal. 2025-09-11. https://doi.org/10.59573/emsj.9(5).2025.22

Full text not retrieved. Abstract metadata: available.

P010  Nidhi Srivastav, Rajiv Singh. A Novel Lightweight Explainable Multilayer Adaptive RNN-Based Intrusion Detection Framework. International Journal of Advanced Computer Science and Applications. 2026. https://doi.org/10.14569/ijacsa.2026.0170222

Full text not retrieved. Abstract metadata: available.

P011  Saurav Kumar Ray, Ritviz Tiwari, Piyush Sharma et al.. AI & MACHINE LEARNING IN CYBERSECURITY. Towards Excellence. 2025-12-31. https://doi.org/10.37867/te170452

Full text not retrieved. Abstract metadata: available.

P012  Sri Ramya Deevi. AI-Based Anomaly Detection in Multi-Cloud Traffic Using Deep Learning Models. Journal of Artificial Intelligence & Cloud Computing. 2024-06-20. https://doi.org/10.47363/jaicc/2024(3)485

Full text not retrieved. Abstract metadata: available.

P013  Pavlo Pidhornyy. ANOMALY DETECTION IN ENCRYPTED NETWORK TRAFFIC USING DEEP LEARNING. Cybersecurity Education Science Technique. 2025-09-26. https://doi.org/10.28925/2663-4023.2025.29.897

Full text not retrieved. Abstract metadata: available.

P014  Danang. An Adaptive Cybersecurity Framework Integrating Machine Learning, Zero Trust Policy, and Blockchain for Academic Cloud Environments. Journal of Intelligent Decision Making and Information Science. 2026-07-31. https://doi.org/10.59543/jidmis.v3.1070

Readable PDF. Abstract metadata: available. DOI on opening pages: not found.

P015  Chanaka Lasantha, Maduranga, Abesekara et al.. An Unsupervised Machine Learning Approach for Dynamic Anomaly Detection and Risk Defense in Cloud Servers. International Journal of Research in Computing. 2026-01-14. https://doi.org/10.64701/ijrc/345/9116

Full text not retrieved. Abstract metadata: available.

P016  Oraye Godspower. Beyond Black Boxes: Permutation Feature Importance for  Explainable Intrusion Detection and Model Optimization. International Journal of Computer Science and Mathematical Theory. 2026-09-22. https://doi.org/10.56201/ijcsmt.vol.12.no8.2026.pg65.77

Full text not retrieved. Abstract metadata: available.

P017  Büşra Günay, Mehmet Yavuz Yağcı. DEA-IDS: Drift-Aware Feature Selection and Few-Shot Adaptation for Cross-Domain IoT–IoMT Intrusion Detection. Sensors. 2026-09-30. https://doi.org/10.3390/s26196200

Full text not retrieved. Abstract metadata: available.

P018  Gowtham Reddy Kunduru. DEEP LEARNING–ENABLED DATA SECURITY AND INTRUSION DETECTION IN AZURE AND AWS CLOUD SYSTEMS. International Journal of Engineering Research and Science & Technology. 2024-08-12. https://doi.org/10.62643/ijerst.2024.v20.n3.pp428-440

Readable PDF. Abstract metadata: available. DOI on opening pages: not found.

P019  A. Sangeetha, J. James Alaguraja, Rohaya Latip. E-HUNF: Explainable Hybrid Unsupervised Network Forensics for robust cybercrime anomaly detection. International Journal of Electronics and Telecommunications. 2026-06-02. https://doi.org/10.24425/ijet.2026.157911

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P020  Shiva Reddy Kashireddy. Enhancement of Cybersecurity in Information Technology Using AI-Powered Working Intrusion Detection Working Systems. International Journal For Multidisciplinary Research. 2026-01-07. https://doi.org/10.36948/ijfmr.2026.v08i01.63042

Full text not retrieved. Abstract metadata: available.

P021  Muhammad Nuraddeen Ado, Jabir Isah Karofi, Hamisu Mukhtar. Evolving Machine Learning Models for Anomaly Detection: An Integrative Review on Evolving Machine Learning Models for Anomaly Detection of Cross-Domain Approaches. International Journal of Research and Innovation in Applied Science. 2026. https://doi.org/10.51584/ijrias.2026.110400056

Full text not retrieved. Abstract metadata: available.

P022  Dr. Mohamed Adel Al-Shaher. Explainable Lightweight Deep Learning for Secure Edge Anomaly Detection. Journal of Internet Services and Information Security. 2026-05-29. https://doi.org/10.58346/jisis.2026.i2.012

Full text not retrieved. Abstract metadata: available.

P023  Zachary T Caldwell, Chloe A Morrison, Lucas J Fischer. Fraud Detection Under Concept Drift: Adaptive and Explainable Machine Learning for Financial Cybersecurity. International Journal of Management and Organizational Research. 2024. https://doi.org/10.54660/ijmor.2024.3.6.249-260

Full text not retrieved. Abstract metadata: available.

P024  Ishwar Bansal. Implementing Adaptive Security Monitoring: Aws Cloudwatch and Advanced Threat Detection Techniques. International Journal of Computational and Experimental Science and Engineering. 2025-07-15. https://doi.org/10.22399/ijcesen.3482

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P025  Alycia Sebastian, S. Silvia Priscila, B. M. Praveen. Interpretable and Adaptive Intrusion Detection Using SHAP-Enhanced Ensemble Learning and Feature Attribution for Next-Generation Cybersecurity. FMDB Transactions on Sustainable Computer Letters. 2026-08-09. https://doi.org/10.69888/ftscl.2026.000748

Full text not retrieved. Abstract metadata: available.

P026  Jouma Ali Al-Mohamad. Strengthening Cybersecurity through Intelligent Machine Learning Architectures: A Multi-Layer Adaptive Defense Framework Integrating Explainability and Privacy-Preserving Mechanisms. Science, Education and Innovations in the context of modern problems. 2026-05-01. https://doi.org/10.56334/sei/9.6.13

Full text not retrieved. Abstract metadata: available.

P027  Alycia Sebastian, B. M. Praveen, S. Silvia Priscila. X-Guard: Advancing Intrusion Detection with Explainable AI for Transparent Cybersecurity Decision-Making. AVE Trends in Intelligent Computing Systems. 2026-01-03. https://doi.org/10.64091/atics.2026.000285

Full text not retrieved. Abstract metadata: available.

P028  Omar Abdel Wahab. Intrusion Detection in the IoT Under Data and Concept Drifts: Online Deep Learning Approach. IEEE Internet of Things Journal. 2022-10-15. https://doi.org/10.1109/jiot.2022.3167005

Full text not retrieved. Abstract metadata: not available.

P029  Maryam Mahsal Khan, Mohammed Alkhathami. Anomaly detection in IoT-based healthcare: machine learning for enhanced security. Scientific Reports. 2024-03-11. https://doi.org/10.1038/s41598-024-56126-x

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P030  Vincent Zibi Mohale, Ibidun Christiana Obagbuwa. A systematic review on the integration of explainable artificial intelligence in intrusion detection systems to enhancing transparency and interpretability in cybersecurity. Frontiers in Artificial Intelligence. 2025-01-28. https://doi.org/10.3389/frai.2025.1526221

Full text not retrieved. Abstract metadata: available.

P031  Methaq A. Shyaa, Noor Farizah Ibrahim, Zurinahni Zainol et al.. Evolving cybersecurity frontiers: A comprehensive survey on concept drift and feature dynamics aware machine and deep learning in intrusion detection systems. Engineering Applications of Artificial Intelligence. 2024-11. https://doi.org/10.1016/j.engappai.2024.109143

Full text not retrieved. Abstract metadata: not available.

P032  Fabian Hinder, Valerie Vaquet, Barbara Hammer. One or two things we know about concept drift—a survey on monitoring in evolving environments. Part A: detecting concept drift. Frontiers in Artificial Intelligence. 2024-06-19. https://doi.org/10.3389/frai.2024.1330257

Full text not retrieved. Abstract metadata: available.

P033  Dheyaaldin Alsalman. A Comparative Study of Anomaly Detection Techniques for IoT Security Using Adaptive Machine Learning for IoT Threats. IEEE Access. 2024. https://doi.org/10.1109/access.2024.3359033

Full text not retrieved. Abstract metadata: not available.

P034  Adel Alabbadi, Fuad Bajaber. An Intrusion Detection System over the IoT Data Streams Using eXplainable Artificial Intelligence (XAI). Sensors. 2025-01-30. https://doi.org/10.3390/s25030847

Full text not retrieved. Abstract metadata: available.

P035  Mohammed M. Alani, Ali Miri. Towards an Explainable Universal Feature Set for IoT Intrusion Detection. Sensors. 2022-07-29. https://doi.org/10.3390/s22155690

Full text not retrieved. Abstract metadata: available.

P036  Mahdi Soltani, Khashayar Khajavi, Mahdi Jafari Siavoshani et al.. A multi-agent adaptive deep learning framework for online intrusion detection. Cybersecurity. 2024-05-01. https://doi.org/10.1186/s42400-023-00199-0

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P037  Abdullah Alabdulatif. A Novel Ensemble of Deep Learning Approach for Cybersecurity Intrusion Detection with Explainable Artificial Intelligence. Applied Sciences. 2025-07-17. https://doi.org/10.3390/app15147984

Full text not retrieved. Abstract metadata: available.

P038  Methaq A. Shyaa, Zurinahni Zainol, Rosni Abdullah et al.. Enhanced Intrusion Detection with Data Stream Classification and Concept Drift Guided by the Incremental Learning Genetic Programming Combiner. Sensors. 2023-04-04. https://doi.org/10.3390/s23073736

Full text not retrieved. Abstract metadata: available.

P039  Yang Liu, Shaochen Ren, Xuran Wang et al.. Temporal Logical Attention Network for Log-Based Anomaly Detection in Distributed Systems. Sensors. 2024-12-12. https://doi.org/10.3390/s24247949

Full text not retrieved. Abstract metadata: available.

P040  Taiwo Blessing Ogunseyi, Gogulakrishan Thiyagarajan. An Explainable LSTM-Based Intrusion Detection System Optimized by Firefly Algorithm for IoT Networks. Sensors. 2025-04-04. https://doi.org/10.3390/s25072288

Full text not retrieved. Abstract metadata: available.

P041  Yilixiati Abudurexiti, Guangjie Han, Fan Zhang et al.. An explainable unsupervised anomaly detection framework for Industrial Internet of Things. Computers & Security. 2025-01. https://doi.org/10.1016/j.cose.2024.104130

Full text not retrieved. Abstract metadata: not available.

P042  Fatemeh Ebrahimi, Reza Javidan, Reza Akbari et al.. Intrusion detection in the internet of things using convolutional neural networks: an explainable AI approach. Cybersecurity. 2025-09-05. https://doi.org/10.1186/s42400-025-00369-2

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P043  Qixuan Li, Yangjian Ji, Mingrui Zhu et al.. Unsupervised feature selection using chronological fitting with Shapley Additive explanation (SHAP) for industrial time-series anomaly detection. Applied Soft Computing. 2024-04. https://doi.org/10.1016/j.asoc.2024.111426

Full text not retrieved. Abstract metadata: not available.

P044  Renat Kermenov, Giacomo Nabissi, Sauro Longhi et al.. Anomaly Detection and Concept Drift Adaptation for Dynamic Systems: A General Method with Practical Implementation Using an Industrial Collaborative Robot. Sensors. 2023-03-20. https://doi.org/10.3390/s23063260

Full text not retrieved. Abstract metadata: available.

P045  Xuejiao Chen, Minyao Liu, Zixuan Wang et al.. Explainable Deep Learning-Based Feature Selection and Intrusion Detection Method on the Internet of Things. Sensors. 2024-08-12. https://doi.org/10.3390/s24165223

Full text not retrieved. Abstract metadata: available.

P046  Balajee R M, Jayanthi Kannan M K. Intrusion Detection on AWS Cloud through Hybrid Deep Learning Algorithm. Electronics. 2023-03-16. https://doi.org/10.3390/electronics12061423

Full text not retrieved. Abstract metadata: available.

P047  Maiada M. Mahmoud, Yasser Omar Youssef, Ayman A. Abdel-Hamid. XI2S-IDS: An Explainable Intelligent 2-Stage Intrusion Detection System. Future Internet. 2025-01-08. https://doi.org/10.3390/fi17010025

Full text not retrieved. Abstract metadata: available.

P048  Chukwuemeka Nwachukwu, Kehinde Durodola-Tunde, Chukwuebuka Akwiwu-Uzoma. AI-driven anomaly detection in cloud computing environments. International Journal of Science and Research Archive. 2024-11-30. https://doi.org/10.30574/ijsra.2024.13.2.2184

Full text not retrieved. Abstract metadata: available.

P049  Jiayi Liu, Donghua Yang, Kaiqi Zhang et al.. Anomaly and change point detection for time series with concept drift. World Wide Web. 2023-07-07. https://doi.org/10.1007/s11280-023-01181-z

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P050  Fabian Hinder, Valerie Vaquet, Barbara Hammer. One or two things we know about concept drift—a survey on monitoring in evolving environments. Part B: locating and explaining concept drift. Frontiers in Artificial Intelligence. 2024-07-19. https://doi.org/10.3389/frai.2024.1330258

Full text not retrieved. Abstract metadata: available.

P051  Sugandh Seth, Kuljit Kaur Chahal, Gurvinder Singh. Concept Drift–Based Intrusion Detection For Evolving Data Stream Classification In IDS: Approaches And Comparative Study. The Computer Journal. 2024-03-03. https://doi.org/10.1093/comjnl/bxae023

Full text not retrieved. Abstract metadata: available.

P052  Seshu Bhavani Mallampati, Hari Seetha. Enhancing Intrusion Detection with Explainable AI: A Transparent Approach to Network Security. Cybernetics and Information Technologies. 2024-03-01. https://doi.org/10.2478/cait-2024-0006

Full text not retrieved. Abstract metadata: available.

P053  Paolo Mignone, Roberto Corizzo, Michelangelo Ceci. Distributed and explainable GHSOM for anomaly detection in sensor networks. Machine Learning. 2024-01-22. https://doi.org/10.1007/s10994-023-06501-y

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P054  Min Li, Mengjie Sun, Gang Li et al.. MDFULog: Multi-Feature Deep Fusion of Unstable Log Anomaly Detection Model. Applied Sciences. 2023-02-09. https://doi.org/10.3390/app13042237

Full text not retrieved. Abstract metadata: available.

P055  Chiheb Eddine Ben Ncir, Mohamed Aymen Ben HajKacem, Mohammed Alattas. Enhancing intrusion detection performance using explainable ensemble deep learning. PeerJ Computer Science. 2024-09-13. https://doi.org/10.7717/peerj-cs.2289

Full text not retrieved. Abstract metadata: available.

P056  Lerina Aversano, Mario Luca Bernardi, Marta Cimitile et al.. Explainable Anomaly Detection of Synthetic Medical IoT Traffic Using Machine Learning. SN Computer Science. 2024-04-24. https://doi.org/10.1007/s42979-024-02830-4

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P057  Renjie Chu, Peiyuan Jin, Hanli Qiao et al.. Intrusion detection in the IoT data streams using concept drift localization. AIMS Mathematics. 2023. https://doi.org/10.3934/math.2024076

Full text not retrieved. Abstract metadata: available.

P058  Wiktor Sus, Piotr Nawrocki. Signature-based Adaptive Cloud Resource Usage Prediction Using Machine Learning and Anomaly Detection. Journal of Grid Computing. 2024-04-23. https://doi.org/10.1007/s10723-024-09764-4

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P059  Pamela Hermosilla, Mauricio Díaz, Sebastián Berríos et al.. Use of Explainable Artificial Intelligence for Analyzing and Explaining Intrusion Detection Systems. Computers. 2025-04-25. https://doi.org/10.3390/computers14050160

Full text not retrieved. Abstract metadata: available.

P060  Sagar Pande, Aditya Khamparia. EXPLAINABLE DEEP NEURAL NETWORK BASED ANALYSIS ON INTRUSION DETECTION SYSTEMS. Computer Science. 2023-03-06. https://doi.org/10.7494/csci.2023.24.1.4551

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P061  Usama Tahir, Muhammad Kamran Abid, Muhammad Fuzail et al.. Enhancing IoT Security through Machine Learning-Driven Anomaly Detection. VFAST Transactions on Software Engineering. 2024-05-16. https://doi.org/10.21015/vtse.v12i1.1766

Full text not retrieved. Abstract metadata: available.

P062  Danlei Li, Nirmal-Kumar C. Nair, Kevin I-Kai Wang. ADDAEIL: Anomaly Detection with Drift-Aware Ensemble-Based Incremental Learning. Algorithms. 2025-06-11. https://doi.org/10.3390/a18060359

Full text not retrieved. Abstract metadata: available.

P063  Borja Aizpurua, Samuel Palmer, Román Orús. Tensor networks for explainable machine learning in cybersecurity. Neurocomputing. 2025-07. https://doi.org/10.1016/j.neucom.2025.130211

Full text not retrieved. Abstract metadata: not available.

P064  Vasudeva Pai, Karthik Pai, Manjunatha S. et al.. Adaptive network anomaly detection using machine learning approaches. EURASIP Journal on Information Security. 2025-10-21. https://doi.org/10.1186/s13635-025-00216-4

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P065  Heinrihs Kristians Skrodelis, Andrejs Romanovs. Explainable hybrid intrusion detection for SCADA/ICS: a review and research agenda. Frontiers in Computer Science. 2026-03-03. https://doi.org/10.3389/fcomp.2026.1724245

Full text not retrieved. Abstract metadata: available.

P066  Yuna Han, Hangbae Chang. XA-GANomaly: An Explainable Adaptive Semi-Supervised Learning Method for Intrusion Detection Using GANomaly. Computers, Materials & Continua. 2023. https://doi.org/10.32604/cmc.2023.039463

Full text not retrieved. Abstract metadata: not available.

P067  Mohammad Zubair Khan, Abdulhakim Sabur, Hamza Ghandorh. A Novel Internet of Medical Things Hybrid Model for Cybersecurity Anomaly Detection. Sensors. 2025-10-21. https://doi.org/10.3390/s25206501

Full text not retrieved. Abstract metadata: available.

P068  Vinura Galwaduge, Jagath Samarabandu. Novel Actionable Counterfactual Explanations for Intrusion Detection Using Diffusion Models. Journal of Cybersecurity and Privacy. 2025-09-05. https://doi.org/10.3390/jcp5030068

Full text not retrieved. Abstract metadata: available.

P069  Usman Ahmed, Muhammad Tariq Sadiq. Enhancing SDN Intrusion Detection via Multi-Hybrid Deep Learning Fusion and Explainable AI. Mathematics. 2026-04-29. https://doi.org/10.3390/math14091498

Full text not retrieved. Abstract metadata: available.

P070  Bhagyashree D Shendkar. Explainable Machine Learning Models for Real-Time Threat Detection in Cybersecurity. Panamerican Mathematical Journal. 2024-11-13. https://doi.org/10.52783/pmj.v35.i1s.2313

Full text not retrieved. Abstract metadata: available.

P071  Adam Grabowski, Shengjie Xu. Advancing Cybersecurity Practice: Explainable Machine Learning for Network Intrusion Detection. Journal of Cybersecurity Education, Research and Practice. 2025-12-15. https://doi.org/10.62915/2472-2707.1247

Full text not retrieved. Abstract metadata: available.

P072  Oumaima Chentoufi, Mouad Choukhairi, Khalid Chougdali. An Enhanced Machine Learning Framework for Network Anomaly Detection. AI. 2025-11-20. https://doi.org/10.3390/ai6110299

Full text not retrieved. Abstract metadata: available.

P073  Tianrui Bai, Yuan Liu, Yiwen Gao et al.. Ats-dta: adaptive two-stage DDoS detection with dynamic threshold adjustment in SDN networks. Cybersecurity. 2026-01-13. https://doi.org/10.1186/s42400-025-00414-0

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P074  Tarek Ali, Panos Kostakos, Saeid Sheikhi. HuntGPT: Integrating Machine Learning-Based Anomaly Detection and Explainable AI with Large Language Models (LLMs). Telecom. 2026-06-08. https://doi.org/10.3390/telecom7030073

Full text not retrieved. Abstract metadata: available.

P075  Juha Mylläri, Tatu Aalto, Jukka K. Nurminen. Ladle: a method for unsupervised anomaly detection across log types. Automated Software Engineering. 2025-03-24. https://doi.org/10.1007/s10515-025-00504-w

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P076  Nisher Ahmed, Md Emran Hossain, Zakir Hossain et al.. Machine Learning-Driven Adaptive Authentication: Strengthening Cybersecurity against High-Volume Data Breaches. Formosa Journal of Multidisciplinary Research. 2025-02-27. https://doi.org/10.55927/fjmr.v4i2.49

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P077  Han-Mei Liu. AI-Enabled Adaptive Cybersecurity Response Using Reinforcement Learning. Frontiers in Artificial Intelligence Research. 2025-03-13. https://doi.org/10.71465/gwa30h81

Full text not retrieved. Abstract metadata: available.

P078  Clifton Reddy, Saravanan Prabhagaran, Adarsh Vaid. Adaptive Anomaly Detection in Database Transactions: Bridging Security Gaps with Reinforcement Learning. European Journal of Artificial Intelligence and Machine Learning. 2025-04-14. https://doi.org/10.24018/ejai.2025.4.2.53

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P079  Muhammad Furqan Khan. Explainable Ai and Machine Learning Models for Transparent and Scalable Intrusion Detection Systems. Journal of Information Systems Engineering and Management. 2024-12-30. https://doi.org/10.52783/jisem.v9i4s.12115

Full text not retrieved. Abstract metadata: available.

P080  Venkatasubramanian Ganapathy. Quantum Machine Learning for Anomaly Detection in Cyber Security Audits. Shodh Sari-An International Multidisciplinary Journal. 2025-01-01. https://doi.org/10.59231/sari7784

Full text not retrieved. Abstract metadata: available.

P081  M. Z. Naser, Ahmad Z. Naser. SPINEX-anomaly: similarity-based predictions with explainable neighbors exploration for anomaly and outlier detection. Journal of Big Data. 2025-04-01. https://doi.org/10.1186/s40537-025-01122-9

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P082  M. V. Carriegos, N. DeCastro-García, D. Escudero. Towards Supercomputing Categorizing the Maliciousness upon Cybersecurity Blacklists with Concept Drift. Computational and Mathematical Methods. 2023-05-20. https://doi.org/10.1155/2023/5780357

Full text not retrieved. Abstract metadata: available.

P083  Taha M.O. Alakhras. A SURVEY OF INTRUSION DETECTION SYSTEMS IN IOT: MACHINE LEARNING AND FEATURE SELECTION APPROACHES. International Journal of Applied Mathematics. 2025-11-03. https://doi.org/10.12732/ijam.v38i10s.1003

Full text not retrieved. Abstract metadata: available.

P084  Shiqi Li. A Tiny Machine Learning for Real‐Time Anomaly Detection of Self‐Media Public Opinion in Edge‐Cloud‐Cooperation Campus Networks. Internet Technology Letters. 2025-05-28. https://doi.org/10.1002/itl2.70038

Full text not retrieved. Abstract metadata: available.

P085  Nughroho Adhi Santoso, Rezi Lutfayza, Bangkit Indarmawan Nughroho et al.. Anomaly detection in network security systems using machine learning. Journal of Intelligent Decision Support System (IDSS). 2024-06-30. https://doi.org/10.35335/idss.v7i2.238

Readable PDF. Abstract metadata: available. DOI on opening pages: not found.

P086  Andrea Pinto, Yezid Donoso, Jairo A. Gutierrez. Balancing the trilemma: a survey of federated anomaly detection for secure cyber-physical systems. Cybersecurity. 2026-03-12. https://doi.org/10.1186/s42400-026-00567-6

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P087  Yu Wang, Guohua Liu. Cross-Scenario Subdomain Adaptive Displacement Anomaly Detection in Dams. Sensors. 2025-05-09. https://doi.org/10.3390/s25102984

Full text not retrieved. Abstract metadata: available.

P088  Ramya V. J.. Data-Driven Framework for Cloud Storage Security Optimization: Leveraging Predictive Analytics and Machine Learning to Enhance Threat Detection and Incident Response. Journal of Electrical Systems. 2024-07-10. https://doi.org/10.52783/jes.6721

Readable PDF. Abstract metadata: available. DOI on opening pages: not found.

P089  Thangatharani T, M. Subalakshmi. Development of an adaptive machine learning framework for real-time anomaly detection in cybersecurity. The Scientific Temper. 2025-08-30. https://doi.org/10.58414/scientifictemper.2025.16.8.07

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P090  Ann Ogechi Felix. Enhancing Digital Forensics Investigations Using AI Driven Anomaly Detection and Log Correlation: A Mixed Methods Approach. International Journal of Future Engineering Innovations. 2025. https://doi.org/10.54660/ijfei.2025.2.4.71-84

Full text not retrieved. Abstract metadata: available.

P091  Mayank Namdev, Jayasundar S., Muhammad Babur, Deepak A. Vidhate, Santosh Yerasuri. Enhancing Security in Cloud Computing with Anomaly Detection Using Machine Learning. Tuijin Jishu/Journal of Propulsion Technology. 2023-09-11. https://doi.org/10.52783/tjjpt.v44.i3.622

Full text not retrieved. Abstract metadata: available.

P092  Naresh Kalimuthu. Explainable AI (XAI) for Enhanced Cyber Threat Intelligence: Building Interpretable Intrusion Detection Systems. International Journal on Science and Technology. 2025-10-22. https://doi.org/10.71097/ijsat.v16.i4.9535

Full text not retrieved. Abstract metadata: available.

P093  Jamiu Olamilekan Akande, Olaitan Miriam Olufisayo Raji, Olufunbi Babalola et al.. Explainable AI for Cybersecurity: Interpretable Intrusion Detection in Encrypted Traffic. Journal of Frontiers in Multidisciplinary Research. 2023. https://doi.org/10.54660/.jfmr.2023.4.2.213-222

Full text not retrieved. Abstract metadata: available.

P094  Zhong Li, Jiayang Shi, Matthijs van Leeuwen. Graph neural networks based log anomaly detection and explanation. Data Mining and Knowledge Discovery. 2026-07-03. https://doi.org/10.1007/s10618-026-01235-6

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P095  Huy Minh Dinh, Wei Zong, Yang-Wai Chow. Investigating Oversampling Techniques to Mitigate Class Imbalance in Network Intrusion Detection Datasets. Pragmatic Cybersecurity. 2026-01-27. https://doi.org/10.53941/pc.2026.100004

Readable PDF. Abstract metadata: available. DOI on opening pages: yes.

P096  Kynatun Mahin, Saba Ashfaq. Machine Learning Enhanced Intrusion Detection and Anomaly Classification for MIS-Driven Enterprise Network Security. International Journal of Scientific Interdisciplinary Research. 2024-09-01. https://doi.org/10.63125/xk6kpc72

Full text not retrieved. Abstract metadata: available.

P097  Yazed Alsaawy. Machine Learning Pipeline: Feature Selection and Adaptive Training for DDoS Detection to Improve Cloud Security. Islamic University Journal of Applied Sciences. 2024-10-25. https://doi.org/10.63070/jesc.2024.023

Full text not retrieved. Abstract metadata: available.

P098  Taras Melko, Volodymyr Kotsun. THEORETICAL AND TECHNICAL ASPECTS OF MACHINE LEARNING USAGE IN CYBERSECURITY. Cybersecurity Education Science Technique. 2025-06-26. https://doi.org/10.28925/2663-4023.2025.28.774

Full text not retrieved. Abstract metadata: available.

P099  James Onyilo, Victoria Chibuzo Uzuegbu. Explainable AI Intrusion Detection System: Improving Transparency and Trust in Cybersecurity. Nature Journal of Emerging Sciences Technologies and Innovations. 2025-09-30. https://doi.org/10.65752/e5fa2b27

Full text not retrieved. Abstract metadata: available.

P100  Minji Kim, Gwangho Yun, Hwasup Jang et al.. A Machine Learning Operations Framework for Self-Adaptive Anomaly Detection in Autonomous Surface Ships Under Data Drift. Journal of Marine Science and Engineering. 2026-06-23. https://doi.org/10.3390/jmse14131152

Full text not retrieved. Abstract metadata: available.
