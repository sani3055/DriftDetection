# Cost-sensitive adaptation analysis

`data/robustness/cost_sensitivity_results.csv` evaluates the already-computed held-out policy
results under a grid of hypothetical operational costs. The loss is:

```text
miss_cost * (1 - recall) on security scenarios
+ false_alarm_cost * false_positive_rate on benign scenarios
+ unnecessary_adaptation_cost * unnecessary_adaptation
```

Lower mean loss is preferred. The grid varies missed-security cost over 1, 2, 5, and 10;
false-alarm cost over 0.5, 1, 2, and 5; and unnecessary-adaptation cost over 0, 0.25, 0.5, 1,
2, and 5.

The current sensitivity result is deliberately not presented as a universal winner: static and
periodic policies dominate many low-miss-cost combinations, while feature-only wins a small
number of combinations. This confirms that the operational recommendation depends on the cost
of missed security changes and unnecessary adaptation. The costs are assumptions for sensitivity
analysis, not estimates from a production AWS account.

Reproduce with:

```text
python scripts/run_cost_sensitivity.py
```
