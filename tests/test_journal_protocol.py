from __future__ import annotations

import numpy as np
import pytest
from sklearn.ensemble import IsolationForest

from src.experiments.journal_protocol import (
    FEATURES, Gates, aligned_rank_tau, calibrate_gates, confusion, drift_signals,
    encode, fit_maps, matched_refit, metrics, ordered_unique, update_requested, windows,
)


def record(identifier: str, time: str = "2026-01-01T00:00:00Z", **extra) -> dict:
    return {"eventID": identifier, "eventTime": time, "eventName": "ListBuckets",
            "eventSource": "s3.amazonaws.com", "awsRegion": "us-east-1", **extra}


def test_native_order_and_windows_ignore_attack_labels() -> None:
    rows = [record("b", "2026-01-02T00:00:00Z", attack_name="A"), record("a")]
    ordered, duplicates = ordered_unique(rows + [rows[0]])
    assert duplicates == 1
    assert [row["eventID"] for row in ordered] == ["a", "b"]
    assert [len(batch) for batch in windows(ordered, 1)] == [1, 1]
    changed = [{**row, "attack_name": "changed", "should_sample": True} for row in rows]
    altered, _ = ordered_unique(changed)
    assert [row["eventID"] for row in altered] == ["a", "b"]


def test_duplicate_conflicts_fail_instead_of_leaking() -> None:
    with pytest.raises(ValueError, match="Conflicting labels"):
        ordered_unique([record("a"), record("a", should_sample=True)])
    with pytest.raises(ValueError, match="Conflicting features"):
        ordered_unique([record("a"), record("a", eventName="DeleteBucket")])


def test_unknown_categories_do_not_expand_training_maps() -> None:
    maps = fit_maps([record("a")])
    encoded = encode([record("b", eventName="NeverSeen")], maps)
    assert encoded[0, 0] == -1
    assert "NeverSeen" not in maps["eventName"]


def test_root_flag_recomputed_from_identity() -> None:
    root = record("a", userIdentity={"type": "Root"})
    maps = fit_maps([root])
    assert encode([root], maps)[0, -1] == 1


def test_labels_are_absent_from_feature_encoding() -> None:
    row = record("a")
    maps = fit_maps([row])
    altered = {**row, "attack_name": "security", "should_sample": True}
    np.testing.assert_array_equal(encode([row], maps), encode([altered], maps))


def test_rank_alignment_is_feature_aligned_and_tie_aware() -> None:
    assert aligned_rank_tau(np.array([3, 2, 1]), np.array([1, 2, 3])) == -1
    assert aligned_rank_tau(np.array([1, 1, 1]), np.array([1, 1, 1])) == 1
    assert aligned_rank_tau(np.array([3, 1, 1]), np.array([6, 2, 2])) == pytest.approx(1)


def test_identical_batch_has_no_drift_even_for_constant_attributions() -> None:
    matrix = np.zeros((20, len(FEATURES)))
    values = np.zeros_like(matrix)
    signals = drift_signals(matrix, matrix, values, values)
    assert signals["feature_score"] == 0
    assert signals["shap_score"] == 0
    assert signals["coupling_score"] == 0
    assert all(np.isfinite(value) for value in signals.values())


def test_variance_floor_bounds_constant_feature_wasserstein() -> None:
    matrix = np.zeros((10, len(FEATURES)))
    values = np.zeros_like(matrix)
    signals = drift_signals(matrix, matrix + 1, values, values + 1)
    assert np.isfinite(signals["shap_score"])
    assert signals["wasserstein_floor"] > 0


def test_calibration_ignores_extra_label_fields() -> None:
    rows = [{"feature_score": x, "shap_score": x / 2, "coupling_score": 0.7,
             "conservative_score": 0.6} for x in range(20)]
    expected = calibrate_gates(rows)
    assert expected == calibrate_gates([{**row, "attack_name": "arbitrary"} for row in rows])
    assert expected.feature_score == 19


def test_joint_gates_use_the_complete_calibration_object() -> None:
    gates = Gates(1, 2, 0.8, 0.7)
    signals = {"feature_score": 1.5, "shap_score": 3, "coupling_score": 0.5,
               "conservative_score": 0.5}
    assert update_requested("dual_signal", signals, gates, 0)
    assert not update_requested("coupled_signal", signals, gates, 0)
    assert not update_requested("conservative_coupled_signal", signals, gates, 0)
    assert not update_requested("periodic", signals, gates, 0)
    assert update_requested("periodic", signals, gates, 4)
    signals["feature_score"] = 1  # Strict > prevents zero-score calibration ties firing.
    assert not update_requested("dual_signal", signals, gates, 0)


def test_pooled_counts_avoid_averaging_zero_f1_from_attack_free_windows() -> None:
    one = confusion(np.array([0, 0]), np.array([0, 0]))
    two = confusion(np.array([1, 1]), np.array([1, 1]))
    assert metrics({name: one[name] + two[name] for name in one})["f1"] == 1
    assert metrics(one)["recall"] is None


def test_refit_preserves_settings_and_does_not_mutate_baseline() -> None:
    rng = np.random.default_rng(0)
    base = rng.normal(size=(100, len(FEATURES)))
    model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42, n_jobs=1).fit(base)
    before = model.predict(base).copy()
    new, count, done = matched_refit(model, base[:20], base[20:])
    assert done and count >= 10
    assert new is not model
    assert new.get_params() == model.get_params()
    np.testing.assert_array_equal(model.predict(base), before)


@pytest.mark.parametrize("size", [0, -1])
def test_invalid_window_size_fails(size: int) -> None:
    with pytest.raises(ValueError):
        list(windows([record("a")], size))


def test_nonfinite_calibration_and_empty_data_fail() -> None:
    with pytest.raises(ValueError):
        calibrate_gates([])
    with pytest.raises(ValueError):
        calibrate_gates([{"feature_score": float("nan"), "shap_score": 0,
                          "coupling_score": 0, "conservative_score": 0}])
