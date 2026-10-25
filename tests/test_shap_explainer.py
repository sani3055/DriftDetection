from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest

from src.explain.shap_explainer import explain_matrix


def test_shap_explains_isolation_forest_tree_output_additively() -> None:
    matrix = np.array([[0.0, 1.0], [1.0, 0.0], [0.5, 0.5], [2.0, 2.0]])
    model = IsolationForest(n_estimators=10, random_state=42, n_jobs=1).fit(matrix)
    explanations, metadata = explain_matrix(model, matrix, ("a", "b"))
    assert len(explanations) == len(matrix)
    assert metadata["max_additivity_residual"] < 1e-6
    assert explanations["explained_tree_path_output"].notna().all()

