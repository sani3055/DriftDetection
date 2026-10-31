# Exploratory candidate screening findings

## Research question and design

Can a stricter, historically calibrated normality filter reduce attack-labelled records in model updates without worsening future detection? We used the frozen Isolation Forest anomaly score and selected records at or below the earlier benign calibration score's 25th or 50th percentile, subject also to the existing predicted-normal screen. We then tested the existing historical guard both with and without the stricter screen. Neither candidate selection nor guard uses attack labels.

The fixed experiment covers five input representations and 30 candidate-pool conditions per representation. Each of 150 conditions uses the same selected pool and later test session as the earlier stress comparison. Source labels construct controlled pools and measure outcomes only. The date-separated feature matrices are inherited from the original labelled deployment: they are not a simulated live poisoning sequence. This protocol was written after the prior deployment had been analysed, so the result is exploratory, not prospective or externally preregistered.

## Main findings

- The 50th-percentile screen produced exactly the same selected candidates, update decisions and detection outcomes as the existing predicted-normal screen in all 150 conditions. It adds no measured benefit in this experiment.
- The 25th-percentile screen reduced selected candidates in three of five input representations and changed nothing in the other two. The smaller pool excluded benign as well as attack-labelled events. A 25th percentile measured on historical benign data does not promise 25 percent retention on shifted candidate data, particularly with score ties.
- In event-only ordinal inputs with 2,000 candidates and a nominal 20 percent attack fraction, the strict screen selected an average of 119 candidates, including 3.7 attack-labelled candidates, compared with 298.3 candidates and 13 attack-labelled candidates under the existing screen. The averages are across three seeds drawn from the same deployment. They are not independent incidents.
- Restricting to those three event-only ordinal conditions, the unguarded strict screen raised later recall by 0.008 on average but also raised benign false-positive rate by 0.023 relative to the ordinary screen; F1 fell by 0.004. These are descriptive paired differences, not estimates for a new environment.
- Over all 30 event-only one-hot conditions, the strict unguarded screen reduced mean recall by 0.1565 and mean F1 by 0.1144 relative to ordinary screening, while reducing mean false-positive rate by 0.0359. Thus, fewer attack-labelled candidates can coincide with substantially weaker later detection.
- Across the repeated controlled conditions, the stricter guarded variant accepted fewer total attack-labelled candidate occurrences (1,309 versus 1,556) but also accepted more candidate occurrences (22,115 versus 19,847) and more refits (84 versus 60). These are sums over overlapping, reused candidate pools, not distinct attacks. The ratio is not a prospective risk estimate, and counts alone cannot establish that one policy is safer.

The appropriate conclusion is that historical-score screening can sometimes reduce contamination, but it does not consistently improve downstream outcomes or prove safe adaptation. It is an ablation and failure analysis, not a deployable security guarantee or evidence of universal superiority. The updated filter has not yet been incorporated into the native chronological stream or independently labelled external validation.

## Evidence

- Pre-outcome amendment: `docs/JOURNAL_V5_SAFETY_PROTOCOL.md`.
- Per-condition and paired outputs: `results/journal_v5_safety_stress/` and `results/journal_v5_safety_analysis/`.
- Selection and runner: `src/experiments/candidate_safety.py` and `scripts/run_candidate_safety_stress.py`.
- Post-change automated suite: 99 passed in the recorded local run.

## Publication implications

These findings strengthen the paper's ablation and integrity, but they do not by themselves establish Q1/Q2 readiness. A stronger paper still needs a second independently labelled environment, a frozen prospective test, matched alternative detector families, operational cost analysis, and a more complete literature comparison. The paper should present failure modes honestly and only incorporate these results after the authors review the experimental design and values.
