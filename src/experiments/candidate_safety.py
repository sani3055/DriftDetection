"""Historical score screening without target labels or target-fitted thresholds."""
import numpy as np


def historical_score_threshold(scores, quantile):
    scores = np.asarray(scores, dtype=float)
    if scores.ndim != 1 or not len(scores) or not np.isfinite(scores).all():
        raise ValueError('Historical scores must be a nonempty finite vector')
    if not 0 <= quantile <= 1:
        raise ValueError('Quantile must be between zero and one')
    return float(np.quantile(scores, quantile, method='higher'))


def historical_normal_mask(scores, original_normal, threshold):
    scores = np.asarray(scores, dtype=float)
    original_normal = np.asarray(original_normal, dtype=bool)
    if scores.ndim != 1 or scores.shape != original_normal.shape:
        raise ValueError('Scores and original screen must be matching vectors')
    if not np.isfinite(scores).all() or not np.isfinite(threshold):
        raise ValueError('Scores and threshold must be finite')
    return original_normal & (scores <= threshold)
