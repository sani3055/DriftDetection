import numpy as np
import pytest
from src.experiments.candidate_safety import historical_normal_mask, historical_score_threshold


def test_historical_quantile_uses_higher_and_keeps_ties():
    assert historical_score_threshold([1, 2, 2, 4], .5) == 2
    assert historical_normal_mask([1, 2, 2, 4], [1, 1, 0, 1], 2).tolist() == [True, True, False, False]


def test_target_scores_do_not_affect_historical_threshold():
    historical = np.array([.1, .2, .3, .4])
    threshold = historical_score_threshold(historical, .25)
    assert historical_normal_mask([.01, .8], [True, True], threshold).tolist() == [True, False]
    assert historical_score_threshold(historical, .25) == threshold


@pytest.mark.parametrize('scores,q', [([], .5), ([1, float('nan')], .5), ([1], 1.1)])
def test_invalid_historical_inputs_raise(scores, q):
    with pytest.raises(ValueError):
        historical_score_threshold(scores, q)


def test_bad_candidate_vectors_raise():
    with pytest.raises(ValueError):
        historical_normal_mask([1, 2], [True], 1)
