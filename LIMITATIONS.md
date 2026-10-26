# Limitations

- The source corpus is real but has month-level `eventTime`; it does not support event-level causal
  sessions or exact chronological API sequences.
- The original corpus has no attack ground truth. Diagnosis and row-level detection metrics are
  therefore reported only for controlled perturbations.
- Controlled scenarios are semi-synthetic perturbations of real feature vectors, not organic attack
  campaigns or production incidents.
- The dataset has severe volume and identity concentration, including a very large 2019-08 window.
- Ordinal encoding of categorical event attributes is retained for compatibility with the legacy
  Isolation Forest baseline; it may impose artificial numeric geometry.
- SHAP values explain the detector's internal tree-path output, not the causal reason an API call is
  malicious.
- Protected adaptation uses high-confidence normal candidates and replay data; real deployments
  would require a stronger contamination-control and analyst-validation policy.
- Results from the primary corpus and controlled perturbations do not establish production security
  effectiveness. A separate labeled corpus now supports detector-only validation and a coarse
  reference/target temporal diagnosis checkpoint; the identical feature-only, SHAP-only, and
  dual-signal results at scenario-window level do not establish a dual-signal advantage. Full
  post-adaptation recovery validation on independent temporal windows remains outstanding.
- The richer raw export confirms day/hour resolution is available, but it is derived from the same
  underlying corpus and therefore does not count as an independent dataset.
- Detector and sample-size ablations show configuration sensitivity; no single detector or window
  size should be presented as universally optimal.
- The attribution-feature coupling extension is currently neutral relative to the simpler dual
  rule under the controlled scenarios. A source-tuned threshold transferred poorly, while a
  largest-gap label-free calibration succeeded on the small external checkpoint; broader
  multi-period validation is needed before claiming general transfer or production benefit.
- The unsupervised transfer calibration estimates a threshold from target-window scores. This is
  not attack-label leakage, but it can be unstable with few windows or contaminated target streams.
- The project does not deploy AWS resources or enforce IAM policies.
