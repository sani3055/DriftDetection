"""Generate reproducible paper figures from saved result artifacts."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix


def make_figures(root: str | Path) -> None:
    root = Path(root)
    figure_dir = root / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)

    drift = pd.read_csv(root / "data" / "drift" / "combined_drift.csv")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(drift["window_id"], drift["feature_drift_score"], marker="o", label="Feature drift")
    ax.plot(drift["window_id"], drift["shap_drift_score"], marker="o", label="SHAP drift")
    ax.tick_params(axis="x", rotation=75)
    ax.set_ylabel("Drift score")
    ax.set_title("Monthly feature and attribution drift")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figure_dir / "monthly_drift_signals.png", dpi=180)
    plt.close(fig)

    summary = pd.read_csv(root / "results" / "adaptation_summary.csv")
    fig, ax = plt.subplots(figsize=(10, 5))
    summary.set_index("policy")[["f1", "unnecessary_adaptation_rate"]].plot(kind="bar", ax=ax)
    ax.set_ylabel("Mean value")
    ax.set_title("Adaptation policy comparison")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(figure_dir / "adaptation_policy_comparison.png", dpi=180)
    plt.close(fig)

    diagnosis = pd.read_csv(root / "data" / "benchmark" / "diagnosis_results.csv")
    test = diagnosis[diagnosis["split"] == "test"].copy()
    mapping = {
        "stable": "stable",
        "benign_region": "benign_drift",
        "benign_identity": "benign_drift",
        "benign_service": "benign_drift",
        "security_privilege": "security_relevant_drift",
        "security_defense": "security_relevant_drift",
        "security_credential": "security_relevant_drift",
    }
    true = test["ground_truth"].map(mapping)
    labels = ["stable", "benign_drift", "security_relevant_drift"]
    matrix = confusion_matrix(true, test["diagnosis"], labels=labels)
    disp = ConfusionMatrixDisplay(matrix, display_labels=labels)
    fig, ax = plt.subplots(figsize=(7, 6))
    disp.plot(ax=ax, cmap="Blues", values_format="d", xticks_rotation=30)
    ax.set_title("Held-out drift-diagnosis confusion matrix")
    fig.tight_layout()
    fig.savefig(figure_dir / "diagnosis_confusion_matrix.png", dpi=180)
    plt.close(fig)

