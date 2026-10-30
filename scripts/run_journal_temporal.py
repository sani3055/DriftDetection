"""Run the locked native chronological protocol; never overwrite legacy tables."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter
import zipfile

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.experiments.journal_protocol import (  # noqa: E402
    FEATURES, POLICIES, calibrate_gates, confusion, drift_signals, encode, fit_maps,
    matched_refit, metrics, ordered_unique, update_requested, windows,
)
from src.explain.shap_explainer import explain_matrix  # noqa: E402


def load(path: Path) -> list[dict]:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.endswith(".json")]
        if len(names) != 1:
            raise ValueError("Archive must contain exactly one JSON")
        return json.loads(archive.read(names[0]))["Records"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--window-size", type=int, default=128)
    parser.add_argument("--quantile", type=float, default=0.95)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    dataset = ROOT / "data/external/cloud_log_sampling-main"
    output = ROOT / f"results/journal_v2/w{args.window_size}_q{args.quantile:g}_s{args.seed}"
    if (output / "manifest.json").exists():
        raise FileExistsError(f"Completed result already exists: {output}. Do not overwrite evidence.")
    output.mkdir(parents=True, exist_ok=True)
    start = perf_counter()
    base_path = dataset / "TrainOn/base_a.zip"
    base, base_duplicates = ordered_unique(load(base_path))
    if any(row.get("should_sample", False) for row in base):
        raise ValueError("Calibration archive is not benign-only")
    first_day = base[0]["eventTime"][:10]
    first = [row for row in base if row["eventTime"][:10] == first_day]
    split = int(0.7 * len(first))
    # Purge events tied at the fit/reference boundary from fitting.
    boundary = pd.Timestamp(first[split]["eventTime"])
    fitting = [row for row in first[:split] if pd.Timestamp(row["eventTime"]) < boundary]
    reference_rows = [row for row in first if pd.Timestamp(row["eventTime"]) >= boundary]
    calibration = [row for row in base if row["eventTime"][:10] > first_day]
    maps = fit_maps(fitting)
    x_train, reference = encode(fitting, maps), encode(reference_rows, maps)
    baseline = IsolationForest(n_estimators=100, contamination=0.05, random_state=args.seed, n_jobs=1)
    fit_start = perf_counter()
    baseline.fit(x_train)
    baseline_fit_seconds = perf_counter() - fit_start
    reference_phi, ref_meta = explain_matrix(baseline, reference, FEATURES)
    max_residual = ref_meta["max_additivity_residual"]
    reference_phi = reference_phi.loc[:, list(FEATURES)].to_numpy()
    replay_rng = np.random.default_rng(args.seed)
    replay = x_train[replay_rng.choice(len(x_train), size=min(512, len(x_train)), replace=False)]
    calibration_rows = []
    shap_seconds = 0.0

    def signals_for(records: list[dict]) -> tuple[np.ndarray, dict]:
        nonlocal max_residual, shap_seconds
        matrix = encode(records, maps)
        tick = perf_counter()
        phi, meta = explain_matrix(baseline, matrix, FEATURES)
        shap_seconds += perf_counter() - tick
        max_residual = max(max_residual, meta["max_additivity_residual"])
        return matrix, drift_signals(reference, matrix, reference_phi, phi.loc[:, list(FEATURES)].to_numpy())

    # Keep day/session boundaries: do not pool overnight gaps into a window.
    for day in sorted({row["eventTime"][:10] for row in calibration}):
        day_rows = [row for row in calibration if row["eventTime"][:10] == day]
        for index, batch in enumerate(windows(day_rows, args.window_size)):
            _, signal = signals_for(batch)
            calibration_rows.append({"day": day, "window_index": index,
                                     "n_events": len(batch), **signal})
    gates = calibrate_gates(calibration_rows, args.quantile)
    pd.DataFrame(calibration_rows).to_csv(output / "calibration_signals.csv", index=False)
    (output / "gates.json").write_text(json.dumps(gates.to_dict(), indent=2) + "\n", encoding="utf-8")
    print(f"Calibrated on {len(calibration_rows)} benign windows", flush=True)
    seen_ids = {row["eventID"] for row in base}
    last_training_time = max(pd.Timestamp(row["eventTime"]) for row in base)
    session_audits, signal_rows, prediction_rows, scenario_rows = [], [], [], []
    decision_rows = []
    input_paths = [dataset / "TestOn/labeled_cloudtrail_a.zip", dataset / "TrainOn/train_labeled_a.zip"]
    # Both are held-out sessions here. The latter's filename does NOT authorise training on it.
    for path in input_paths:
        unique, duplicates = ordered_unique(load(path))
        retained = [row for row in unique if pd.Timestamp(row["eventTime"]) > last_training_time]
        if {row["eventID"] for row in unique} & seen_ids:
            raise ValueError("Event ID overlap across archives")
        seen_ids.update(row["eventID"] for row in unique)
        # Day-separated sessions avoid interpreting an overnight gap as one stream.
        for day in sorted({row["eventTime"][:10] for row in retained}):
            session = f"{path.stem}_{day}"
            day_rows = [row for row in retained if row["eventTime"][:10] == day]
            models = {policy: baseline for policy in POLICIES}
            versions = {policy: 0 for policy in POLICIES}
            for index, batch in enumerate(windows(day_rows, args.window_size)):
                matrix, signal = signals_for(batch)
                signal_rows.append({"session": session, "window_index": index,
                    "first_event_time": batch[0]["eventTime"], "last_event_time": batch[-1]["eventTime"],
                    "n_events": len(batch), **signal})
                # PREQUENTIAL: every prediction is made before screening or fitting on this batch.
                predictions = {policy: (model.predict(matrix) == -1).astype(int)
                               for policy, model in models.items()}
                requests = {policy: update_requested(policy, signal, gates, index) for policy in POLICIES}
                # Refit candidates do not receive labels. Shared diagnostic baseline keeps pools matched.
                candidate_model, candidate_count, refit_done = baseline, 0, False
                fit_seconds = 0.0
                if any(requests.values()):
                    tick = perf_counter()
                    candidate_model, candidate_count, refit_done = matched_refit(baseline, replay, matrix)
                    fit_seconds = perf_counter() - tick
                # Labels are accessed here, after predictions and decisions have been fixed.
                labels = np.asarray([int(bool(row.get("should_sample", False))) for row in batch])
                attack_names = [str(row.get("attack_name") or "benign") for row in batch]
                for policy in POLICIES:
                    counts = confusion(labels, predictions[policy])
                    prediction_rows.append({"session": session, "window_index": index, "policy": policy,
                        "n_events": len(batch), "model_version_used": versions[policy], **counts})
                    decision_rows.append({"session": session, "window_index": index, "policy": policy,
                        "request": int(requests[policy]), "refit": int(requests[policy] and refit_done),
                        "n_candidates": candidate_count if requests[policy] else 0,
                        "fit_seconds": fit_seconds if requests[policy] else 0.0,
                        "attack_events_for_evaluation_only": int(labels.sum()),
                        "has_future_window": int(index < (len(day_rows) - 1) // args.window_size)})
                    for name in sorted(set(attack_names)):
                        mask = np.asarray([value == name for value in attack_names])
                        scenario_rows.append({"session": session, "window_index": index,
                            "policy": policy, "scenario_for_evaluation_only": name,
                            **confusion(labels[mask], predictions[policy][mask])})
                    if requests[policy] and refit_done:
                        models[policy] = candidate_model
                        versions[policy] += 1
                if index % 10 == 0:
                    print(f"{session}: window {index + 1}, n={len(batch)}", flush=True)
            session_audits.append({"session": session, "archive": str(path.relative_to(ROOT)),
                "archive_sha256": sha256(path), "archive_duplicates_removed": duplicates,
                "archive_records_removed_as_not_future": len(unique) - len(retained),
                "events": len(day_rows), "first": day_rows[0]["eventTime"], "last": day_rows[-1]["eventTime"]})
    predictions = pd.DataFrame(prediction_rows)
    decisions = pd.DataFrame(decision_rows)
    predictions.to_csv(output / "prequential_window_counts.csv", index=False)
    decisions.to_csv(output / "update_decisions.csv", index=False)
    pd.DataFrame(signal_rows).to_csv(output / "test_signals.csv", index=False)
    pd.DataFrame(scenario_rows).to_csv(output / "scenario_confusion_counts.csv", index=False)
    summaries = []
    for session in ["pooled", *predictions["session"].unique()]:
        frame = predictions if session == "pooled" else predictions[predictions.session == session]
        decision_frame = decisions if session == "pooled" else decisions[decisions.session == session]
        for policy in POLICIES:
            counts = {name: int(frame[frame.policy == policy][name].sum()) for name in ("tp", "fp", "tn", "fn")}
            selected = decision_frame[decision_frame.policy == policy]
            security = selected.attack_events_for_evaluation_only > 0
            summaries.append({"session": session, "policy": policy, **counts, **metrics(counts),
                "update_requests": int(selected.request.sum()), "completed_refits": int(selected.refit.sum()),
                "requests_on_attack_free_windows": int(selected.loc[~security, "request"].sum()),
                "attack_free_windows": int((~security).sum()), "security_windows": int(security.sum()),
                "requests_on_security_windows": int(selected.loc[security, "request"].sum()),
                "terminal_requests_without_future_window": int(selected.loc[selected.has_future_window == 0, "request"].sum())})
    summary = pd.DataFrame(summaries)
    summary.to_csv(output / "policy_summary.csv", index=False)
    manifest = {
        "protocol": "journal-v2-native-time-prequential", "created_utc": datetime.now(timezone.utc).isoformat(),
        "parameters": vars(args), "features": FEATURES, "model": baseline.get_params(),
        "base_archive_sha256": sha256(base_path), "base_duplicates_removed": base_duplicates,
        "fit_events": len(fitting), "reference_events": len(reference_rows), "calibration_events": len(calibration),
        "fit_last_time": fitting[-1]["eventTime"], "reference_first_time": reference_rows[0]["eventTime"],
        "calibration_first_time": calibration[0]["eventTime"], "calibration_last_time": calibration[-1]["eventTime"],
        "calibration_windows": len(calibration_rows), "sessions": session_audits,
        "gates": gates.to_dict(), "max_shap_additivity_residual": max_residual,
        "baseline_fit_seconds": baseline_fit_seconds, "monitoring_shap_seconds": shap_seconds,
        "wall_seconds": perf_counter() - start,
        "code_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in
            [Path(__file__), ROOT / "src/experiments/journal_protocol.py"]},
        "limitations": ["One controlled cloud deployment; days/windows are not independent incidents",
            "Ordinal encoding, unseen categories -1, frozen diagnostic reference can become stale",
            "Benign empirical quantiles do not guarantee an operational false-alarm rate",
            "Predicted-normal candidates can contain attacks; requests need not improve detection",
            "Session model resets and time gaps preclude continuous-production claims",
            "Shared refit caching gives policy-attributed fit work, not seven independent timing benchmarks",
            "No test-label threshold tuning; prior project already inspected this dataset, so this is not a blind new corpus"],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(summary[summary.session == "pooled"].to_string(index=False), flush=True)
    print(f"Saved {output}; {manifest['wall_seconds']:.1f} s", flush=True)


if __name__ == "__main__":
    main()
