"""Run a transparent cost-sensitivity analysis over held-out policy results.

The costs are scenario assumptions, not learned labels or claims about a production AWS account.
The analysis makes the operational trade-off explicit and reports which policy minimizes the
specified average loss.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "benchmark" / "adaptation_results.csv"
OUTPUT = ROOT / "data" / "robustness"


def main() -> None:
    frame = pd.read_csv(INPUT)
    frame["is_security"] = frame["scenario"].astype(str).str.startswith("security_")
    frame["miss_component"] = frame["is_security"].astype(float) * (1.0 - frame["recall"])
    frame["false_alarm_component"] = (~frame["is_security"]).astype(float) * frame["false_positive_rate"]
    frame["unnecessary_component"] = frame["unnecessary_adaptation"].astype(float)

    rows = []
    for miss_cost in (1.0, 2.0, 5.0, 10.0):
        for false_alarm_cost in (0.5, 1.0, 2.0, 5.0):
            for adaptation_cost in (0.0, 0.25, 0.5, 1.0, 2.0, 5.0):
                for policy, group in frame.groupby("policy"):
                    loss = (
                        miss_cost * group["miss_component"]
                        + false_alarm_cost * group["false_alarm_component"]
                        + adaptation_cost * group["unnecessary_component"]
                    )
                    rows.append({
                        "policy": policy,
                        "miss_cost": miss_cost,
                        "false_alarm_cost": false_alarm_cost,
                        "unnecessary_adaptation_cost": adaptation_cost,
                        "mean_loss": float(loss.mean()),
                        "security_miss_component": float(group["miss_component"].mean()),
                        "false_alarm_component": float(group["false_alarm_component"].mean()),
                        "unnecessary_adaptation_component": float(group["unnecessary_component"].mean()),
                    })

    results = pd.DataFrame(rows)
    results["best_policy"] = results.groupby(
        ["miss_cost", "false_alarm_cost", "unnecessary_adaptation_cost"]
    )["mean_loss"].transform(lambda values: "")
    keys = ["miss_cost", "false_alarm_cost", "unnecessary_adaptation_cost"]
    winners = results.loc[results.groupby(keys)["mean_loss"].idxmin(), keys + ["policy", "mean_loss"]].rename(
        columns={"policy": "best_policy", "mean_loss": "best_mean_loss"}
    )
    results = results.drop(columns=["best_policy"]).merge(winners, on=keys, how="left")
    results.to_csv(OUTPUT / "cost_sensitivity_results.csv", index=False)
    winners.to_csv(OUTPUT / "cost_sensitivity_winners.csv", index=False)
    metadata = {
        "input": str(INPUT.relative_to(ROOT)),
        "loss_definition": "miss_cost*(1-recall) on security scenarios + false_alarm_cost*FPR on benign scenarios + unnecessary_adaptation_cost*unnecessary_adaptation",
        "interpretation": "Lower mean_loss is preferred. Costs are sensitivity assumptions for the controlled benchmark, not production estimates.",
        "policies": sorted(frame["policy"].unique().tolist()),
    }
    (OUTPUT / "cost_sensitivity_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(winners["best_policy"].value_counts().to_string())


if __name__ == "__main__":
    main()
