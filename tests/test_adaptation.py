from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest

from src.adaptation.controller import protected_retrain, should_adapt


def test_policy_trigger_rules() -> None:
    assert not should_adapt("static", 2.0, 2.0, "security_relevant_drift", 1.0, 1.0, 0, 3)
    assert should_adapt("feature_only", 2.0, 0.0, "benign_drift", 1.0, 1.0, 0, 3)
    assert should_adapt("dual_signal", 2.0, 2.0, "security_relevant_drift", 1.0, 1.0, 0, 3)


def test_protected_retrain_uses_normal_candidates() -> None:
    rng = np.random.default_rng(42)
    base = rng.normal(size=(50, 3))
    baseline = IsolationForest(n_estimators=10, random_state=42).fit(base)
    adapted, count = protected_retrain(baseline, base, base[:20], random_state=7, n_estimators=5, n_jobs=1)
    assert adapted is not None
    assert count >= 0

