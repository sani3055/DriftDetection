"""Result summaries and paired policy comparisons."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from scipy.stats import wilcoxon

from src.evaluation.inference import adaptation_inference


def summarize_adaptation(results: pd.DataFrame) -> pd.DataFrame:
    return results.groupby("policy").agg(
        trigger_rate=("triggered", "mean"),
        unnecessary_adaptation_rate=("unnecessary_adaptation", "mean"),
        anomaly_rate=("anomaly_rate", "mean"),
        precision=("precision", "mean"),
        recall=("recall", "mean"),
        f1=("f1", "mean"),
        false_positive_rate=("false_positive_rate", "mean"),
    ).reset_index()


def paired_wilcoxon(results: pd.DataFrame, metric: str, left: str = "dual_signal", right: str = "static") -> dict:
    pivot = results.pivot_table(index=["scenario", "seed"], columns="policy", values=metric, aggfunc="mean")
    if left not in pivot or right not in pivot:
        return {"metric": metric, "left": left, "right": right, "n": 0, "statistic": None, "p_value": None}
    paired = pivot[[left, right]].dropna()
    if len(paired) < 2 or (paired[left] == paired[right]).all():
        return {"metric": metric, "left": left, "right": right, "n": len(paired), "statistic": None, "p_value": None}
    test = wilcoxon(paired[left], paired[right], zero_method="wilcox", alternative="two-sided")
    return {"metric": metric, "left": left, "right": right, "n": len(paired), "statistic": float(test.statistic), "p_value": float(test.pvalue)}


def write_summaries(results_path: str | Path, output_dir: str | Path) -> None:
    results = pd.read_csv(results_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_adaptation(results)
    summary.to_csv(output_dir / "adaptation_summary.csv", index=False)
    tests = pd.DataFrame([paired_wilcoxon(results, metric) for metric in ["f1", "false_positive_rate", "unnecessary_adaptation"]])
    tests.to_csv(output_dir / "paired_wilcoxon.csv", index=False)
    adaptation_inference(results).to_csv(output_dir / "paired_inference.csv", index=False)
